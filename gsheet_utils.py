# gsheet_utils.py
import gspread
import pandas as pd
import streamlit as st  # <-- 1. เพิ่มบรรทัดนี้

# --- ค่าคงที่ (เราไม่ต้องการ KEY_FILE_PATH อีกต่อไป) ---
SHEET_NAME = "MyLoanAppDB" # <-- 2. แก้ไขเป็นชื่อ Google Sheet ของคุณ (ถ้าจำเป็น)

# --- การเชื่อมต่อ (ใช้ cache ของ Streamlit เพื่อเชื่อมต่อครั้งเดียว) ---
@st.cache_resource
def connect_to_sheet():
    """
    เชื่อมต่อกับ Google Sheet โดยใช้ Service Account จาก st.secrets
    """
    try:
        # 3. แก้ไขส่วนนี้ทั้งหมด
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open(SHEET_NAME)
        return sh
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ Google Sheet (ตรวจสอบ Secrets): {e}")
        st.stop()

@st.cache_data(ttl=60) # ดึงข้อมูลใหม่ทุก 60 วินาที
def get_data_as_dataframe(worksheet_name: str, _sh: gspread.Spreadsheet):
    """
    ดึงข้อมูลจากแท็บที่ระบุมาเป็น DataFrame
    """
    try:
        worksheet = _sh.worksheet(worksheet_name)
        data = worksheet.get_all_records() # ดึงข้อมูลทั้งหมดมาเป็น dict
        return pd.DataFrame(data)
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"ไม่พบแท็บ (Worksheet) ชื่อ: '{worksheet_name}'")
        return pd.DataFrame() # คืนค่า DataFrame ว่างเปล่า
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return pd.DataFrame()

def add_row_to_sheet(worksheet_name: str, _sh: gspread.Spreadsheet, data_list: list):
    """
    เพิ่มข้อมูล 1 แถว (list) ลงในแท็บที่ระบุ
    """
    try:
        worksheet = _sh.worksheet(worksheet_name)
        worksheet.append_row(data_list)
        
        # ล้าง cache ของข้อมูลเพื่อให้ตารางอัปเดตทันที
        get_data_as_dataframe.clear() 
        return True
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
        return False
def update_cell_by_id(worksheet_name: str, _sh: gspread.Spreadsheet, item_id: str, id_column: str, target_column: str, new_value):
    """
    อัปเดตค่าในช่อง (cell) โดยการค้นหาจาก ID
    """
    try:
        worksheet = _sh.worksheet(worksheet_name)
        # หาว่าคอลัมน์ ID อยู่คอลัมน์ที่เท่าไหร่ (เช่น A=1, B=2)
        cell = worksheet.find(item_id, in_column=worksheet.find(id_column).col)
        # อัปเดตค่าในแถวเดียวกัน แต่คนละคอลัมน์
        worksheet.update_cell(cell.row, worksheet.find(target_column).col, new_value)
        
        get_data_as_dataframe.clear() # ล้าง cache
        return True
    except (gspread.exceptions.CellNotFound, AttributeError):
        st.error(f"ไม่พบ ID '{item_id}' ในคอลัมน์ '{id_column}'")
        return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอัปเดตข้อมูล: {e}")
        return False

def get_member_by_id(_sh: gspread.Spreadsheet, member_id: str):
    """
    ดึงข้อมูลสมาชิก 1 คนจาก MemberID
    """
    df = get_data_as_dataframe("Members", _sh)
    if not df.empty:
        member_data = df[df['MemberID'] == member_id]
        if not member_data.empty:
            return member_data.to_dict('records')[0] # คืนค่าเป็น dict
    return None
def delete_row_by_id(worksheet_name: str, _sh: gspread.Spreadsheet, item_id: str, id_column: str):
    """
    ลบแถวข้อมูลโดยการค้นหาจาก ID
    """
    try:
        worksheet = _sh.worksheet(worksheet_name)
        # 1. ค้นหา ID ว่าอยู่คอลัมน์ไหน (เช่น คอลัมน์ที่ 1)
        id_col_index = worksheet.find(id_column).col
        # 2. ค้นหาค่า ID (เช่น "M-176...") ในคอลัมน์นั้น
        cell = worksheet.find(item_id, in_column=id_col_index)
        # 3. สั่งลบแถวที่พบ
        worksheet.delete_rows(cell.row)
        
        get_data_as_dataframe.clear() # ล้าง cache
        return True
    except (gspread.exceptions.CellNotFound, AttributeError):
        st.error(f"ไม่พบ ID '{item_id}' ที่จะลบ")
        return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการลบข้อมูล: {e}")
        return False

