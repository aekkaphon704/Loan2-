# app.py
import streamlit as st
import gsheet_utils
import pdf_utils
from datetime import datetime, date
from babel.dates import format_date

# --- 1. ค่าคงที่และพจนานุกรม ---
THAI_HEADERS = {
    "MemberID": "รหัสสมาชิก", "Name": "ชื่อ-สกุล", "AddressNo": "บ้านเลขที่",
    "Village": "หมู่บ้าน", "SubDistrict": "ตำบล", "District": "อำเภอ",
    "Province": "จังหวัด", "DOB": "วันเกิด (ป-ด-ว)", "Savings": "เงินฝากสัจจะ",
    "Shares": "หุ้น", "Loan1_Balance": "ยอดกู้ บช.1",
    "Loan2_Balance": "ยอดกู้ บช.2", "Loan4_Balance": "ยอดกู้ บช.4",
    "Loan1_InterestDue": "ดบ.ค้าง(1)",
    "Loan2_InterestDue": "ดบ.ค้าง(2)",
    "Loan4_InterestDue": "ดบ.ค้าง(4)",
    "LastUpdated": "อัปเดตล่าสุด"  # <-- เพิ่มบรรทัดนี้
}

# --- 2. การตั้งค่าและฟังก์ชัน Helper ---
st.set_page_config(page_title="ระบบจัดการสมาชิก", page_icon="🗂️", layout="wide")

def format_thai_date(dt):
    if dt is None: return "ไม่ได้ระบุ"
    return format_date(dt, format='d MMMM yyyy', locale='th_TH')

@st.cache_data(ttl=60)
def get_address_suggestions(_sh):
    df = gsheet_utils.get_data_as_dataframe("Members", _sh)
    if df.empty: return {k: [] for k in ["villages", "sub_districts", "districts", "provinces"]}
    return {
        "villages": sorted(df["Village"].dropna().unique().tolist()),
        "sub_districts": sorted(df["SubDistrict"].dropna().unique().tolist()),
        "districts": sorted(df["District"].dropna().unique().tolist()),
        "provinces": sorted(df["Province"].dropna().unique().tolist())
    }

# --- 3. เชื่อมต่อและเตรียมข้อมูล ---
_sh = gsheet_utils.connect_to_sheet()
address_data = get_address_suggestions(_sh)

st.title("🗂️ ระบบจัดการสมาชิกและหนี้สิน")
st.caption(f"เชื่อมต่อกับ Google Sheet: '{gsheet_utils.SHEET_NAME}' สำเร็จ")

# --- 4. ส่วนเพิ่มสมาชิกใหม่ ---
st.header("1. เพิ่มสมาชิกใหม่")

with st.form("add_member_form", clear_on_submit=True):
    st.subheader("ส่วนที่ 1: ข้อมูลส่วนตัว")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("ชื่อ-สกุล")
        address_no = st.text_input("บ้านเลขที่")
        village_select = st.selectbox("หมู่บ้าน (เลือกจากที่มีอยู่)", [None] + address_data["villages"], index=0, format_func=lambda x: "--- เลือก ---" if x is None else x)
        village_new = st.text_input("...หรือ พิมพ์หมู่บ้านใหม่ที่นี่")
        sub_district_select = st.selectbox("ตำบล (เลือกจากที่มีอยู่)", [None] + address_data["sub_districts"], index=0, format_func=lambda x: "--- เลือก ---" if x is None else x)
        sub_district_new = st.text_input("...หรือ พิมพ์ตำบลใหม่ที่นี่")

    with col2:
        district_select = st.selectbox("อำเภอ (เลือกจากที่มีอยู่)", [None] + address_data["districts"], index=0, format_func=lambda x: "--- เลือก ---" if x is None else x)
        district_new = st.text_input("...หรือ พิมพ์อำเภอใหม่ที่นี่")
        province_select = st.selectbox("จังหวัด (เลือกจากที่มีอยู่)", [None] + address_data["provinces"], index=0, format_func=lambda x: "--- เลือก ---" if x is None else x)
        province_new = st.text_input("...หรือ พิมพ์จังหวัดใหม่ที่นี่")
        today = date.today()
        dob = st.date_input("วันเดือนปีเกิด", value=None, format="DD/MM/YYYY",
                            min_value=date(today.year - 100, 1, 1), max_value=today)
        member_id = f"M-{int(datetime.now().timestamp())}"

    st.subheader("ส่วนที่ 2: ข้อมูลการเงิน")
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a: savings = st.number_input("เงินฝากสัจจะ", min_value=0.0, step=100.0)
    with col_b: shares = st.number_input("เงินหุ้น", min_value=0.0, step=100.0)
    with col_c: loan1 = st.number_input("ยอดกู้ บช.1", min_value=0.0, step=1000.0)
    with col_d: loan2 = st.number_input("ยอดกู้ บช.2", min_value=0.0, step=1000.0)
    with col_e: loan4 = st.number_input("ยอดกู้ บช.4", min_value=0.0, step=1000.0)
    
    submitted = st.form_submit_button("บันทึกข้อมูลสมาชิก")

