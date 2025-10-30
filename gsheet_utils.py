# gsheet_utils.py
import gspread
import pandas as pd
import streamlit as st
from gspread.exceptions import WorksheetNotFound, SpreadsheetNotFound

# --- ค่าคงที่ ---
SHEET_NAME = "MyLoanAppDB"

# --- ฟังก์ชัน Helper ---
def safe_float(value):
    return float(value) if value not in [None, ''] else 0.0

# --- การเชื่อมต่อ ---
@st.cache_resource
def connect_to_sheet():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open(SHEET_NAME)
        return sh
    except SpreadsheetNotFound:
        st.error(f"ไม่พบ Google Sheet ชื่อ: '{SHEET_NAME}' กรุณาตรวจสอบการตั้งค่า")
        st.stop()
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ Google Sheet (ตรวจสอบ Secrets): {e}")
        st.stop()

# --- ฟังก์ชันเคลียร์ Cache ---
def clear_all_caches():
    get_data_as_dataframe.clear()
    get_address_suggestions.clear()
    get_member_by_id.clear()
    get_active_loans_by_member.clear()

# --- ฟังก์ชันดึงข้อมูล ---
@st.cache_data(ttl=60)
def get_data_as_dataframe(worksheet_name: str, _sh: gspread.Spreadsheet):
    try:
        worksheet = _sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except WorksheetNotFound:
        st.error(f"ไม่พบแท็บ (Worksheet) ชื่อ: '{worksheet_name}'")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล ({worksheet_name}): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_address_suggestions(_sh: gspread.Spreadsheet):
    df = get_data_as_dataframe("Members", _sh)
    if df.empty: return {k: [] for k in ["villages", "sub_districts", "districts", "provinces"]}
    return {
        "villages": sorted(df["Village"].dropna().unique().tolist()),
        "sub_districts": sorted(df["SubDistrict"].dropna().unique().tolist()),
        "districts": sorted(df["District"].dropna().unique().tolist()),
        "provinces": sorted(df["Province"].dropna().unique().tolist())
    }

@st.cache_data(ttl=5)
def get_member_by_id(_sh: gspread.Spreadsheet, member_id: str):
    df = get_data_as_dataframe("Members", _sh)
    if not df.empty:
        member_data = df[df['MemberID'] == member_id]
        if not member_data.empty:
            return member_data.to_dict('records')[0]
    return None

@st.cache_data(ttl=30)
def get_active_loans_by_member(_sh: gspread.Spreadsheet, member_id: str):
    df = get_data_as_dataframe("Loans", _sh)
    if not df.empty:
        df['PrincipalAmount'] = pd.to_numeric(df['PrincipalAmount'], errors='coerce').fillna(0)
        df['AmountPaid'] = pd.to_numeric(df['AmountPaid'], errors='coerce').fillna(0)
        
        member_loans = df[
            (df['MemberID'] == member_id) &
            (df['Status'].isin(['ยังค้างชำระ', 'เกินกำหนดชำระ', 'Active'])) # <-- เพิ่ม Active (กันพลาด)
        ].copy()
        
        if not member_loans.empty:
            member_loans['Remaining'] = member_loans['PrincipalAmount'] - member_loans['AmountPaid']
            member_loans = member_loans[member_loans['Remaining'] > 0]
            
        return member_loans
    return pd.DataFrame()


# --- ฟังก์ชันแก้ไข/เพิ่ม/ลบ ข้อมูล ---
def add_row_to_sheet(worksheet_name: str, _sh: gspread.Spreadsheet, data_list: list):
    try:
        worksheet = _sh.worksheet(worksheet_name)
        worksheet.append_row(data_list)
        clear_all_caches()
        return True
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล ({worksheet_name}): {e}")
        return False

def update_member_data(worksheet_name: str, _sh: gspread.Spreadsheet, item_id: str, id_column: str, updates_dict: dict):
    try:
        worksheet = _sh.worksheet(worksheet_name)
        id_col_index = worksheet.find(id_column, in_column=1).col
        cell = worksheet.find(item_id, in_column=id_col_index)
        row_to_update = cell.row
        
        cells_to_update = []
        header_row = worksheet.row_values(1)
        
        for column_name, new_value in updates_dict.items():
            try:
                col_to_update = header_row.index(column_name) + 1
                cells_to_update.append(gspread.Cell(row_to_update, col_to_update, new_value))
            except ValueError:
                st.warning(f"ไม่พบคอลัมน์ '{column_name}' ใน Google Sheet '{worksheet_name}'")
        
        if cells_to_update:
            worksheet.update_cells(cells_to_update)
            
        clear_all_caches()
        return True
    except (gspread.CellNotFound, AttributeError):
        st.error(f"ไม่พบ ID '{item_id}' ที่จะอัปเดตใน '{worksheet_name}'")
        return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอัปเดตข้อมูล ({worksheet_name}): {e}")
        return False

def delete_row_by_id(worksheet_name: str, _sh: gspread.Spreadsheet, item_id: str, id_column: str):
    try:
        worksheet = _sh.worksheet(worksheet_name)
        id_col_index = worksheet.find(id_column, in_column=1).col
        cell = worksheet.find(item_id, in_column=id_col_index)
        worksheet.delete_rows(cell.row)
        clear_all_caches()
        return True
    except (gspread.CellNotFound, AttributeError):
        st.error(f"ไม่พบ ID '{item_id}' ที่จะลบใน '{worksheet_name}'")
        return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการลบข้อมูล ({worksheet_name}): {e}")
        return False

