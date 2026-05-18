import pandas as pd
from docx import Document
import json

def get_excel_info(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        info = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, nrows=0)
            info[sheet_name] = list(df.columns)
        return info
    except Exception as e:
        return str(e)

def get_docx_text(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        return str(e)

input_file = "04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
output_file = "bao_cao_hanh_vi_ban_hang_04_2026.xlsx"
docx_file = "Mô tả phân tích nhóm kinh doanh.docx"

result = {
    "input_excel": get_excel_info(input_file),
    "output_excel": get_excel_info(output_file),
    "docx_text": get_docx_text(docx_file)
}

with open("scratch_analysis.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Analysis saved to scratch_analysis.json")
