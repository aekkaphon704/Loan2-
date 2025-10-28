# pages/3_⚙️_เครื่องมือแอดมิน.py
import streamlit as st
import gsheet_utils
from datetime import datetime, date
from babel.dates import format_date

def format_thai_date(dt):
    if dt is None: return "ไม่ได้ระบุ"
    return format_date(dt, format='d MMMM yyyy', locale='th_TH')

st.set_page_config(page_title="เครื่องมือแอดมิน", page_icon="⚙️", layout="centered")
st.title("⚙️ เครื่องมือสำหรับผู้ดูแลระบบ")

_sh = gsheet_utils.connect_to_sheet()

today = date.today()
st.info(f"วันนี้วันที่: **{format_thai_date(today)}**")

st.markdown("---")

# --- ส่วนที่ 1: คำนวณดอกเบี้ย บัญชี 4 ---
st.subheader("1. คำนวณดอกเบี้ย (รอบ 5 ก.ค. - บัญชี 4)")

# ดึงข้อมูลว่าคำนวณครั้งล่าสุดเมื่อไหร่
last_calc_acc4_str = gsheet_utils.get_system_config(_sh, "LastCalc_Acc4")
last_calc_acc4 = datetime.strptime(last_calc_acc4_str, "%Y-%m-%d").date()

st.write(f"คำนวณครั้งล่าสุด: {format_thai_date(last_calc_acc4)}")

# กำหนดวันครบกำหนดของปีนี้
due_date_acc4 = date(today.year, 7, 5)

# ตรวจสอบว่า "วันนี้" เลย "วันครบกำหนด" หรือยัง
# และ "การคำนวณครั้งล่าสุด" ต้อง "ก่อนหน้า" วันครบกำหนดของปีนี้ (กันการกดซ้ำ)
if today >= due_date_acc4 and last_calc_acc4 < due_date_acc4:
    st.warning("ตรวจพบว่าถึงรอบคำนวณดอกเบี้ย บัญชี 4 (5 ก.ค.)")
    if st.button("ดำเนินการคำนวณดอกเบี้ย บช. 4 (6%)", type="primary"):
        with st.spinner("กำลังคำนวณและอัปเดตดอกเบี้ยให้สมาชิกทุกคน..."):
            # สั่งคำนวณ
            gsheet_utils.batch_calculate_interest(_sh, ["4"])
            # อัปเดตวันที่คำนวณล่าสุดเป็น "วันนี้"
            gsheet_utils.update_system_config(_sh, "LastCalc_Acc4", today.strftime("%Y-%m-%d"))
        st.success("คำนวณดอกเบี้ย บัญชี 4 เรียบร้อย!")
        st.rerun()
else:
    st.success("บัญชี 4: ยังไม่ถึงรอบคำนวณ หรือ คำนวณสำหรับปีนี้ไปแล้ว")

st.markdown("---")

# --- ส่วนที่ 2: คำนวณดอกเบี้ย บัญชี 1 และ 2 ---
st.subheader("2. คำนวณดอกเบี้ย (รอบ 5 พ.ย. - บัญชี 1, 2)")

last_calc_acc1_2_str = gsheet_utils.get_system_config(_sh, "LastCalc_Acc1_2")
last_calc_acc1_2 = datetime.strptime(last_calc_acc1_2_str, "%Y-%m-%d").date()

st.write(f"คำนวณครั้งล่าสุด: {format_thai_date(last_calc_acc1_2)}")

due_date_acc1_2 = date(today.year, 11, 5)

if today >= due_date_acc1_2 and last_calc_acc1_2 < due_date_acc1_2:
    st.warning("ตรวจพบว่าถึงรอบคำนวณดอกเบี้ย บัญชี 1 และ 2 (5 พ.ย.)")
    if st.button("ดำเนินการคำนวณดอกเบี้ย บช. 1 และ 2 (6%)", type="primary"):
        with st.spinner("กำลังคำนวณและอัปเดตดอกเบี้ยให้สมาชิกทุกคน..."):
            gsheet_utils.batch_calculate_interest(_sh, ["1", "2"])
            gsheet_utils.update_system_config(_sh, "LastCalc_Acc1_2", today.strftime("%Y-%m-%d"))
        st.success("คำนวณดอกเบี้ย บัญชี 1 และ 2 เรียบร้อย!")
        st.rerun()
else:
    st.success("บัญชี 1, 2: ยังไม่ถึงรอบคำนวณ หรือ คำนวณสำหรับปีนี้ไปแล้ว")