# --- ฟังก์ชันสำหรับเงินกู้ (Loans) ---
def add_loan_contract(_sh: gspread.Spreadsheet, loan_data_list: list):
    return add_row_to_sheet("Loans", _sh, loan_data_list)

def update_loan_payment(_sh: gspread.Spreadsheet, loan_id: str, principal_paid_increment: float, interest_paid_increment: float):
    try:
        worksheet = _sh.worksheet("Loans")
        header_row = worksheet.row_values(1)
        loan_id_col = header_row.index("LoanID") + 1
        cells = worksheet.findall(loan_id, in_column=loan_id_col)
        if not cells: raise gspread.CellNotFound
        
        row_index = cells[0].row 
        amount_paid_col = header_row.index("AmountPaid") + 1
        interest_paid_col = header_row.index("InterestPaid") + 1
        current_amount_paid = safe_float(worksheet.cell(row_index, amount_paid_col).value)
        current_interest_paid = safe_float(worksheet.cell(row_index, interest_paid_col).value)
        new_amount_paid = current_amount_paid + principal_paid_increment
        new_interest_paid = current_interest_paid + interest_paid_increment
        cells_to_update = [
            gspread.Cell(row_index, amount_paid_col, new_amount_paid),
            gspread.Cell(row_index, interest_paid_col, new_interest_paid)
        ]
        worksheet.update_cells(cells_to_update)
        clear_all_caches()
        return True
    except (gspread.CellNotFound, AttributeError):
        st.error(f"ไม่พบ LoanID '{loan_id}' ที่จะอัปเดตการชำระเงิน")
        return False
    except ValueError:
         st.error(f"ไม่พบคอลัมน์ที่จำเป็น ('LoanID', 'AmountPaid', 'InterestPaid') ในแท็บ Loans")
         return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอัปเดตการชำระเงินกู้: {e}")
        return False
            
def update_loan_status(_sh: gspread.Spreadsheet, loan_id: str, new_status: str):
    """
    อัปเดต Status ของสัญญาที่ระบุ (อัปเดตทุกแถวที่ตรงกัน)
    *** นี่คือเวอร์ชันแก้ไขที่ "ดุ" ขึ้น ***
    """
    try:
        # 1. เพิ่มข้อความดีบัก
        st.write(f"--- ⚙️ gsheet_utils: กำลังอัปเดต ID: {loan_id} เป็น '{new_status}' ---")
        
        worksheet = _sh.worksheet("Loans")
        header_row = worksheet.row_values(1)
            
        loan_id_col = header_row.index("LoanID") + 1
        status_col = header_row.index("Status") + 1
            
        cells_to_update = worksheet.findall(loan_id, in_column=loan_id_col)
        if not cells_to_update:
             st.warning(f"ไม่พบ LoanID '{loan_id}' ในคอลัมน์ {loan_id_col}")
             raise gspread.CellNotFound
        
        st.write(f"พบ {len(cells_to_update)} แถวที่ตรงกันสำหรับ {loan_id}...")
        
        # 2. แก้ไข: เปลี่ยนจาก batch เป็น single update ทีละเซลล์
        for cell in cells_to_update:
            worksheet.update_cell(cell.row, status_col, new_status)
            st.write(f"อัปเดตแถว {cell.row} สำเร็จ")
        # 3. สิ้นสุดการแก้ไข

        clear_all_caches()
        st.write(f"--- ⚙️ เคลียร์ Cache และเสร็จสิ้น {loan_id} ---")
        return True
    except (gspread.CellNotFound, AttributeError):
        st.error(f"ไม่พบ LoanID '{loan_id}' ที่จะอัปเดตสถานะ")
        return False
    except ValueError:
         st.error(f"ไม่พบคอลัมน์ที่จำเป็น ('LoanID', 'Status') ในแท็บ Loans")
         return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอัปเดตสถานะเงินกู้: {e}")
        return False

# --- ฟังก์ชันสำหรับแอดมิน ---
def get_system_config(_sh: gspread.Spreadsheet, key: str):
    try:
        worksheet = _sh.worksheet("SystemConfig")
        cell = worksheet.find(key, in_column=1)
        value = worksheet.cell(cell.row, 2).value
        return value
    except WorksheetNotFound:
        st.error(f"ไม่พบแท็บ SystemConfig")
        return None
    except (gspread.CellNotFound, AttributeError):
        st.warning(f"ไม่พบค่า Config '{key}' ใน SystemConfig")
        return None
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงค่า Config '{key}': {e}")
        return None

def update_system_config(_sh: gspread.Spreadsheet, key: str, value: str):
    try:
        worksheet = _sh.worksheet("SystemConfig")
        cell = worksheet.find(key, in_column=1)
        worksheet.update_cell(cell.row, 2, value)
        return True
    except (gspread.CellNotFound, AttributeError):
        st.error(f"ไม่พบ Config '{key}' ที่จะอัปเดตใน SystemConfig")
        return False
    except Exception as e:
        st.error(f"อัปเดต Config '{key}' ไม่สำเร็จ: {e}")
        return False