# --- 5. ตรรกะการบันทึกข้อมูล ---
if submitted:
    village = village_select if village_select is not None else village_new
    sub_district = sub_district_select if sub_district_select is not None else sub_district_new
    district = district_select if district_select is not None else district_new
    province = province_select if province_select is not None else province_new

    if not name:
        st.warning("กรุณากรอก 'ชื่อ-สกุล' ด้วยครับ")
    elif not village or not sub_district or not district or not province:
        st.warning("กรุณากรอกข้อมูลที่อยู่ให้ครบถ้วน (เลือก หรือ พิมพ์ใหม่)")
    else:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # <-- รับค่าวันที่ปัจจุบัน
        dob_str = dob.strftime("%Y-%m-%d") if dob else None
        
        new_row_data = [
            member_id, name, address_no, village, sub_district, district, province,
            dob_str, savings, shares, loan1, loan2, loan4,
            0, 0, 0,
            timestamp_str  # <-- เพิ่มวันที่ปัจจุบันเข้าไปในข้อมูลที่จะบันทึก
        ]
        
        if gsheet_utils.add_row_to_sheet("Members", _sh, new_row_data):
            st.success(f"บันทึกข้อมูลคุณ '{name}' เรียบร้อย!")
            get_address_suggestions.clear()
        else:
            st.error("ไม่สามารถบันทึกข้อมูลได้")

# --- 6. ส่วนของการแสดงข้อมูลทั้งหมด ---
st.header("2. ข้อมูลสมาชิกทั้งหมด")
if st.button("รีเฟรชข้อมูลสมาชิก"):
    get_address_suggestions.clear()
    gsheet_utils.get_data_as_dataframe.clear()
    st.rerun()
st.info("💡 หากต้องการแก้ไขหรือลบข้อมูล กรุณาไปที่เมนู '✏️ แก้ไขและลบข้อมูล' ด้านซ้ายมือ")
members_df = gsheet_utils.get_data_as_dataframe("Members", _sh)
if members_df.empty:
    st.info("ยังไม่มีข้อมูลสมาชิกในระบบ")
else:
    display_df = members_df.rename(columns=THAI_HEADERS)
    display_df.index = range(1, len(display_df) + 1)
    display_df.index.name = "ลำดับ"
    display_columns = [col for col in THAI_HEADERS.values() if col in display_df.columns]
    st.dataframe(display_df[display_columns], use_container_width=True)

# --- 7. *** ส่วนตรวจสอบยอดและชำระเงิน  ---
st.header("3. ตรวจสอบยอดและชำระเงิน")
st.markdown("---") 

members_df_for_payment = gsheet_utils.get_data_as_dataframe("Members", _sh)

if members_df_for_payment.empty:
    st.info("กรุณาเพิ่มข้อมูลสมาชิกก่อน")
