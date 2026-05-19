import pandas as pd

file_path = r"c:\ADMIN\Code CPC1HN\TestAI-OTC\Data-Analytics-Dashboard-OTC\04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
xl = pd.ExcelFile(file_path, engine='openpyxl')
df_order = pd.read_excel(xl, '3_DonHang')

# Find orders containing dots
dot_orders = df_order[df_order['Mã ĐH'].astype(str).str.contains(r'\.')]['Mã ĐH'].unique()
print("Orders with dots:")
print(list(dot_orders)[:10])
