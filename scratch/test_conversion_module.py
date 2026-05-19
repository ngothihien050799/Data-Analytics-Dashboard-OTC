import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hanh_vi import process_hanh_vi_data
import json

file_path = "04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
result = process_hanh_vi_data(file_path)

with open("scratch/test_conversion_output.txt", "w", encoding="utf-8") as f:
    if result.get("Status") == "Error":
        f.write("Error: " + str(result.get("Message")) + "\n")
        f.write(str(result.get("Traceback")) + "\n")
    else:
        f.write("Success!\n")
        for g in result.get("groups", []):
            f.write(f"\nGroup: {g.get('name')}\n")
            conv = g.get("conversion_module")
            if conv:
                f.write("Conversion Module:\n")
                f.write(f"  Total calls KHCN (exploratory targets): {conv.get('total_calls_khcn')}\n")
                f.write(f"  Total checks count (exploration calls): {conv.get('total_checks_khcn')}\n")
                f.write(f"  Exploration rate (Tỷ lệ khai phá): {conv.get('exploration_rate')}%\n")
                f.write(f"  Converted count (Đơn chốt): {conv.get('converted_khcn_count')}\n")
                f.write(f"  Conversion rate (Tỷ lệ chuyển đổi): {conv.get('conversion_rate')}%\n")
                f.write(f"  Total rate (Tỷ lệ chốt tổng): {conv.get('total_rate')}%\n")
                f.write(f"  Revenue: {conv.get('revenue')} M\n")
                f.write(f"  Number of member records: {len(conv.get('member_conversions', []))}\n")
                f.write(f"  Number of details: {len(conv.get('conversion_details', []))}\n")
                
                if conv.get('member_conversions'):
                    f.write(f"  Sample member conversion: {json.dumps(conv['member_conversions'][0], ensure_ascii=False)}\n")
                if conv.get('conversion_details'):
                    f.write(f"  Sample detail: {json.dumps(conv['conversion_details'][0], ensure_ascii=False)}\n")
            else:
                f.write("  conversion_module NOT found!\n")
print("Done")
