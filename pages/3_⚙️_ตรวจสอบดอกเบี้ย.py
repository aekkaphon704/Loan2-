# pages/3_⚙️_ตรวจสอบดอกเบี้ย.py
import streamlit as st
import gsheet_utils
import pandas as pd
from datetime import datetime, date
from pytz import timezone

# --- ฟังก์ชันแปลงวันที่เป็น พ.ศ. ---
def format_thai_date(dt):
    if pd.isna(dt) or dt is None or dt == "": return "ไม่ได้ระบุ"
    if isinstance(dt, str):
        try: dt = datetime.strptime(dt, "%Y-%m-%d").date()
        except ValueError:
             try: dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").date()
             except ValueError: return dt
    if isinstance(dt, date) or isinstance(dt, datetime):
        thai_months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                       "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
        return f"{dt.day} {thai_months[dt.month - 1]} {dt.year + 543}"
    return str(dt)

st.set_page_config(page_title="ตรวจสอบสัญญา", page_icon="⚙️", layout="wide")
st.title("⚙️ ตรวจสอบสัญญา & สถานะหนี้")

_sh = gsheet_utils.connect_to_sheet()
bangkok_tz = timezone("Asia/Bangkok")

st.header("1. ตรวจสอบสัญญาเงินกู้ที่ครบกำหนดแต่ยังค้างชำระ")

if st.button("🔍 เริ่มการตรวจสอบ"):
    with st.spinner("กำลังตรวจสอบข้อมูล..."):
        loans_df = gsheet_utils.get_data_as_dataframe("Loans", _sh)
        members_df = gsheet_utils.get_data_as_dataframe("Members", _sh)
        
        if loans_df.empty:
            st.info("ไม่มีข้อมูลสัญญาในระบบ")
        else:
            # 1. แปลงชนิดข้อมูลวันที่
            loans_df['DueDate_Date'] = pd.to_datetime(loans_df['DueDate'], errors='coerce').dt.date
            today = datetime.now(bangkok_tz).date()
            
            # 2. กรองเฉพาะที่ค้างชำระและเลยวันกำหนด
            overdue_mask = (loans_df['Status'] == 'ยังค้างชำระ') & (loans_df['DueDate_Date'] < today)
            overdue_loans = loans_df[overdue_mask].copy()
            
            if overdue_loans.empty:
                st.success("🎉 ยอดเยี่ยม! ไม่มีสัญญาเงินกู้ที่เกินกำหนดชำระ")
            else:
                st.error(f"🚨 พบสัญญาเงินกู้ที่ครบกำหนดแต่ยังค้างชำระ {len(overdue_loans)} ฉบับ:")
                
                # 3. จัดการคอลัมน์ชื่อสมาชิก (ดึงจากคอลัมน์ Name ใหม่ หรือถ้าไม่มีให้เทียบจาก MemberID)
                if 'Name' in overdue_loans.columns:
                    overdue_loans['ชื่อสมาชิก'] = overdue_loans['Name'].replace("", "ไม่ระบุชื่อ")
                else:
                    name_dict = dict(zip(members_df['MemberID'], members_df['Name']))
                    overdue_loans['ชื่อสมาชิก'] = overdue_loans['MemberID'].map(name_dict).fillna("ไม่พบชื่อ")

                # 4. คำนวณตัวเลข
                overdue_loans['PrincipalAmount'] = pd.to_numeric(overdue_loans['PrincipalAmount'], errors='coerce').fillna(0)
                overdue_loans['AmountPaid'] = pd.to_numeric(overdue_loans['AmountPaid'], errors='coerce').fillna(0)
                overdue_loans['RemainingPrincipal'] = overdue_loans['PrincipalAmount'] - overdue_loans['AmountPaid']
                
                # 5. จัดรูปแบบวันที่เป็น พ.ศ.
                overdue_loans['วันครบกำหนด'] = overdue_loans['DueDate_Date'].apply(format_thai_date)
                
                # 6. เลือกคอลัมน์ที่จะแสดงผลแบบ Dynamic (ป้องกัน KeyError 100%)
                display_cols_mapping = {
                    'LoanID': 'รหัสสัญญา',
                    'ชื่อสมาชิก': 'ชื่อสมาชิก',
                    'LoanAccount': 'บัญชี',
                    'PrincipalAmount': 'เงินต้น',
                    'RemainingPrincipal': 'คงเหลือ (ต้น)',
                    'วันครบกำหนด': 'ครบกำหนด'
                }
                
                # ตรวจสอบว่ามีคอลัมน์ครบไหมก่อนสั่งแสดงผล
                available_cols = [col for col in display_cols_mapping.keys() if col in overdue_loans.columns]
                overdue_loans_to_show = overdue_loans[available_cols].rename(columns={k: display_cols_mapping[k] for k in available_cols})
                
                st.dataframe(overdue_loans_to_show, use_container_width=True, hide_index=True)

                st.markdown("---")
                
                # --- กรอบบังคับอัปเดตทีละรายการ (Fallback) ---
                st.warning("💡 คุณสามารถเลือกอัปเดตสถานะสัญญาเป็น 'เกินกำหนดชำระ' ได้ทีละรายการด้านล่างนี้")
                
                selected_overdue_id = st.selectbox(
                    "เลือก LoanID ที่ต้องการบังคับอัปเดต:",
                    options=["--- เลือก ID สัญญา ---"] + overdue_loans['LoanID'].tolist()
                )
                
                if selected_overdue_id != "--- เลือก ID สัญญา ---":
                    if st.button(f"อัปเดตสถานะ {selected_overdue_id}", type="primary"):
                        with st.spinner("กำลังอัปเดต..."):
                            success = gsheet_utils.update_loan_status(_sh, selected_overdue_id, "เกินกำหนดชำระ")
                            if success:
                                st.success(f"✅ อัปเดตสถานะ {selected_overdue_id} เป็น 'เกินกำหนดชำระ' สำเร็จ! กรุณากดปุ่ม 'เริ่มการตรวจสอบ' ด้านบนอีกครั้ง")
                            else:
                                st.error("❌ อัปเดตไม่สำเร็จ กรุณาลองใหม่")
