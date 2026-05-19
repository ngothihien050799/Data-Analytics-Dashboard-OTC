import pandas as pd

file_path = r"c:\ADMIN\Code CPC1HN\TestAI-OTC\Data-Analytics-Dashboard-OTC\04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
xl = pd.ExcelFile(file_path, engine='openpyxl')
df_call = pd.read_excel(xl, '2_Call')
df_order = pd.read_excel(xl, '3_DonHang')

with open("scratch/inspect_kh_khaipha.txt", "w", encoding="utf-8") as f:
    f.write("Columns in 2_Call:\n")
    f.write(str(df_call.columns.tolist()) + "\n\n")
    
    # Check Tên KH containing Khách hàng khai phá
    if 'Tên KH' in df_call.columns:
        match_ten_kh = df_call[df_call['Tên KH'].astype(str).str.contains("Khách hàng khai phá", case=False, na=False)]
        f.write(f"Matches for 'Tên KH' containing 'Khách hàng khai phá': {len(match_ten_kh)}\n")
        if len(match_ten_kh) > 0:
            f.write("Sample rows:\n")
            f.write(match_ten_kh[['MNV', 'Mã KH', 'Tên KH', 'KHCN', 'KHCN.1']].head(5).to_string() + "\n\n")
            
    # Check KHCN.1 containing Khách hàng khai phá
    if 'KHCN.1' in df_call.columns:
        match_khcn_1 = df_call[df_call['KHCN.1'].astype(str).str.contains("Khách hàng khai phá", case=False, na=False)]
        f.write(f"Matches for 'KHCN.1' containing 'Khách hàng khai phá': {len(match_khcn_1)}\n")
        if len(match_khcn_1) > 0:
            f.write("Sample rows:\n")
            f.write(match_khcn_1[['MNV', 'Mã KH', 'Tên KH', 'KHCN', 'KHCN.1']].head(5).to_string() + "\n\n")
            
    # Let's check unique values in Tên KH of 2_Call
    f.write("Unique values in 'Tên KH' of 2_Call (first 20):\n")
    f.write(str(df_call['Tên KH'].dropna().unique().tolist()[:20]) + "\n\n")

print("Inspection completed.")