def update_member_data(worksheet_name: str, _sh: gspread.Spreadsheet, item_id: str, id_column: str, updates_dict: dict):
    """
    อัปเดตหลายๆ ช่องในแถวเดียวกัน โดยค้นหาจาก ID
    updates_dict คือ {'ชื่อคอลัมน์': 'ค่าใหม่', 'อีกคอลัมน์': 'ค่าใหม่'}
    """
    try:
        worksheet = _sh.worksheet(worksheet_name)
        # 1. ค้นหา ID ว่าอยู่คอลัมน์ไหน (เช่น คอลัมน์ที่ 1)
        id_col_index = worksheet.find(id_column).col
        # 2. ค้นหาค่า ID (เช่น "M-176...") ในคอลัมน์นั้น เพื่อหา "แถว"
        cell = worksheet.find(item_id, in_column=id_col_index)
        row_to_update = cell.row
        
        cells_to_update = []
        for column_name, new_value in updates_dict.items():
            # 3. ค้นหาว่า "ชื่อคอลัมน์" (เช่น 'Name') อยู่ "คอลัมน์" ที่เท่าไหร่
            col_to_update = worksheet.find(column_name).col
            # 4. เตรียมรายการอัปเดต
            cells_to_update.append(gspread.Cell(row_to_update, col_to_update, new_value))
        
        # 5. สั่งอัปเดตทั้งหมดในครั้งเดียว (เร็วกว่า)
        if cells_to_update:
            worksheet.update_cells(cells_to_update)
            
        get_data_as_dataframe.clear() # ล้าง cache
        return True
    except (gspread.exceptions.CellNotFound, AttributeError):
        st.error(f"ไม่พบ ID '{item_id}' ที่จะอัปเดต")
        return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอัปเดตข้อมูล: {e}")
        return False
def get_system_config(_sh: gspread.Spreadsheet, key: str):
    """
    ดึงค่าการตั้งค่าจากแท็บ SystemConfig
    """
    try:
        worksheet = _sh.worksheet("SystemConfig")
        cell = worksheet.find(key, in_column=1) # ค้นหา key ในคอลัมน์ A
        value = worksheet.cell(cell.row, 2).value # ดึงค่าจากคอลัมน์ B
        return value
    except Exception as e:
        st.error(f"ไม่พบค่า Config: {key}")
        return None

def update_system_config(_sh: gspread.Spreadsheet, key: str, value: str):
    """
    อัปเดตค่าการตั้งค่าในแท็บ SystemConfig
    """
    try:
        worksheet = _sh.worksheet("SystemConfig")
        cell = worksheet.find(key, in_column=1) # ค้นหา key ในคอลัมน์ A
        worksheet.update_cell(cell.row, 2, value) # อัปเดตค่าในคอลัมน์ B
        return True
    except Exception as e:
        st.error(f"อัปเดต Config ไม่สำเร็จ: {key}")
        return False

def batch_calculate_interest(_sh: gspread.Spreadsheet, account_nums: list):
    """
    คำนวณดอกเบี้ย 6% ให้สมาชิกทุกคนสำหรับบัญชีที่ระบุ (แบบ Batch)
    """
    try:
        worksheet = _sh.worksheet("Members")
        all_data = worksheet.get_all_records() # ดึงข้อมูลทั้งหมด
        
        updated_cells = [] # เตรียมรายการอัปเดต
        
        for i, row in enumerate(all_data):
            current_row_index = i + 2 # +2 เพราะแถวแรกคือ header และ gspread เริ่มที่ 1
            
            for num in account_nums:
                balance_col_name = f"Loan{num}_Balance"
                interest_col_name = f"Loan{num}_InterestDue"
                
                # 1. คำนวณดอกเบี้ยใหม่ (6%)
                new_interest = (row[balance_col_name] * 0.06)
                
                # 2. เอามารวมกับดอกเบี้ยเก่าที่ค้างอยู่
                total_interest_due = row[interest_col_name] + new_interest
                
                # 3. ค้นหาว่าคอลัมน์ InterestDue อยู่ตรงไหน
                interest_col_index = worksheet.find(interest_col_name).col
                
                # 4. เพิ่มเข้าคิวอัปเดต
                updated_cells.append(gspread.Cell(current_row_index, interest_col_index, total_interest_due))

        # 5. สั่งอัปเดตทั้งหมดในครั้งเดียว!
        if updated_cells:
            worksheet.update_cells(updated_cells)
            
        get_data_as_dataframe.clear() # ล้าง cache
        return True
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการคำนวณดอกเบี้ย: {e}")
        return False