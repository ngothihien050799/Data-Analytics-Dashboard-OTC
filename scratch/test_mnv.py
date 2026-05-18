import pandas as pd
import math

file_path = "04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
xl = pd.ExcelFile(file_path, engine='openpyxl')
df_nv = pd.read_excel(xl, '1_NhanVien')
df_call = pd.read_excel(xl, '2_Call')

print(df_nv['MNV'].head())
print(df_call['MNV'].head())
