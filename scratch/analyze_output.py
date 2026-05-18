import pandas as pd
import json

file_path = "bao_cao_hanh_vi_ban_hang_04_2026.xlsx"
try:
    xls = pd.ExcelFile(file_path)
    output_schema = {}
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Get columns and first 2 rows of data to understand the structure
        output_schema[sheet_name] = {
            "columns": list(df.columns),
            "sample_data": df.head(2).fillna("").to_dict(orient="records")
        }
        
    with open("scratch/output_schema.json", "w", encoding="utf-8") as f:
        json.dump(output_schema, f, ensure_ascii=False, indent=2)
    print("Success")
except Exception as e:
    print(e)
