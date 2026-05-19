import pandas as pd
import numpy as np

file_path = r"c:\ADMIN\Code CPC1HN\TestAI-OTC\Data-Analytics-Dashboard-OTC\04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
xl = pd.ExcelFile(file_path, engine='openpyxl')
df_nv = pd.read_excel(xl, '1_NhanVien', dtype=str)
df_call = pd.read_excel(xl, '2_Call', dtype={'MNV': str, 'Mã KH': str})
df_order = pd.read_excel(xl, '3_DonHang', dtype={'MNV': str, 'Mã KH': str})

# Clean IDs
def clean_id(x):
    if pd.isna(x): return ""
    s = str(x).strip()
    if s.endswith('.0'): s = s[:-2]
    return s

for col in ['MNV', 'Mã KH']:
    if col in df_nv.columns: df_nv[col] = df_nv[col].apply(clean_id)
    if col in df_call.columns: df_call[col] = df_call[col].apply(clean_id)
    if col in df_order.columns: df_order[col] = df_order[col].apply(clean_id)

def get_base_order_id(val):
    s = clean_id(val)
    if '.' in s:
        parts = s.split('.')
        if parts[-1].isdigit():
            return ".".join(parts[:-1])
    return s

if 'Mã ĐH' in df_order.columns:
    df_order['Mã ĐH'] = df_order['Mã ĐH'].apply(get_base_order_id)

df_call['Thời gian checkin'] = pd.to_datetime(df_call['Thời gian checkin'], errors='coerce')
df_order['Ngày đặt'] = pd.to_datetime(df_order['Ngày đặt'], errors='coerce')

df_order['Số lượng'] = pd.to_numeric(df_order['Số lượng'], errors='coerce').fillna(0)
df_order['Đơn giá'] = pd.to_numeric(df_order['Đơn giá'], errors='coerce').fillna(0)
df_order['Doanh Thu'] = df_order['Số lượng'] * df_order['Đơn giá']

# Group definitions: let's match hanh_vi.py groups
groups_dict = {}
for _, row in df_nv.iterrows():
    mnv = row['MNV']
    ten = row['Tên']
    nhom = row.get('Nhóm', 'Chưa phân nhóm')
    if nhom not in groups_dict:
        groups_dict[nhom] = {
            "group_name": nhom,
            "members": []
        }
    groups_dict[nhom]["members"].append({"mnv": mnv, "ten": ten})

print("Groups and member counts:")
for nhom, g_data in groups_dict.items():
    print(f"Group: {nhom}, members: {len(g_data['members'])}")

# Let's test conversion logic for one group
for nhom, g_data in groups_dict.items():
    group_mnvs = [m["mnv"] for m in g_data["members"]]
    g_calls = df_call[df_call['MNV'].isin(group_mnvs)]
    g_orders = df_order[df_order['MNV'].isin(group_mnvs)]
    
    # Unique KHCN GUIDs in calls
    # Let's drop empty/na values
    called_guids = set(g_calls['KHCN'].dropna().unique())
    # Unique Mã KHCN in orders
    ordered_guids = set(g_orders['Mã KHCN'].dropna().unique())
    
    intersection = called_guids.intersection(ordered_guids)
    
    print(f"\nGroup: {nhom}")
    print(f"  Called KHCN count (unique): {len(called_guids)}")
    print(f"  Ordered KHCN count (unique): {len(ordered_guids)}")
    print(f"  Intersection count: {len(intersection)}")
    if len(called_guids) > 0:
        print(f"  Conversion rate: {len(intersection)/len(called_guids)*100:.2f}%")
        
    # Let's see some converted detail examples
    converted_orders = g_orders[g_orders['Mã KHCN'].isin(intersection)]
    print(f"  Total revenue from converted orders: {converted_orders['Doanh Thu'].sum():,.0f} VND")
