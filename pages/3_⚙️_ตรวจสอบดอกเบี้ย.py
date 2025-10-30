# pages/3_⚙️_เครื่องมือแอดมิน.py (หรือชื่อไฟล์ที่คุณใช้)
import streamlit as st
import gsheet_utils
from datetime import datetime, date
from babel.dates import format_date

# --- ฟังก์ชัน Helper (เฉพาะหน้านี้) ---
def format_thai_date_admin(dt):
    if dt is None: return "ไม่ได้ระบุ"
    if isinstance(dt, str):
        try: dt = datetime.strptime(dt, "%Y-%m-%d").date()
        except ValueError: return dt # ถ้าแปลงไม่ได้ ก็แสดงค่าเดิม
    return format_date(dt, format='d MMMM yyyy', locale='th_TH')

st.set_page_config(page_title="เครื่องมือแอดมิน", page_icon="⚙️", layout="centered")
st.title("⚙️ เครื่องมือสำหรับผู้ดูแลระบบ")

_sh = gsheet_utils.connect_to_sheet()

today = date.today()
st.info(f"วันนี้วันที่: **{format_thai_date_admin(today)}**")

st.markdown("---")

# --- ส่วนที่ 1: คำนวณดอกเบี้ย บัญชี 4 (แก้ไข Error Handling) ---
st.subheader("1. คำนวณดอกเบี้ย (รอบ 5 ก.ค. - บัญชี 4)")

last_calc_acc4_str = gsheet_utils.get_system_config(_sh, "LastCalc_Acc4")
last_calc_acc4 = date(1900, 1, 1) # ตั้งค่าเริ่มต้นเป็นวันที่เก่ามาก

if last_calc_acc4_str:
    try:
        last_calc_acc4 = datetime.strptime(last_calc_acc4_str, "%Y-%m-%d").date()
        st.write(f"คำนวณครั้งล่าสุด: {format_thai_date_admin(last_calc_acc4)}")
    except ValueError:
        st.error(f"รูปแบบวันที่ 'LastCalc_Acc4' ใน SystemConfig ไม่ถูกต้อง ({last_calc_acc4_str}), กรุณาใช้ YYYY-MM-DD")
        # ใช้ค่าเริ่มต้น date(1900, 1, 1)
else:
    st.warning("ไม่พบข้อมูล 'LastCalc_Acc4' ใน SystemConfig, สมมติว่าเป็นการคำนวณครั้งแรก")
    # ใช้ค่าเริ่มต้น date(1900, 1, 1)

due_date_acc4 = date(today.year, 7, 5) # (เดือน 7, วันที่ 5)

if today >= due_date_acc4 and last_calc_acc4 < due_date_acc4:
    st.warning("ตรวจพบว่าถึงรอบคำนวณดอกเบี้ย บัญชี 4 (5 ก.ค.)")
    if st.button("ดำเนินการคำนวณดอกเบี้ย บช. 4 (6%)", type="primary"):
        with st.spinner("กำลังคำนวณและอัปเดตดอกเบี้ยให้สมาชิกทุกคน..."):
            if gsheet_utils.batch_calculate_interest(_sh, ["4"]):
                gsheet_utils.update_system_config(_sh, "LastCalc_Acc4", today.strftime("%Y-%m-%d"))
                st.success("คำนวณดอกเบี้ย บัญชี 4 เรียบร้อย!")
                st.rerun()
            # (ถ้า batch_calculate_interest ไม่สำเร็จ จะมี st.error แสดงจากในฟังก์ชันเอง)
else:
    st.success("บัญชี 4: ยังไม่ถึงรอบคำนวณ หรือ คำนวณสำหรับปีนี้ไปแล้ว")

st.markdown("---")

# --- ส่วนที่ 2: คำนวณดอกเบี้ย บัญชี 1 และ 2 (แก้ไข Error Handling) ---
st.subheader("2. คำนวณดอกเบี้ย (รอบ 5 พ.ย. - บัญชี 1, 2)")

last_calc_acc1_2_str = gsheet_utils.get_system_config(_sh, "LastCalc_Acc1_2")
last_calc_acc1_2 = date(1900, 1, 1) # ตั้งค่าเริ่มต้น

if last_calc_acc1_2_str:
    try:
        last_calc_acc1_2 = datetime.strptime(last_calc_acc1_2_str, "%Y-%m-%d").date()
        st.write(f"คำนวณครั้งล่าสุด: {format_thai_date_admin(last_calc_acc1_2)}")
    except ValueError:
        st.error(f"รูปแบบวันที่ 'LastCalc_Acc1_2' ใน SystemConfig ไม่ถูกต้อง ({last_calc_acc1_2_str}), กรุณาใช้ YYYY-MM-DD")
        # ใช้ค่าเริ่มต้น date(1900, 1, 1)
else:
    st.warning("ไม่พบข้อมูล 'LastCalc_Acc1_2' ใน SystemConfig, สมมติว่าเป็นการคำนวณครั้งแรก")
    # ใช้ค่าเริ่มต้น date(1900, 1, 1)

due_date_acc1_2 = date(today.year, 10, 5) # (เดือน 11, วันที่ 5) - คุณสามารถแก้เป็น 10 เพื่อทดสอบ

if today >= due_date_acc1_2 and last_calc_acc1_2 < due_date_acc1_2:
    st.warning("ตรวจพบว่าถึงรอบคำนวณดอกเบี้ย บัญชี 1 และ 2 (5 พ.ย.)")
    if st.button("ดำเนินการคำนวณดอกเบี้ย บช. 1 และ 2 (6%)", type="primary"):
        with st.spinner("กำลังคำนวณและอัปเดตดอกเบี้ยให้สมาชิกทุกคน..."):
            if gsheet_utils.batch_calculate_interest(_sh, ["1", "2"]):
                gsheet_utils.update_system_config(_sh, "LastCalc_Acc1_2", today.strftime("%Y-%m-%d"))
                st.success("คำนวณดอกเบี้ย บัญชี 1 และ 2 เรียบร้อย!")
                st.rerun()
            # (ถ้า batch_calculate_interest ไม่สำเร็จ จะมี st.error แสดงจากในฟังก์ชันเอง)
else:
    st.success("บัญชี 1, 2: ยังไม่ถึงรอบคำนวณ หรือ คำนวณสำหรับปีนี้ไปแล้ว")
