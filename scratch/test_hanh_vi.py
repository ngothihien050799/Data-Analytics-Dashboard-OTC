import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hanh_vi import process_hanh_vi_data
import json

file_path = "bao_cao_hanh_vi_ban_hang_04_2026.xlsx"
print(f"Testing process_hanh_vi_data with {file_path}...")
try:
    result = process_hanh_vi_data(file_path)
    if result.get("Status") == "Error":
        print("Error returned from function:")
        print(result.get("Message"))
        print(result.get("Traceback"))
    else:
        print("Success! Result status is:", result.get("Status"))
        print(f"Number of groups: {len(result.get('groups', []))}")
        # Print a small sample of the result structure
        if result.get('groups'):
            g = result['groups'][0]
            print(f"Group name: {g.get('name')}")
            print(f"Members count: {len(g.get('members', []))}")
            if g.get('members'):
                print("First member sample keys:", list(g['members'][0].keys()))
except Exception as e:
    import traceback
    print("Raised Exception:")
    traceback.print_exc()
