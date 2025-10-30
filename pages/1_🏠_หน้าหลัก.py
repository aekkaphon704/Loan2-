# pages/1_🏠_หน้าหลัก.py
import streamlit as st
import gsheet_utils
import pdf_utils
from datetime import datetime, date
from babel.dates import format_date
from pytz import timezone
import pandas as pd # เพิ่ม import pandas

# --- 1. ค่าคงที่และพจนานุกรม ---
THAI_HEADERS = {
    "MemberID": "รหัสสมาชิก", "Name": "ชื่อ-สกุล", "AddressNo": "บ้านเลขที่",
    "Village": "หมู่บ้าน", "SubDistrict": "ตำบล", "District": "อำเภอ",
    "Province": "จังหวัด", "DOB": "วันเกิด (ป-ด-ว)", "Savings": "เงินฝากสัจจะ",
    "Shares": "หุ้นสะสม (บาท)",
    "Loan1_Balance": "ยอดกู้ บช.1", "Loan2_Balance": "ยอดกู้ บช.2", "Loan4_Balance": "ยอดกู้ บช.4",
    "Loan1_InterestDue": "ดบ.ค้าง(1)", "Loan2_InterestDue": "ดบ.ค้าง(2)", "Loan4_InterestDue": "ดบ.ค้าง(4)",
    "LastSharePurchaseDate": "ซื้อหุ้นล่าสุด",
    "LastUpdated": "อัปเดตล่าสุด"
}

# --- 2. การตั้งค่าและฟังก์ชัน Helper ---
st.set_page_config(page_title="ระบบจัดการสมาชิก", page_icon="🗂️", layout="wide")

def format_thai_date(dt):
    if dt is None: return "ไม่ได้ระบุ"
    if isinstance(dt, str):
        try: dt = datetime.strptime(dt, "%Y-%m-%d").date()
        except ValueError: return dt
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

def safe_float(value):
    return float(value) if value not in [None, ''] else 0.0

# --- 3. เชื่อมต่อและเตรียมข้อมูล ---
_sh = gsheet_utils.connect_to_sheet()
address_data = get_address_suggestions(_sh)

