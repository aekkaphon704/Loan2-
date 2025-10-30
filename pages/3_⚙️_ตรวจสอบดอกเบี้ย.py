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

if st.button("🔍 เริ่มการตรวจสอบ"):
    with st.spinner("กำลังดึงข้อมูลสัญญาเงินกู้ทั้งหมด..."):
        all_loans_df = gsheet_utils.get_data_as_dataframe("Loans", _sh)

    if all_loans_df.empty:
        st.info("ยังไม่มีข้อมูลสัญญาเงินกู้ในระบบ")
    else:
        try:
            all_loans_df['DueDate'] = pd.to_datetime(all_loans_df['DueDate'], errors='coerce').dt.date
            all_loans_df['PrincipalAmount'] = pd.to_numeric(all_loans_df['PrincipalAmount'], errors='coerce').fillna(0)
            all_loans_df['AmountPaid'] = pd.to_numeric(all_loans_df['AmountPaid'], errors='coerce').fillna(0)

            # --- *** นี่คือส่วนที่แก้ไข *** ---
            # 1. กำหนดสถานะที่ถือว่า "ยังไม่จ่าย"
            active_statuses = ['Active', 'ยังค้างชำระ']
            
            # 2. ค้นหาแถวที่ (DueDate <= today) และ (Status อยู่ใน active_statuses)
            overdue_loans = all_loans_df[
                (all_loans_df['DueDate'] <= today) &
                (all_loans_df['Status'].isin(active_statuses))
            ].copy()
            # --- *** สิ้นสุดการแก้ไข *** ---

            if overdue_loans.empty:
                st.success("✅ ไม่พบสัญญาเงินกู้ที่ครบกำหนดและยังค้างชำระ")
            else:
                st.error(f"🚨 พบสัญญาเงินกู้ที่ครบกำหนดแต่ยังค้างชำระ {len(overdue_loans)} ฉบับ:")

                members_df_admin = gsheet_utils.get_data_as_dataframe("Members", _sh)
                if not members_df_admin.empty and 'Name' in members_df_admin.columns:
                    overdue_loans = pd.merge(overdue_loans, members_df_admin[['MemberID', 'Name']], on='MemberID', how='left')
                else:
                    overdue_loans['Name'] = 'N/A' # ถ้าหาชื่อไม่เจอ

                overdue_loans['เงินต้นคงเหลือ'] = overdue_loans['PrincipalAmount'] - overdue_loans['AmountPaid']
                overdue_loans['วันครบกำหนด'] = overdue_loans['DueDate'].apply(format_thai_date_admin)

                display_cols = ['LoanID', 'Name', 'LoanAccount', 'PrincipalAmount', 'เงินต้นคงเหลือ', 'วันครบกำหนด']
                st.dataframe(overdue_loans[display_cols].rename(columns={
                    'LoanID': 'รหัสสัญญา', 'Name': 'ชื่อสมาชิก', 'LoanAccount': 'บัญชี',
                    'PrincipalAmount': 'เงินต้น', 'เงินต้นคงเหลือ': 'คงเหลือ (ต้น)', 'วันครบกำหนด': 'ครบกำหนด'
                }), use_container_width=True)

                st.markdown("---")
                st.warning("คุณสามารถกดปุ่มด้านล่างเพื่อเปลี่ยนสถานะสัญญาเหล่านี้เป็น 'เกินกำหนดชำระ'")
                
                if st.button("เปลี่ยนสถานะสัญญาที่พบเป็น 'เกินกำหนดชำระ' ทั้งหมด", type="primary"):
                    updated_count = 0
                    error_count = 0
                    with st.spinner("กำลังอัปเดตสถานะ..."):
                        for loan_id in overdue_loans['LoanID']:
                            # อัปเดตเป็นสถานะภาษาไทยที่ถูกต้อง
                            if gsheet_utils.update_loan_status(_sh, str(loan_id), "เกินกำหนดชำระ"):
                                updated_count += 1
                            else:
                                error_count += 1
                    if error_count == 0:
                        st.success(f"อัปเดตสถานะสัญญา {updated_count} ฉบับ เป็น 'เกินกำหนดชำระ' เรียบร้อย!")
                    else:
                         st.error(f"อัปเดตสถานะสำเร็จ {updated_count} ฉบับ, เกิดข้อผิดพลาด {error_count} ฉบับ")
                    st.rerun()

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูลสัญญา: {e}")
            st.error("กรุณาตรวจสอบรูปแบบข้อมูลในแท็บ Loans, โดยเฉพาะคอลัมน์ DueDate (ควรเป็น YYYY-MM-DD)")
