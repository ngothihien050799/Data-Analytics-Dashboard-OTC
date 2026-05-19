import pandas as pd
import os
import json

file_path = r"c:\ADMIN\Code CPC1HN\TestAI-OTC\Data-Analytics-Dashboard-OTC\04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
if os.path.exists(file_path):
    xl = pd.ExcelFile(file_path, engine='openpyxl')
    
    df_call = pd.read_excel(xl, '2_Call', nrows=10)
    df_order = pd.read_excel(xl, '3_DonHang', nrows=10)
    
    res = {
        "sheets": xl.sheet_names,
        "2_Call_columns": df_call.columns.tolist(),
        "3_DonHang_columns": df_order.columns.tolist(),
        "2_Call_sample": df_call.fillna("").to_dict(orient='records'),
        "3_DonHang_sample": df_order.fillna("").to_dict(orient='records')
    }
    
    with open("scratch/excel_info.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("Done")
else:
    print("File not found")