st.title("🏠 หน้าหลัก: จัดการข้อมูล")

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
    with col_b: shares = st.number_input("เงินหุ้น (บาท)", min_value=0.0, step=100.0)
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

    if not name or not village or not sub_district or not district or not province:
        st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")
    else:
        bangkok_tz = timezone("Asia/Bangkok")
        timestamp_str = datetime.now(bangkok_tz).strftime("%Y-%m-%d %H:%M:%S")
        dob_str = dob.strftime("%Y-%m-%d") if dob else None
        
        new_row_data = [
            member_id, name, address_no, village, sub_district, district, province,
            dob_str, savings, shares, loan1, loan2, loan4,
            0, 0, 0, # ดอกเบี้ย
            "",      # <-- LastSharePurchaseDate (ค่าว่าง)
            timestamp_str
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
    
    if "หุ้นสะสม (บาท)" in display_df.columns:
        # ใช้ pd.to_numeric เพื่อแปลงอย่างปลอดภัย
        numeric_shares = pd.to_numeric(display_df["หุ้นสะสม (บาท)"], errors='coerce')
        safe_shares = numeric_shares.fillna(0)
        display_df.loc[:, "หุ้น (หน่วย)"] = (safe_shares / 50).astype(int)
    
    display_df.index = range(1, len(display_df) + 1)
    display_df.index.name = "ลำดับ"
    
    display_columns = [col for col in THAI_HEADERS.values() if col in display_df.columns]
    if "หุ้น (หน่วย)" in display_df.columns:
        try:
            col_index = display_columns.index("หุ้นสะสม (บาท)")
            display_columns.insert(col_index + 1, "หุ้น (หน่วย)")
        except ValueError:
            pass

    st.dataframe(display_df[display_columns], use_container_width=True)

# --- 7. ส่วนตรวจสอบยอดและทำธุรกรรม ---
st.header("3. ตรวจสอบยอดและทำธุรกรรม")
st.markdown("---") 

members_df_for_payment = gsheet_utils.get_data_as_dataframe("Members", _sh)

if members_df_for_payment.empty:
    st.info("กรุณาเพิ่มข้อมูลสมาชิกก่อน")
else:
    member_names = members_df_for_payment["Name"].tolist()
    selected_name = st.selectbox(
        "เลือกสมาชิก:", 
        options=member_names, 
        index=None, 
        placeholder="กรุณาเลือกชื่อ...",
        key="transaction_member_name"
    )

    if selected_name:
        member_info = members_df_for_payment[members_df_for_payment["Name"] == selected_name].to_dict('records')[0]
        member_id = member_info["MemberID"]
        bangkok_tz = timezone("Asia/Bangkok")
        
        transaction_type = st.radio(
            "เลือกประเภทธุรกรรม:",
            ("ชำระหนี้เงินกู้", "ซื้อหุ้นประจำปี", "ฝากเงินสัจจะ"),
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # ------------------------------------
        #       กรณี "ชำระหนี้เงินกู้"
        # ------------------------------------
        if transaction_type == "ชำระหนี้เงินกู้":
            account_paid = st.selectbox( "เลือกบัญชี:", options=["1", "2", "4"], index=None, placeholder="เลือกบัญชี...")
            
            if account_paid:
                balance_col = f"Loan{account_paid}_Balance"
                interest_due_col = f"Loan{account_paid}_InterestDue"
                
                prefilled_balance = safe_float(member_info.get(balance_col))
                prefilled_interest = safe_float(member_info.get(interest_due_col))

                st.subheader(f"สรุปยอดบัญชี (คุณ: {selected_name} | บัญชี: {account_paid})")
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric(label=f"💰 ยอดเงินกู้คงเหลือ (บช. {account_paid})", value=f"{prefilled_balance:,.2f} บาท")
                with col_metric2:
                    st.metric(label=f"📈 ดอกเบี้ยค้างชำระ (บช. {account_paid})", 
                              value=f"{prefilled_interest:,.2f} บาท",
                              delta=f"{prefilled_interest:,.2f} บาท" if prefilled_interest > 0 else None,
                              delta_color="inverse")
                
                with st.form("payment_form", clear_on_submit=True):
                    st.markdown("**กรอกข้อมูลการชำระเงิน**")
                    payment_date = st.date_input("วันที่ชำระ", value=date.today(), format="DD/MM/YYYY")
                    col_amount1, col_amount2 = st.columns(2)
                    with col_amount1:
                        interest_paid = st.number_input("ชำระดอกเบี้ย (ระบบกรอกอัตโนมัติ)", 
                                                        min_value=0.0, 
                                                        value=max(0.0, prefilled_interest),
                                                        step=100.0)
                    with col_amount2:
                        principal_paid = st.number_input("ชำระเงินต้น", min_value=0.0, step=100.0)
                    payment_submitted = st.form_submit_button("บันทึกการชำระเงิน")
                
                if payment_submitted:
                    timestamp_str = datetime.now(bangkok_tz).strftime("%Y-%m-%d %H:%M:%S")
                    new_balance = prefilled_balance - principal_paid
                    new_interest_due = prefilled_interest - interest_paid
                    
                    transaction_id = f"T-{int(datetime.now().timestamp())}"
                    payment_row = [transaction_id, timestamp_str, member_id, account_paid, principal_paid, interest_paid]
                    gsheet_utils.add_row_to_sheet("PaymentHistory", _sh, payment_row)

                    updates = {
                        balance_col: new_balance,
                        interest_due_col: new_interest_due,
                        "LastUpdated": timestamp_str
                    }
                    success = gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", updates)

                    if success:
                        st.success(f"บันทึกการชำระเงินของ '{selected_name}' เรียบร้อย!")
                        latest_member_info = gsheet_utils.get_member_by_id(_sh, member_id)
                        
                        receipt_line_items = []
                        if principal_paid > 0:
                            receipt_line_items.append({'label': f"ชำระเงินต้น บัญชี {account_paid}", 'amount': principal_paid})
                        if interest_paid > 0:
                            receipt_line_items.append({'label': f"ชำระดอกเบี้ย บัญชี {account_paid}", 'amount': interest_paid})
                        
                        receipt_balances = [
                            {'label': 'ยอดกู้ บช.1 คงเหลือ', 'amount': safe_float(latest_member_info.get('Loan1_Balance'))},
                            {'label': 'ยอดกู้ บช.2 คงเหลือ', 'amount': safe_float(latest_member_info.get('Loan2_Balance'))},
                            {'label': 'ยอดกู้ บช.4 คงเหลือ', 'amount': safe_float(latest_member_info.get('Loan4_Balance'))}
                        ]

                        st.session_state['receipt_data'] = {
                            "member_info": latest_member_info,
                            "payment_date": format_thai_date(payment_date),
                            "line_items": receipt_line_items,
                            "balance_summary": receipt_balances
                        }
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาดในการอัปเดตยอดหนี้")

        # ------------------------------------
        #       กรณี "ซื้อหุ้นประจำปี"
        # ------------------------------------
        elif transaction_type == "ซื้อหุ้นประจำปี":
            st.subheader(f"ซื้อหุ้นประจำปี (คุณ: {selected_name})")
            
            today = date.today()
            purchase_period_start = date(today.year, 10, 5) # (เดือน 11, วันที่ 5)
            
            current_shares_baht = safe_float(member_info.get('Shares'))
            current_shares_units = int(current_shares_baht / 50)
            
            col_share1, col_share2 = st.columns(2)
            with col_share1:
                st.metric("หุ้นสะสมปัจจุบัน", 
                          f"{current_shares_baht:,.0f} บาท", 
                          f"{current_shares_units} หุ้น")
            with col_share2:
                st.metric("ยอดซื้อประจำปี", "100.00 บาท", "2 หุ้น x 50 บาท")
            
            if today < purchase_period_start:
                st.error(f"ยังไม่ถึงรอบการซื้อหุ้นประจำปี")
                st.info(f"รอบการซื้อหุ้นสำหรับปี {today.year} จะเริ่มในวันที่ 5 พฤศจิกายน {today.year} ครับ")
                
            else:
                last_purchase_str = member_info.get("LastSharePurchaseDate")
                needs_to_buy = False
                
                if not last_purchase_str or last_purchase_str == "":
                    needs_to_buy = True
                else:
                    try:
                        last_purchase_date = datetime.strptime(last_purchase_str, "%Y-%m-%d").date()
                        if last_purchase_date.year < today.year:
                            needs_to_buy = True
                    except ValueError:
                        needs_to_buy = True
                
                if needs_to_buy:
                    st.warning(f"**สถานะ:** อยู่ในช่วงที่สามารถซื้อหุ้นรอบปี {today.year} ได้")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        buy_button = st.button("ยืนยันการซื้อหุ้น (100 บาท)", type="primary", use_container_width=True)
                    with col_btn2:
                        no_buy_button = st.button("ไม่ต้องการซื้อหุ้นในปีนี้", use_container_width=True)

                    if buy_button:
                        with st.spinner("กำลังบันทึกการซื้อหุ้น..."):
                            timestamp_str = datetime.now(bangkok_tz).strftime("%Y-%m-%d %H:%M:%S")
                            today_str = date.today().strftime("%Y-%m-%d")

                            new_share_balance = current_shares_baht + 100
                            updates = {
                                "Shares": new_share_balance,
                                "LastSharePurchaseDate": today_str,
                                "LastUpdated": timestamp_str
                            }
                            gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", updates)

                            transaction_id = f"S-{int(datetime.now().timestamp())}"
                            history_row = [transaction_id, timestamp_str, member_id, 2, 100, "Purchase"] # <-- เพิ่ม Type
                            gsheet_utils.add_row_to_sheet("ShareHistory", _sh, history_row)
                            
                            st.success("บันทึกการซื้อหุ้นเรียบร้อย!")
                            
                            latest_member_info = gsheet_utils.get_member_by_id(_sh, member_id)
                            st.session_state['receipt_data'] = {
                                "member_info": latest_member_info,
                                "payment_date": format_thai_date(date.today()),
                                "line_items": [{'label': "ซื้อหุ้นประจำปี (2 หุ้น)", 'amount': 100.00}],
                                "balance_summary": [
                                    {'label': 'หุ้นสะสมคงเหลือ', 'amount': latest_member_info.get('Shares', 0), 'unit': 'บาท'},
                                    {'label': 'จำนวนหุ้นคงเหลือ', 'amount': int(latest_member_info.get('Shares', 0) / 50), 'unit': 'หุ้น'}
                                ]
                            }
                            st.rerun()

                    if no_buy_button:
                        with st.spinner("กำลังบันทึกการตัดสินใจ..."):
                            timestamp_str = datetime.now(bangkok_tz).strftime("%Y-%m-%d %H:%M:%S")
                            today_str = date.today().strftime("%Y-%m-%d")
                            
                            updates = {
                                "LastSharePurchaseDate": today_str,
                                "LastUpdated": timestamp_str
                            }
                            gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", updates)
                            
                            transaction_id = f"S-{int(datetime.now().timestamp())}"
                            history_row = [transaction_id, timestamp_str, member_id, 0, 0, "Declined"] # <-- บันทึกหลักฐาน
                            gsheet_utils.add_row_to_sheet("ShareHistory", _sh, history_row)

                            st.info(f"รับทราบการตัดสินใจ 'ไม่ซื้อหุ้น' ของคุณในปีนี้เรียบร้อยแล้ว (ปุ่มจะกลับมาอีกครั้งในปี {today.year + 1})")
                            st.rerun()
                else:
                    st.success(f"**สถานะ:** คุณได้ดำเนินการ (ซื้อ หรือ ไม่ซื้อ) หุ้นสำหรับปี {today.year} เรียบร้อยแล้ว")

        # ------------------------------------
        #       กรณี "ฝากเงินสัจจะ"
        # ------------------------------------
        elif transaction_type == "ฝากเงินสัจจะ":
            st.subheader(f"ฝากเงินออมสัจจะ (คุณ: {selected_name})")
            
            current_savings = safe_float(member_info.get('Savings'))
            st.metric("ยอดเงินฝากสัจจะปัจจุบัน", f"{current_savings:,.2f} บาท")
            
            with st.form("deposit_form"):
                deposit_amount = st.number_input("จำนวนเงินที่ต้องการฝาก", min_value=1.0, step=50.0)
                deposit_date = st.date_input("วันที่ฝาก", value=date.today(), format="DD/MM/YYYY")
                
                deposit_submitted = st.form_submit_button("ยืนยันการฝากเงิน")

            if deposit_submitted:
                with st.spinner("กำลังบันทึกเงินฝาก..."):
                    timestamp_str = datetime.now(bangkok_tz).strftime("%Y-%m-%d %H:%M:%S")

                    new_savings_balance = current_savings + deposit_amount
                    updates = { 
                        "Savings": new_savings_balance,
                        "LastUpdated": timestamp_str
                    }
                    gsheet_utils.update_member_data("Members", _sh, member_id, "MemberID", updates)

                    transaction_id = f"D-{int(datetime.now().timestamp())}"
                    history_row = [transaction_id, timestamp_str, member_id, deposit_amount]
                    gsheet_utils.add_row_to_sheet("SavingsHistory", _sh, history_row)
                    
                    st.success(f"บันทึกเงินฝาก {deposit_amount:,.2f} บาท เรียบร้อย! ยอดคงเหลือใหม่: {new_savings_balance:,.2f} บาท")
                    
                    latest_member_info = gsheet_utils.get_member_by_id(_sh, member_id)
                    
                    st.session_state['receipt_data'] = {
                        "member_info": latest_member_info,
                        "payment_date": format_thai_date(deposit_date),
                        "line_items": [
                            {'label': "ฝากเงินออมสัจจะ", 'amount': deposit_amount}
                        ],
                        "balance_summary": [
                            {'label': 'เงินฝากสัจจะคงเหลือ', 'amount': latest_member_info.get('Savings', 0), 'unit': 'บาท'}
                        ]
                    }
                    st.rerun()

# --- 8. ส่วนแสดงปุ่มดาวน์โหลดใบเสร็จ และ ปุ่มเริ่มใหม่ ---
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

# --- ปุ่มเริ่มธุรกรรมใหม่ (อยู่นอก if) ---
if selected_name: # จะแสดงปุ่มนี้ก็ต่อเมื่อมีการเลือกชื่อแล้ว
    if st.button("เริ่มธุรกรรมใหม่ / ล้างข้อมูลใบเสร็จ"):
        if 'receipt_data' in st.session_state:
            del st.session_state['receipt_data']
        st.rerun()
