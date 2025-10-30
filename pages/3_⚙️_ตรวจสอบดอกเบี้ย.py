# pages/3_⚙️_เครื่องมือแอดมิน.py
import streamlit as st
import gsheet_utils
from datetime import datetime, date
from babel.dates import format_date
import pandas as pd

# --- ฟังก์ชัน Helper ---
def format_thai_date_admin(dt):
    if dt is None: return "ไม่ได้ระบุ"
    if isinstance(dt, str):
        try: dt = datetime.strptime(dt, "%Y-%m-%d").date()
        except ValueError:
            try: dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").date()
            except ValueError: return dt
    if isinstance(dt, date):
        return format_date(dt, format='d MMMM yyyy', locale='th_TH')
    return str(dt)

def safe_float(value):
    return float(value) if value not in [None, ''] else 0.0

st.set_page_config(page_title="เครื่องมือแอดมิน", page_icon="⚙️", layout="wide")
st.title("⚙️ เครื่องมือสำหรับผู้ดูแลระบบ")

_sh = gsheet_utils.connect_to_sheet()

today = date.today()
st.info(f"วันนี้วันที่: **{format_thai_date_admin(today)}**")

st.markdown("---")

# --- ส่วนที่ 1: ตรวจสอบสัญญาค้างชำระ ---
st.subheader("1. ตรวจสอบสัญญาเงินกู้ที่ครบกำหนดแต่ยังค้างชำระ")

# ใช้ Session State เก็บผลการตรวจสอบ
if 'overdue_loans_df' not in st.session_state:
    st.session_state.overdue_loans_df = pd.DataFrame()

if st.button("🔍 เริ่มการตรวจสอบ"):
    with st.spinner("กำลังดึงข้อมูลสัญญาเงินกู้ทั้งหมด..."):
        all_loans_df = gsheet_utils.get_data_as_dataframe("Loans", _sh)

    if all_loans_df.empty:
        st.info("ยังไม่มีข้อมูลสัญญาเงินกู้ในระบบ")
        st.session_state.overdue_loans_df = pd.DataFrame() # เคลียร์ค่า
    else:
        try:
            all_loans_df['DueDate'] = pd.to_datetime(all_loans_df['DueDate'], errors='coerce').dt.date
            all_loans_df['PrincipalAmount'] = pd.to_numeric(all_loans_df['PrincipalAmount'], errors='coerce').fillna(0)
            all_loans_df['AmountPaid'] = pd.to_numeric(all_loans_df['AmountPaid'], errors='coerce').fillna(0)

            active_statuses = ['Active', 'ยังค้างชำระ']
            
            overdue_loans_check = all_loans_df[
                (all_loans_df['DueDate'] <= today) &
                (all_loans_df['Status'].isin(active_statuses))
            ].copy()
            
            # เก็บผลลัพธ์ไว้ใน Session State
            st.session_state.overdue_loans_df = overdue_loans_check
            st.rerun() # รีเฟรชเพื่อแสดงผล

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูลสัญญา: {e}")
            st.session_state.overdue_loans_df = pd.DataFrame()

# --- แสดงผลลัพธ์ (จาก Session State) ---
if not st.session_state.overdue_loans_df.empty:
    overdue_loans_to_show = st.session_state.overdue_loans_df
    st.error(f"🚨 พบสัญญาเงินกู้ที่ครบกำหนดแต่ยังค้างชำระ {len(overdue_loans_to_show)} ฉบับ:")

    members_df_admin = gsheet_utils.get_data_as_dataframe("Members", _sh)
    if not members_df_admin.empty and 'Name' in members_df_admin.columns:
        overdue_loans_to_show = pd.merge(overdue_loans_to_show, members_df_admin[['MemberID', 'Name']], on='MemberID', how='left')
    else:
        overdue_loans_to_show['Name'] = 'N/A'

    overdue_loans_to_show['เงินต้นคงเหลือ'] = overdue_loans_to_show['PrincipalAmount'] - overdue_loans_to_show['AmountPaid']
    overdue_loans_to_show['วันครบกำหนด'] = overdue_loans_to_show['DueDate'].apply(format_thai_date_admin)

    display_cols = ['LoanID', 'Name', 'LoanAccount', 'PrincipalAmount', 'เงินต้นคงเหลือ', 'วันครบกำหนด']
    st.dataframe(overdue_loans_to_show[display_cols].rename(columns={
        'LoanID': 'รหัสสัญญา', 'Name': 'ชื่อสมาชิก', 'LoanAccount': 'บัญชี',
        'PrincipalAmount': 'เงินต้น', 'เงินต้นคงเหลือ': 'คงเหลือ (ต้น)', 'วันครบกำหนด': 'ครบกำหนด'
    }), use_container_width=True)

    # --- *** นี่คือส่วนแก้ไข: บังคับอัปเดตทีละรายการ *** ---
    st.markdown("---")
    st.warning("ดูเหมือนการอัปเดตแบบ 'ทั้งหมด' มีปัญหา ลองอัปเดต 'ทีละรายการ' ด้านล่างนี้แทนครับ")
    
    # 1. สร้าง Dropdown จาก ID ที่พบ
    loan_id_list = overdue_loans_to_show['LoanID'].tolist()
    
    selected_loan_id_to_fix = st.selectbox(
        "เลือก LoanID ที่ต้องการบังคับอัปเดต:",
        options=loan_id_list,
        index=None,
        placeholder="--- เลือก ID สัญญา ---"
    )
    
    # 2. สร้างปุ่มสำหรับ ID ที่เลือก
    if selected_loan_id_to_fix:
        if st.button(f"บังคับอัปเดต {selected_loan_id_to_fix} เป็น 'เกินกำหนดชำระ'", type="primary"):
            st.info(f"กำลังส่งคำสั่งอัปเดตสำหรับ {selected_loan_id_to_fix}...")
            
            # เรียกฟังก์ชัน (ที่เราใส่ st.write ไว้)
            success = gsheet_utils.update_loan_status(_sh, str(selected_loan_id_to_fix), "เกินกำหนดชำระ")
            
            if success:
                st.success(f"อัปเดต {selected_loan_id_to_fix} สำเร็จ! (ดูข้อความดีบักด้านบน)")
                # เคลียร์ State เพื่อให้ตารางโหลดใหม่
                st.session_state.overdue_loans_df = pd.DataFrame() 
                st.rerun()
            else:
                st.error(f"การอัปเดต {selected_loan_id_to_fix} ล้มเหลว (ดู Error ด้านบน)")

else:
    # (แสดงเฉพาะเมื่อกดตรวจสอบแล้ว และไม่พบอะไร)
    if st.session_state.get('overdue_loans_df') is not None and st.session_state.overdue_loans_df.empty:
         st.success("✅ ไม่พบสัญญาเงินกู้ที่ครบกำหนดและยังค้างชำระ")
