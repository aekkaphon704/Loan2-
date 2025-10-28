# pages/2_✏️_แก้ไขและลบข้อมูล.py
import streamlit as st
import gsheet_utils
from datetime import datetime

# --- Session State Setup ---
if 'confirm_delete_id' not in st.session_state:
    st.session_state.confirm_delete_id = None
if 'confirm_delete_name' not in st.session_state:
    st.session_state.confirm_delete_name = None

_sh = gsheet_utils.connect_to_sheet()

st.set_page_config(page_title="แก้ไขข้อมูลสมาชิก", page_icon="✏️", layout="wide")
st.title("✏️ แก้ไขและลบข้อมูลสมาชิก")

# --- 1. Member Selection ---
members_df = gsheet_utils.get_data_as_dataframe("Members", _sh)
if not members_df.empty:
    member_options = dict(zip(members_df['Name'], members_df['MemberID']))
    
    selected_name = st.selectbox(
        "เลือกสมาชิกที่ต้องการแก้ไขหรือลบ:",
        options=member_options.keys(),
        index=None,
        placeholder="กรุณาเลือกชื่อ..."
    )

    # --- 2. Display Form and Logic ---
    if selected_name:
        member_id = member_options[selected_name]
        
        if st.session_state.confirm_delete_id and st.session_state.confirm_delete_id != member_id:
            st.session_state.confirm_delete_id = None
            st.session_state.confirm_delete_name = None

        member_data = gsheet_utils.get_member_by_id(_sh, member_id)

        if member_data:
            st.subheader(f"กำลังแก้ไขข้อมูลของ: {selected_name}")
            
            with st.form("edit_form"):
                dob_obj = datetime.strptime(member_data['DOB'], "%Y-%m-%d").date() if member_data.get('DOB') else None
                
                # Layout and Inputs inside the form
                st.markdown("**ข้อมูลส่วนตัว**")
                col_form_1, col_form_2 = st.columns(2)
                with col_form_1:
                    name = st.text_input("ชื่อ-สกุล", value=member_data.get('Name'))
                    address_no = st.text_input("บ้านเลขที่", value=member_data.get('AddressNo'))
                    village = st.text_input("หมู่บ้าน", value=member_data.get('Village'))
                    sub_district = st.text_input("ตำบล", value=member_data.get('SubDistrict'))
                with col_form_2:
                    district = st.text_input("อำเภอ", value=member_data.get('District'))
                    province = st.text_input("จังหวัด", value=member_data.get('Province'))
                    dob = st.date_input("วันเกิด", value=dob_obj, format="DD/MM/YYYY")

                st.markdown("**ข้อมูลการเงิน (แก้ไขเฉพาะยอดตั้งต้น)**")
                col_fin_1, col_fin_2 = st.columns(2)
                with col_fin_1:
                    savings = st.number_input("เงินฝากสัจจะ", value=member_data.get('Savings'))
                    loan1 = st.number_input("ยอดกู้ บช.1 (ตั้งต้น)", value=member_data.get('Loan1_Balance'))
                    loan4 = st.number_input("ยอดกู้ บช.4 (ตั้งต้น)", value=member_data.get('Loan4_Balance'))
                with col_fin_2:
                    shares = st.number_input("เงินหุ้น", value=member_data.get('Shares'))
                    loan2 = st.number_input("ยอดกู้ บช.2 (ตั้งต้น)", value=member_data.get('Loan2_Balance'))
                
                st.markdown("---")
                
                col_btn_1, col_btn_2 = st.columns(2)
                with col_btn_1:
                    save_button = st.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True)
                with col_btn_2:
                    delete_button = st.form_submit_button("🗑️ ลบสมาชิกคนนี้", type="secondary", use_container_width=True)

            # --- Logic after form submission ---
            if save_button:
                st.session_state.confirm_delete_id = None 
                st.session_state.confirm_delete_name = None
                
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # <-- รับค่าวันที่ปัจจุบัน
                dob_str = dob.strftime("%Y-%m-%d") if dob else None
                
                updates = {
                    "Name": name, "AddressNo": address_no, "Village": village,
                    "SubDistrict": sub_district, "District": district, "Province": province,
                    "DOB": dob_str, "Savings": savings, "Shares": shares,
                    "Loan1_Balance": loan1, "Loan2_Balance": loan2, "Loan4_Balance": loan4,
                    "LastUpdated": timestamp_str # <-- เพิ่มวันที่ปัจจุบันเข้าไปในข้อมูลที่จะอัปเดต
                }
                
                if gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", updates):
                    st.success(f"อัปเดตข้อมูลของ '{name}' เรียบร้อยแล้ว!")
                else:
                    st.error("ไม่สามารถอัปเดตข้อมูลได้")

            if delete_button:
                st.session_state.confirm_delete_id = member_id
                st.session_state.confirm_delete_name = selected_name
                st.rerun()

            # --- Confirmation Block (OUTSIDE the form) ---
            if st.session_state.confirm_delete_id == member_id:
                st.warning(f"**คุณกำลังจะลบข้อมูลของ {st.session_state.confirm_delete_name}**")
                st.markdown("การดำเนินการนี้ไม่สามารถย้อนกลับได้ คุณแน่ใจหรือไม่?")
                
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    # This is a regular st.button, now correctly placed outside the form.
                    if st.button("🔴 ใช่, ฉันยืนยันการลบ", use_container_width=True, type="primary"):
                        if gsheet_utils.delete_row_by_id("Members", _sh, st.session_state.confirm_delete_id, "MemberID"):
                            st.success(f"ลบข้อมูลของ '{st.session_state.confirm_delete_name}' เรียบร้อยแล้ว")
                            st.session_state.confirm_delete_id = None
                            st.session_state.confirm_delete_name = None
                            st.rerun()
                        else:
                            st.error("ไม่สามารถลบข้อมูลได้")
                with confirm_col2:
                    # This is also a regular st.button.
                    if st.button("🔵 ไม่, ยกเลิก", use_container_width=True, type="secondary"):
                        st.session_state.confirm_delete_id = None
                        st.session_state.confirm_delete_name = None
                        st.rerun()
else:
    st.info("ยังไม่มีข้อมูลสมาชิกในระบบ")