else:
    # --- 1. ช่องเลือก (ย้ายออกมานอกฟอร์ม) ---
    member_names = members_df_for_payment["Name"].tolist()
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        selected_name = st.selectbox(
            "เลือกสมาชิก:", 
            options=member_names, 
            index=None, 
            placeholder="กรุณาเลือกชื่อ...",
            key="payment_member_name"
        )
    with col_sel2:
        account_paid = st.selectbox(
            "เลือกบัญชี:", 
            options=["1", "2", "4"], 
            index=None, 
            placeholder="เลือกบัญชี...",
            key="payment_account_num"
        )

    # --- 2. ตรรกะดึงข้อมูลอัตโนมัติ (เพิ่มยอดคงเหลือ) ---
    prefilled_interest = 0.0
    prefilled_balance = 0.0  # <-- (เพิ่ม) ตัวแปรเก็บยอดคงเหลือ
    
    if selected_name and account_paid:
        try:
            member_info = members_df_for_payment[members_df_for_payment["Name"] == selected_name].to_dict('records')[0]
            
            # (เพิ่ม) ดึงยอดคงเหลือ
            balance_col = f"Loan{account_paid}_Balance"
            if balance_col in member_info:
                prefilled_balance = float(member_info[balance_col])

            # ดึงดอกเบี้ย
            interest_due_col = f"Loan{account_paid}_InterestDue"
            if interest_due_col in member_info:
                prefilled_interest = float(member_info[interest_due_col])
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")

    # --- 3. แดชบอร์ดสรุปยอด (ส่วนที่เพิ่มใหม่) และฟอร์มชำระเงิน ---
    if selected_name and account_paid:
        
        # *** นี่คือ "แดชบอร์ด" ที่คุณต้องการ ***
        st.subheader(f"สรุปยอดบัญชี (คุณ: {selected_name} | บัญชี: {account_paid})")
        col_metric1, col_metric2 = st.columns(2)
        with col_metric1:
            st.metric(
                label=f"💰 ยอดเงินกู้คงเหลือ (บช. {account_paid})", 
                value=f"{prefilled_balance:,.2f} บาท"
            )
        with col_metric2:
            st.metric(
                label=f"📈 ดอกเบี้ยค้างชำระ (บช. {account_paid})", 
                value=f"{prefilled_interest:,.2f} บาท",
                delta=f"{prefilled_interest:,.2f} บาท", # (เพิ่มสีแดงถ้ายอด > 0)
                delta_color="inverse" if prefilled_interest > 0 else "off"
            )
        # **********************************
        
        with st.form("payment_form", clear_on_submit=True):
            st.markdown("**กรอกข้อมูลการชำระเงิน**")
            payment_date = st.date_input("วันที่ชำระ", value=date.today(), format="DD/MM/YYYY")

            col_amount1, col_amount2 = st.columns(2)
            with col_amount1:
                interest_paid = st.number_input(
                    "ชำระดอกเบี้ย (ระบบกรอกอัตโนมัติ)", 
                    min_value=0.0, 
                    value=prefilled_interest, # <-- กรอกอัตโนมัติ!
                    step=100.0
                )
            with col_amount2:
                principal_paid = st.number_input("ชำระเงินต้น", min_value=0.0, step=100.0)
                
            payment_submitted = st.form_submit_button("บันทึกการชำระเงิน")

        # --- 4. ตรรกะการบันทึก (เหมือนเดิม) ---
        if payment_submitted:
            member_info = members_df_for_payment[members_df_for_payment["Name"] == selected_name].to_dict('records')[0]
            member_id = member_info["MemberID"]
            
            loan_column_name = f"Loan{account_paid}_Balance"
            interest_due_col = f"Loan{account_paid}_InterestDue"
            
            new_balance = member_info[loan_column_name] - principal_paid
            new_interest_due = member_info[interest_due_col] - interest_paid 
            
            payment_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            transaction_id = f"T-{int(datetime.now().timestamp())}"
            payment_row = [
                transaction_id, payment_timestamp, member_id, 
                account_paid, principal_paid, interest_paid
            ]
            gsheet_utils.add_row_to_sheet("PaymentHistory", _sh, payment_row)

            updates = {
                loan_column_name: new_balance,
                interest_due_col: new_interest_due
            }
            success = gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", updates)

            if success:
                st.success(f"บันทึกการชำระเงินของ '{selected_name}' เรียบร้อย!")
                
                latest_member_info = gsheet_utils.get_member_by_id(_sh, member_id)
                st.session_state['receipt_data'] = {
                    "member_info": latest_member_info,
                    "payment_date": format_thai_date(payment_date),
                    "account_paid": account_paid,
                    "principal_paid": principal_paid,
                    "interest_paid": interest_paid,
                    "total_paid": principal_paid + interest_paid,
                    "new_balances": latest_member_info
                }
                st.rerun()
            else:
                st.error("เกิดข้อผิดพลาดในการอัปเดตยอดหนี้")

# --- 8. ส่วนแสดงปุ่มดาวน์โหลดใบเสร็จ (เหมือนเดิม) ---
if 'receipt_data' in st.session_state and st.session_state['receipt_data']:
    receipt_info = st.session_state['receipt_data']
    st.info(f"ข้อมูลสำหรับสร้างใบเสร็จของ '{receipt_info['member_info']['Name']}' พร้อมแล้ว")
    
    pdf_bytes = pdf_utils.generate_receipt_pdf(receipt_info)
    
    st.download_button(
        label="📄 ดาวน์โหลดใบเสร็จ (PDF)",
        data=bytes(pdf_bytes),
        file_name=f"Receipt_{receipt_info['member_info']['Name']}_{date.today().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
    if st.button("เริ่มการชำระเงินครั้งใหม่"):
        del st.session_state['receipt_data']
        st.rerun()
st.markdown("**ระบบมีปัญหาติดต่อ FB : เอกพล  แข็งแรง**")