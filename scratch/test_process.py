import pandas as pd
import io
import os
import sys

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import process_data

# Create a mock input file
def create_mock_excel(path):
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        pd.DataFrame({'MNV': ['1'], 'Tên': ['A'], 'Nhóm': ['G'], 'Phòng ban': ['P'], 'Vị trí': ['V']}).to_excel(writer, sheet_name='1_NhanVien', index=False)
        pd.DataFrame({'Mã KH': ['K1'], 'Tên KH': ['Cust 1']}).to_excel(writer, sheet_name='2_KHTrongTam', index=False)
        pd.DataFrame({'Mã KH': ['K1'], 'Ngày đặt': [pd.Timestamp.now()], 'Số lượng': [1], 'Đơn giá': [1000000]}).to_excel(writer, sheet_name='3_DonHang', index=False)
        pd.DataFrame({'Mã KH': ['K1'], 'Thời gian checkin': [pd.Timestamp.now()]}).to_excel(writer, sheet_name='4_Call', index=False)
        pd.DataFrame({'Mã KHTC': ['K1'], 'Doanh số KH': [2000000], 'Call': [2], 'F': [1]}).to_excel(writer, sheet_name='5_FrequencyF', index=False)

mock_path = 'mock_input.xlsx'
create_mock_excel(mock_path)

try:
    print("Starting process_data...")
    result_excel, df_tonghop, df_chamdiem, df_nhanvien = process_data(mock_path)
    print("Process data success!")
    print(f"Tong hop rows: {len(df_tonghop)}")
    print(f"Cham diem rows: {len(df_chamdiem)}")
    
    # Test reading the output
    content = result_excel.read()
    print(f"Result excel size: {len(content)} bytes")
except Exception as e:
    import traceback
    print("Error during process_data:")
    print(traceback.format_exc())
finally:
    if os.path.exists(mock_path):
        os.remove(mock_path)
