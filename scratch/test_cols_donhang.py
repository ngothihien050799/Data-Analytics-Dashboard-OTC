import pandas as pd
file_path = "04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
xl = pd.ExcelFile(file_path, engine='openpyxl')
df = pd.read_excel(xl, '3_DonHang')
with open('cols_donhang.txt', 'w', encoding='utf-8') as f:
    f.write(str(df.columns.tolist()))
