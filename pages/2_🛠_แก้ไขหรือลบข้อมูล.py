# pages/2_✏️_แก้ไขและลบข้อมูล.py
import streamlit as st
import gsheet_utils
from datetime import datetime, date, timedelta
from pytz import timezone

# --- 1. พจนานุกรม (เอา Loan Balance ออก) ---
THAI_HEADERS_REVERSE = {
    "รหัสสมาชิก": "MemberID", "ชื่อ-สกุล": "Name", "บ้านเลขที่": "AddressNo",
    "หมู่บ้าน": "Village", "ตำบล": "SubDistrict", "อำเภอ": "District",
    "จังหวัด": "Province", "วันเกิด (ป-ด-ว)": "DOB", "เงินฝากสัจจะ": "Savings",
    "หุ้นสะสม (บาท)": "Shares",
    "อัปเดตล่าสุด": "LastUpdated"
}

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

    # --- 2. Display Forms and Logic when member is selected ---
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
                    dob = st.date_input("วันเกิด", value=dob_obj, format="DD/MM/YYYY")
                    shares = st.number_input("เงินหุ้น (บาท, ยอดปัจจุบัน)", value=gsheet_utils.safe_float(member_data.get('Shares')))

                st.markdown("---")
                col_btn_1, col_btn_2 = st.columns(2)
                with col_btn_1:
                    save_button = st.form_submit_button("💾 บันทึกการแก้ไขข้อมูล", use_container_width=True)
                with col_btn_2:
                    delete_button = st.form_submit_button("🗑️ ลบสมาชิกคนนี้", type="secondary", use_container_width=True)

            # --- Logic after edit/delete form submission ---
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

            # --- Delete Confirmation Block (OUTSIDE the form) ---
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

            st.markdown("---")

            # --- 2B. New Loan Contract Form ---
            st.subheader("💰 อนุมัติสัญญาเงินกู้ใหม่")
            st.info("ระบบจะกำหนดรอบสัญญาวันที่ 5 ก.ค. หรือ 5 พ.ย. ให้อัตโนมัติ โดยอิงจาก 'วันที่คุณกำลังกรอกข้อมูล' นี้")

            with st.form("new_loan_form", clear_on_submit=True):
                col_loan_1, col_loan_2 = st.columns(2)
                with col_loan_1:
                    loan_account = st.selectbox("เลือกบัญชีเงินกู้:", options=["1", "2", "4"], index=None, placeholder="--- เลือก ---")
                with col_loan_2:
                    principal_amount_new = st.number_input("ยอดเงินต้นที่อนุมัติ:", min_value=100.0, step=100.0)

                new_loan_submitted = st.form_submit_button("อนุมัติสัญญาเงินกู้ใหม่")

            if new_loan_submitted:
                if not loan_account:
                    st.warning("กรุณาเลือกบัญชีเงินกู้")
                else:
                    with st.spinner("กำลังสร้างสัญญาเงินกู้..."):
                        
                        today = date.today()
                        this_year = today.year
                        data_entry_datetime = datetime.now(bangkok_tz)
                        data_entry_date_str = data_entry_datetime.strftime("%Y-%m-%d %H:%M:%S")

                        if loan_account in ["1", "2"]:
                            cut_off_date = date(this_year, 11, 5)
                            if today < cut_off_date:
                                issue_date = date(this_year - 1, 11, 5)
                                due_date = date(this_year, 11, 5)
                            else:
                                issue_date = date(this_year, 11, 5)
                                due_date = date(this_year + 1, 11, 5)
                        
                        elif loan_account == "4":
                            cut_off_date = date(this_year, 7, 5)
                            if today < cut_off_date:
                                issue_date = date(this_year - 1, 7, 5)
                                due_date = date(this_year, 7, 5)
                            else:
                                issue_date = date(this_year, 7, 5)
                                due_date = date(this_year + 1, 7, 5)
                        
                        issue_date_str = issue_date.strftime("%Y-%m-%d")
                        due_date_str = due_date.strftime("%Y-%m-%d")
                        
                        loan_id = f"L-{member_id}-{loan_account}-{int(data_entry_datetime.timestamp())}"

                        # LoanID, MemberID, LoanAccount, IssueDate, DueDate,
                        # PrincipalAmount, AmountPaid, InterestPaid, Status, DataEntryDate
                        new_loan_data = [
                            loan_id, member_id, loan_account, issue_date_str, due_date_str,
                            principal_amount_new, 0, 0, 
                            "ยังค้างชำระ", # <-- ใช้ภาษาไทย
                            data_entry_date_str
                        ]

                        if gsheet_utils.add_loan_contract(_sh, new_loan_data):
                            gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", {"LastUpdated": data_entry_date_str})
                            st.success(f"สร้างสัญญาเงินกู้ ID: {loan_id} สำเร็จ!")
                            st.info(f"รอบสัญญาที่กำหนด: {issue_date_str} ถึง {due_date_str}")
                        else:
                            st.error("ไม่สามารถสร้างสัญญาเงินกู้ได้")
else:
    st.info("ยังไม่มีข้อมูลสมาชิกในระบบ")
