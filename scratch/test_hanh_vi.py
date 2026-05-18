import json
from hanh_vi import process_hanh_vi_data

file_path = "04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
result = process_hanh_vi_data(file_path)
if result.get("Status") == "Error":
    print("ERROR:")
    print(result.get("Message"))
    print(result.get("Traceback"))
else:
    print("SUCCESS!")
