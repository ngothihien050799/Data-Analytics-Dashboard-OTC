import pandas as pd
import sys

file_path = r"c:\ADMIN\Code CPC1HN\TestAI-OTC\Data-Analytics-Dashboard-OTC\04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
xl = pd.ExcelFile(file_path, engine='openpyxl')
df_call = pd.read_excel(xl, '2_Call')
df_order = pd.read_excel(xl, '3_DonHang')

with open("scratch/explore_output.txt", "w", encoding="utf-8") as f:
    f.write("2_Call info:\n")
    f.write(f"Total rows: {len(df_call)}\n")
    f.write(f"Non-null KHCN (GUID): {df_call['KHCN'].notna().sum()}\n")
    f.write(f"Non-null KHCN.1 (Names): {df_call['KHCN.1'].notna().sum()}\n\n")

    f.write("Sample df_call with KHCN:\n")
    f.write(df_call[df_call['KHCN'].notna()][['MNV', 'Mã KH', 'Tên KH', 'KHCN', 'KHCN.1', 'Ghi chú']].head(5).to_string())
    f.write("\n\n")

    f.write("Sample df_order with Mã KHCN:\n")
    f.write(df_order[df_order['Mã KHCN'].notna()][['MNV', 'Mã KH', 'Tên KH', 'Mã KHCN', 'Mã ĐH']].head(5).to_string())
    f.write("\n\n")

    for col in df_call.columns:
        if df_call[col].dtype == object and df_call[col].nunique() < 20:
            f.write(f"Unique values in 2_Call['{col}']: {df_call[col].unique().tolist()[:10]}\n")

    for col in df_order.columns:
        if df_order[col].dtype == object and df_order[col].nunique() < 20:
            f.write(f"Unique values in 3_DonHang['{col}']: {df_order[col].unique().tolist()[:10]}\n")

print("Written to scratch/explore_output.txt")
