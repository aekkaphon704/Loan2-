# pages/2_✏️_แก้ไขและลบข้อมูล.py
import streamlit as st
import gsheet_utils
from datetime import datetime, date
from pytz import timezone
from babel.dates import format_date
import time

# --- ฟังก์ชันแปลงวันที่เป็น พ.ศ. ---
def format_thai_date(dt):
    if dt is None or dt == "": return "ไม่ได้ระบุ"
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

# --- Session State Setup ---
if 'confirm_delete_id' not in st.session_state:
    st.session_state.confirm_delete_id = None
if 'confirm_delete_name' not in st.session_state:
    st.session_state.confirm_delete_name = None

_sh = gsheet_utils.connect_to_sheet()
bangkok_tz = timezone("Asia/Bangkok")

st.set_page_config(page_title="แก้ไขข้อมูลสมาชิก", page_icon="✏️", layout="wide")
st.title("✏️ แก้ไข / ลบ / อนุมัติเงินกู้")

# --- 1. Member Selection ---
members_df = gsheet_utils.get_data_as_dataframe("Members", _sh)
if not members_df.empty:
    member_options = dict(zip(members_df['Name'], members_df['MemberID']))

    selected_name = st.selectbox(
        "เลือกสมาชิก:",
        options=member_options.keys(),
        index=None,
        placeholder="กรุณาเลือกชื่อ..."
    )

    if selected_name:
        member_id = member_options[selected_name]

        if st.session_state.confirm_delete_id and st.session_state.confirm_delete_id != member_id:
            st.session_state.confirm_delete_id = None
            st.session_state.confirm_delete_name = None

        member_data = gsheet_utils.get_member_by_id(_sh, member_id)

        if member_data:
            st.markdown("---")
            st.subheader(f"👤 ข้อมูลสมาชิก: {selected_name}")

            # --- 2A. Edit Member Info Form ---
            with st.form("edit_form"):
                st.markdown("**แก้ไขข้อมูลส่วนตัวและการเงินพื้นฐาน**")
                dob_obj = datetime.strptime(member_data['DOB'], "%Y-%m-%d").date() if member_data.get('DOB') else None

                col_form_1, col_form_2 = st.columns(2)
                with col_form_1:
                    name = st.text_input("ชื่อ-สกุล", value=member_data.get('Name'))
                    address_no = st.text_input("บ้านเลขที่", value=member_data.get('AddressNo'))
                    village = st.text_input("หมู่บ้าน", value=member_data.get('Village'))
                    sub_district = st.text_input("ตำบล", value=member_data.get('SubDistrict'))
                    savings = st.number_input("เงินฝากสัจจะ (ยอดปัจจุบัน)", value=gsheet_utils.safe_float(member_data.get('Savings')))
                with col_form_2:
                    district = st.text_input("อำเภอ", value=member_data.get('District'))
                    province = st.text_input("จังหวัด", value=member_data.get('Province'))
                    dob = st.date_input("วันเกิด (เลือกปี ค.ศ.)", value=dob_obj, format="DD/MM/YYYY")
                    shares = st.number_input("เงินหุ้น (บาท, ยอดปัจจุบัน)", value=gsheet_utils.safe_float(member_data.get('Shares')))

                st.markdown("---")
                col_btn_1, col_btn_2 = st.columns(2)
                with col_btn_1:
                    save_button = st.form_submit_button("💾 บันทึกการแก้ไขข้อมูล", use_container_width=True)
                with col_btn_2:
                    delete_button = st.form_submit_button("🗑️ ลบสมาชิกคนนี้", type="secondary", use_container_width=True)

            if save_button:
                st.session_state.confirm_delete_id = None
                st.session_state.confirm_delete_name = None
                timestamp_str = datetime.now(bangkok_tz).strftime("%Y-%m-%d %H:%M:%S")
                dob_str = dob.strftime("%Y-%m-%d") if dob else None
                updates = {
                    "Name": name, "AddressNo": address_no, "Village": village,
                    "SubDistrict": sub_district, "District": district, "Province": province,
                    "DOB": dob_str, "Savings": savings, "Shares": shares,
                    "LastUpdated": timestamp_str
                }
                if gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", updates):
                    st.success(f"อัปเดตข้อมูลของ '{name}' เรียบร้อยแล้ว!")
                else:
                    st.error("ไม่สามารถอัปเดตข้อมูลได้")

            if delete_button:
                st.session_state.confirm_delete_id = member_id
                st.session_state.confirm_delete_name = selected_name
                st.rerun()

            if st.session_state.confirm_delete_id == member_id:
                st.warning(f"**คุณกำลังจะลบข้อมูลของ {st.session_state.confirm_delete_name}**")
                st.markdown("การดำเนินการนี้ไม่สามารถย้อนกลับได้ คุณแน่ใจหรือไม่?")
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("🔴 ใช่, ฉันยืนยันการลบ", use_container_width=True, type="primary"):
                        if gsheet_utils.delete_row_by_id("Members", _sh, st.session_state.confirm_delete_id, "MemberID"):
                            st.success(f"ลบข้อมูลของ '{st.session_state.confirm_delete_name}' เรียบร้อยแล้ว")
                            st.session_state.confirm_delete_id = None
                            st.session_state.confirm_delete_name = None
                            st.rerun()
                        else:
                            st.error("ไม่สามารถลบข้อมูลได้")
                with confirm_col2:
                    if st.button("🔵 ไม่, ยกเลิก", use_container_width=True, type="secondary"):
                        st.session_state.confirm_delete_id = None
                        st.session_state.confirm_delete_name = None
                        st.rerun()

            # --- 2B. New Loan Contract Form (เปลี่ยนจาก st.form เป็นปุ่มธรรมดา เพื่อให้ Interactive) ---
            st.markdown("---")
            st.subheader("💰 อนุมัติสัญญาเงินกู้ใหม่ (และยอดยกมา)")
            st.info("ระบุ 'วันที่เริ่มกู้' ระบบจะคำนวณวันหมดอายุสัญญาให้โดยอัตโนมัติ")

            col_loan_1, col_loan_2 = st.columns(2)
            with col_loan_1:
                loan_account = st.selectbox(
                    "เลือกบัญชีเงินกู้:", 
                    options=["บัญชี 1 (ตัดรอบ 5 พ.ย.)", "บัญชี 2 (ตัดรอบ 5 พ.ย.)", "บัญชี 3 (รายเดือน 4 ปี)", "บัญชี 4 (ตัดรอบ 5 ก.ค.)"], 
                    index=None, placeholder="--- เลือกบัญชี ---"
                )
                principal_amount_new = st.number_input("ยอดเงินต้นที่อนุมัติ (บาท):", min_value=0.0, step=1000.0)
            
            with col_loan_2:
                issue_date = st.date_input("วันที่ทำสัญญา / วันที่เริ่มกู้ (ปฏิทิน ค.ศ.)", value=date.today())
                st.caption(f"ตรงกับ พ.ศ.: **{format_thai_date(issue_date)}**") # แสดง พ.ศ. ให้แอดมินดูทันที
                
                # ส่วนรับข้อมูล "ยอดยกมา" (เด้งขึ้นมาทันทีเมื่อเลือกบัญชี 3)
                is_carry_over = False
                months_paid = 0
                if loan_account == "บัญชี 3 (รายเดือน 4 ปี)":
                    is_carry_over = st.checkbox("✅ เป็นสัญญายกยอดมา (ลูกค้าเคยผ่อนมาแล้วก่อนใช้แอป)")
                    if is_carry_over:
                        months_paid = st.number_input("จำนวนงวดที่ชำระไปแล้ว (งวด)", min_value=1, max_value=47, step=1, value=1)

            # --- พรีวิวค่างวดสำหรับบัญชี 3 ---
            monthly_principal, monthly_interest = 0.0, 0.0
            if loan_account == "บัญชี 3 (รายเดือน 4 ปี)" and principal_amount_new > 0:
                total_interest = principal_amount_new * 0.13 * 4
                monthly_total = (principal_amount_new + total_interest) / 48
                monthly_principal = principal_amount_new / 48
                monthly_interest = total_interest / 48
                
                st.info(f"💡 **พรีวิวบัญชี 3 (สัญญารายเดือน 48 งวด):**\n"
                        f"- ยอดส่งรวม: **{monthly_total:,.2f}** บาท/เดือน\n"
                        f"- (หักเป็นเงินต้น: **{monthly_principal:,.2f}** บาท | ดอกเบี้ย: **{monthly_interest:,.2f}** บาท)")
                
                if is_carry_over:
                    st.warning(f"⚠️ **ยอดยกมา:** ระบบจะบันทึกว่าลูกค้าจ่ายเงินต้นมาแล้ว **{monthly_principal * months_paid:,.2f}** บาท และจ่ายดอกเบี้ยแล้ว **{monthly_interest * months_paid:,.2f}** บาท (รวม {months_paid} งวด)")

            # ปุ่มกด (อยู่ข้างนอกฟอร์ม)
            new_loan_submitted = st.button("✅ อนุมัติสัญญาเงินกู้", use_container_width=True, type="primary")

            if new_loan_submitted:
                if not loan_account:
                    st.warning("กรุณาเลือกบัญชีเงินกู้")
                elif principal_amount_new <= 0:
                    st.warning("กรุณาระบุยอดเงินต้นให้ถูกต้อง")
                else:
                    with st.spinner("กำลังสร้างสัญญาเงินกู้..."):
                        data_entry_datetime = datetime.now(bangkok_tz)
                        data_entry_date_str = data_entry_datetime.strftime("%Y-%m-%d %H:%M:%S")

                        clean_loan_account = loan_account.split(" ")[0] + " " + loan_account.split(" ")[1]

                        if clean_loan_account == "บัญชี 3":
                            try: due_date = issue_date.replace(year=issue_date.year + 4)
                            except ValueError: due_date = issue_date.replace(year=issue_date.year + 4, day=28)
                        elif clean_loan_account in ["บัญชี 1", "บัญชี 2"]:
                            if issue_date.month > 11 or (issue_date.month == 11 and issue_date.day > 5):
                                due_date = date(issue_date.year + 1, 11, 5)
                            else: due_date = date(issue_date.year, 11, 5)
                        elif clean_loan_account == "บัญชี 4":
                            if issue_date.month > 7 or (issue_date.month == 7 and issue_date.day > 5):
                                due_date = date(issue_date.year + 1, 7, 5)
                            else: due_date = date(issue_date.year, 7, 5)
                        
                        issue_date_str = issue_date.strftime("%Y-%m-%d")
                        due_date_str = due_date.strftime("%Y-%m-%d")
                        
                        initial_principal_paid = 0.0
                        initial_interest_paid = 0.0
                        if clean_loan_account == "บัญชี 3" and is_carry_over:
                            initial_principal_paid = round(monthly_principal * months_paid, 2)
                            initial_interest_paid = round(monthly_interest * months_paid, 2)

                        loan_id = f"L-{member_id}-{clean_loan_account.replace(' ', '')}-{int(data_entry_datetime.timestamp())}"

                        new_loan_data = [
                            loan_id, member_id, clean_loan_account, issue_date_str, due_date_str,
                            principal_amount_new, initial_principal_paid, initial_interest_paid, 
                            "ยังค้างชำระ", data_entry_date_str
                        ]

                        if gsheet_utils.add_loan_contract(_sh, new_loan_data):
                            gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", {"LastUpdated": data_entry_date_str})
                            
                            if is_carry_over and (initial_principal_paid > 0 or initial_interest_paid > 0):
                                trans_id = f"PAY-CARRY-{int(data_entry_datetime.timestamp())}"
                                carry_over_payment_data = [
                                    trans_id, data_entry_date_str, member_id, loan_id,
                                    initial_principal_paid, initial_interest_paid
                                ]
                                gsheet_utils.add_row_to_sheet("PaymentHistory", _sh, carry_over_payment_data)

                            st.success(f"สร้างสัญญาเงินกู้ ID: {loan_id} สำเร็จ!")
                            st.info(f"📅 รอบสัญญา: **{format_thai_date(issue_date)}** ถึง **{format_thai_date(due_date)}**")
                            if is_carry_over:
                                st.info(f"📌 บันทึกประวัติ 'ยอดยกมา' จำนวน {months_paid} งวด เรียบร้อยแล้ว")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("ไม่สามารถสร้างสัญญาเงินกู้ได้")
else:
    st.info("ยังไม่มีข้อมูลสมาชิกในระบบ")
