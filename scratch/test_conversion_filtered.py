import pandas as pd

file_path = r"c:\ADMIN\Code CPC1HN\TestAI-OTC\Data-Analytics-Dashboard-OTC\04-2026 - Danh sách data tổng hợp khách hàng trọng tâm nhóm.xlsx"
xl = pd.ExcelFile(file_path, engine='openpyxl')
df_nv = pd.read_excel(xl, '1_NhanVien', dtype=str)
df_call = pd.read_excel(xl, '2_Call', dtype={'MNV': str, 'Mã KH': str, 'KHCN': str})
df_order = pd.read_excel(xl, '3_DonHang', dtype={'MNV': str, 'Mã KH': str, 'Mã KHCN': str})

# Clean IDs
def clean_id(x):
    if pd.isna(x): return ""
    s = str(x).strip()
    if s.endswith('.0'): s = s[:-2]
    return s

for col in ['MNV', 'Mã KH', 'KHCN', 'Mã KHCN']:
    if col in df_call.columns: df_call[col] = df_call[col].apply(clean_id)
    if col in df_order.columns: df_order[col] = df_order[col].apply(clean_id)

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

for nhom, g_data in groups_dict.items():
    group_mnvs = [m["mnv"] for m in g_data["members"]]
    g_calls = df_call[df_call['MNV'].isin(group_mnvs)]
    g_orders = df_order[df_order['MNV'].isin(group_mnvs)]
    
    # Filter calls where Tên KH is "Khách hàng khai phá"
    g_calls_filtered = g_calls[g_calls['Tên KH'] == 'Khách hàng khai phá']
    
    called_guids = set(g_calls_filtered['KHCN'].dropna().unique())
    called_guids = {x for x in called_guids if x != ""}
    
    ordered_guids = set(g_orders['Mã KHCN'].dropna().unique())
    ordered_guids = {x for x in ordered_guids if x != ""}
    
    intersection = called_guids.intersection(ordered_guids)
    
    print(f"\nGroup: {nhom}")
    print(f"  Called 'Khách hàng khai phá' GUIDs (unique): {len(called_guids)}")
    print(f"  Ordered KHCN GUIDs (unique): {len(ordered_guids)}")
    print(f"  Intersection count: {len(intersection)}")
    if len(called_guids) > 0:
        print(f"  Conversion rate: {len(intersection)/len(called_guids)*100:.2f}%")
