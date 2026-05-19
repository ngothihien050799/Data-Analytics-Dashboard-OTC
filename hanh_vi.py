import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback

def process_hanh_vi_data(file_path):
    try:
        try:
            xl = pd.ExcelFile(file_path, engine='openpyxl')
        except:
            xl = pd.ExcelFile(file_path, engine='xlrd')
        
        with xl:
            df_nv = pd.read_excel(xl, '1_NhanVien', dtype=str)
            df_call = pd.read_excel(xl, '2_Call', dtype={'MNV': str, 'Mã KH': str})
            df_order = pd.read_excel(xl, '3_DonHang', dtype={'MNV': str, 'Mã KH': str})
        
        def clean_id(x):
            if pd.isna(x): return ""
            s = str(x).strip()
            if s.endswith('.0'): s = s[:-2]
            return s

        for col in ['MNV', 'Mã KH']:
            if col in df_nv.columns: df_nv[col] = df_nv[col].apply(clean_id)
            if col in df_call.columns: df_call[col] = df_call[col].apply(clean_id)
            if col in df_order.columns: df_order[col] = df_order[col].apply(clean_id)
            
        if 'Mã ĐH' in df_order.columns:
            # Chuẩn hóa và cắt lấy đúng 14 ký tự đầu tiên để gom nhóm đơn hàng trùng nhau
            df_order['Mã ĐH'] = df_order['Mã ĐH'].apply(clean_id).str[:14]
            
        df_call['Thời gian checkin'] = pd.to_datetime(df_call['Thời gian checkin'], errors='coerce')
        df_call['Thời gian checkout'] = pd.to_datetime(df_call['Thời gian checkout'], errors='coerce')
        df_order['Ngày đặt'] = pd.to_datetime(df_order['Ngày đặt'], errors='coerce')
        
        df_order['Số lượng'] = pd.to_numeric(df_order['Số lượng'], errors='coerce').fillna(0)
        df_order['Đơn giá'] = pd.to_numeric(df_order['Đơn giá'], errors='coerce').fillna(0)
        df_order['Doanh Thu'] = df_order['Số lượng'] * df_order['Đơn giá']
        
        def is_bad_note(note):
            if pd.isna(note): 
                return True
            note_str = str(note).strip()
            if not note_str:
                return True
            
            # 1. Tách các từ dựa trên khoảng trắng
            words = [w for w in note_str.split() if w.strip()]
            
            # Quá ngắn dưới 5 từ -> Kém chất lượng
            if len(words) < 5:
                return True
                
            # Loại bỏ khoảng trắng để phân tích chuỗi ký tự
            char_str = "".join(words)
            
            # 2. Hoặc chỉ gồm các chữ số
            alnum_chars = [c.lower() for c in char_str if c.isalnum()]
            if alnum_chars:
                if all(c.isdigit() for c in alnum_chars):
                    return True
            else:
                # 3. Hoặc chỉ gồm các ký tự đặc biệt (không có chữ cái hay chữ số nào)
                return True
                
            # 4. Hoặc chỉ gồm các chữ cái lặp lại hoặc vô nghĩa (ví dụ: các chữ cái giống nhau hoàn toàn)
            letters = [c for c in alnum_chars if c.isalpha()]
            if letters and len(set(letters)) <= 1:
                return True
                
            # Nếu tất cả các từ trong note đều trùng nhau (ví dụ: "xong xong xong xong xong")
            if len(set([w.lower() for w in words])) <= 1:
                return True
                
            # Nếu tất cả các từ đều chỉ dài 1 ký tự (chuỗi các chữ cái vô nghĩa, ví dụ: "a b c d e")
            if all(len(w) <= 1 for w in words):
                return True
                
            return False

        def get_duration(row):
            if pd.isna(row['Thời gian checkin']) or pd.isna(row['Thời gian checkout']):
                return 0
            diff = (row['Thời gian checkout'] - row['Thời gian checkin']).total_seconds()
            return max(0, diff / 60)
            
        def check_gps_same(row):
            lat_in = row.get('Tọa độ checkin lat')
            lng_in = row.get('Tọa độ checkin lng')
            lat_out = row.get('Tọa độ checkout lat')
            lng_out = row.get('Tọa độ checkout lng')
            if pd.notna(lat_in) and pd.notna(lng_in) and pd.notna(lat_out) and pd.notna(lng_out):
                try:
                    return 1 if (float(lat_in) == float(lat_out) and float(lng_in) == float(lng_out)) else 0
                except:
                    return 0
            return 0
            
        df_call['Duration_ph'] = df_call.apply(get_duration, axis=1)
        df_call['Is_Bad_Note'] = df_call['Ghi chú'].apply(is_bad_note)
        df_call['Out_Of_Hours'] = df_call['Thời gian checkin'].apply(
            lambda x: 1 if pd.notna(x) and (x.hour < 7 or x.hour >= 18) else 0
        )
        df_call['Under_5m'] = df_call['Duration_ph'].apply(lambda x: 1 if x < 5 and x > 0 else 0)
        df_call['GPS_Same'] = df_call.apply(check_gps_same, axis=1)
        
        df_call['Tháng'] = df_call['Thời gian checkin'].dt.month
        months_available = sorted([int(m) for m in df_call['Tháng'].dropna().unique() if m >= 1 and m <= 12])
        if not months_available:
            months_available = [1, 2, 3, 4] # fallback

        # Tính tuần ISO cho 8 tuần gần nhất
        df_order['Tuần ISO'] = df_order['Ngày đặt'].dt.isocalendar().week
        # Get up to 8 latest weeks
        weeks_available = sorted([int(w) for w in df_order['Tuần ISO'].dropna().unique()])[-8:]
        
        # Build week labels dynamically based on max/min dates per week in data
        week_labels = []
        for w in weeks_available:
            w_orders = df_order[df_order['Tuần ISO'] == w]
            if not w_orders.empty:
                min_d = w_orders['Ngày đặt'].min().strftime('%d/%m')
                max_d = w_orders['Ngày đặt'].max().strftime('%d/%m')
                week_labels.append(f"T{w}\n{min_d}–{max_d}")
            else:
                week_labels.append(f"T{w}")

        groups_dict = {}
        
        # Iterate NV
        for idx, row_nv in df_nv.iterrows():
            nhom = row_nv.get('Nhóm', 'Chưa phân nhóm')
            if pd.isna(nhom): nhom = 'Chưa phân nhóm'
            
            if nhom not in groups_dict:
                groups_dict[nhom] = {
                    "id": f"g_{len(groups_dict)}",
                    "name": str(nhom),
                    "members": [],
                    "weeks": week_labels
                }
                
            mnv = row_nv.get('MNV')
            ten_nv = row_nv.get('Tên', '')
            tuoi_nghe = row_nv.get('Tuổi nghề', 0)
            
            nv_calls = df_call[df_call['MNV'] == mnv]
            nv_orders = df_order[df_order['MNV'] == mnv]
            
            so_visit = len(nv_calls)
            doanh_thu = nv_orders['Doanh Thu'].sum()
            doanh_thu_m = doanh_thu / 1000000
            
            so_don = nv_orders['Mã ĐH'].nunique() if 'Mã ĐH' in nv_orders.columns else len(nv_orders)
            kh_tham = nv_calls['Mã KH'].nunique()
            kh_mua = nv_orders['Mã KH'].nunique()
            
            conv_pct = (kh_mua / kh_tham * 100) if kh_tham > 0 else 0
            avg_duration = nv_calls['Duration_ph'].mean() if so_visit > 0 else 0
            
            bad_notes_cnt = nv_calls['Is_Bad_Note'].sum()
            note_xau_pct = (bad_notes_cnt / so_visit * 100) if so_visit > 0 else 0
            
            check_ngoai_gio = nv_calls['Out_Of_Hours'].sum()
            off_hours_list = []
            if check_ngoai_gio > 0:
                off_calls = nv_calls[nv_calls['Out_Of_Hours'] == 1].sort_values(by='Thời gian checkin')
                for _, c_row in off_calls.iterrows():
                    dt_ci = c_row['Thời gian checkin']
                    dt_co = c_row['Thời gian checkout']
                    
                    ma_kh = str(c_row.get('Mã KH', '')) if pd.notna(c_row.get('Mã KH')) else ''
                    ten_kh = str(c_row.get('Tên KH', '')) if pd.notna(c_row.get('Tên KH')) else ''
                    khcn = str(c_row.get('KHCN.1', '')) if pd.notna(c_row.get('KHCN.1')) else ''
                    
                    ci_str = dt_ci.strftime('%d/%m %H:%M') if pd.notna(dt_ci) else ''
                    co_str = dt_co.strftime('%d/%m %H:%M') if pd.notna(dt_co) else ''
                    
                    off_hours_list.append({
                        "ma_kh": ma_kh,
                        "ten_kh": ten_kh,
                        "khcn": khcn,
                        "checkin": ci_str,
                        "checkout": co_str
                    })

            visit_duoi_5p = nv_calls['Under_5m'].sum()
            gps_same = nv_calls['GPS_Same'].sum()
            
            # Monthly visits
            monthly_arr = []
            for m in months_available:
                m_cnt = len(nv_calls[nv_calls['Tháng'] == m])
                monthly_arr.append(m_cnt)
                
            # Weekly orders and revenue
            weekly_arr = []
            weekly_rev_arr = []
            for w in weeks_available:
                w_orders = nv_orders[nv_orders['Tuần ISO'] == w]
                w_cnt = w_orders['Mã ĐH'].nunique() if 'Mã ĐH' in w_orders.columns else len(w_orders)
                weekly_arr.append(w_cnt)
                
                w_rev = w_orders['Doanh Thu'].sum() / 1000000
                weekly_rev_arr.append(float(round(w_rev, 2)))
                
            member = {
                "mnv": str(mnv),
                "ten": str(ten_nv),
                "tuoi_nghe": int(tuoi_nghe) if pd.notna(tuoi_nghe) else 0,
                "visits": int(so_visit),
                "rev": float(round(doanh_thu_m, 1)),
                "orders": int(so_don),
                "kh_visit": int(kh_tham),
                "kh_buy": int(kh_mua),
                "conv": float(round(conv_pct, 1)),
                "avg_dur": float(round(avg_duration, 1)) if not pd.isna(avg_duration) else 0,
                "note_bad_pct": float(round(note_xau_pct, 1)),
                "off_hours": int(check_ngoai_gio),
                "off_hours_list": off_hours_list,
                "short_visits": int(visit_duoi_5p),
                "gps_same": int(gps_same),
                "monthly": [int(x) for x in monthly_arr],
                "weekly": [int(x) for x in weekly_arr],
                "weekly_rev": [float(x) for x in weekly_rev_arr]
            }
            groups_dict[nhom]["members"].append(member)

        # Iterate through all groups and calculate product stats dynamically
        for nhom, g_data in groups_dict.items():
            group_mnvs = [m["mnv"] for m in g_data["members"]]
            # Filter orders belonging to this group
            group_orders = df_order[df_order['MNV'].isin(group_mnvs)]
            
            # Filter out empty or missing product codes
            group_orders_valid = group_orders[
                group_orders['Mã sản phẩm'].notna() & 
                (group_orders['Mã sản phẩm'].astype(str).str.strip() != "")
            ].copy()
            
            # 1. Calculate Group Products List
            products_list = []
            if not group_orders_valid.empty:
                prod_grouped = group_orders_valid.groupby('Mã sản phẩm')
                for ma, p_df in prod_grouped:
                    ten = p_df['Tên sản phẩm'].iloc[0] if 'Tên sản phẩm' in p_df.columns and not p_df['Tên sản phẩm'].empty else str(ma)
                    if pd.isna(ten) or not str(ten).strip():
                        ten = str(ma)
                    
                    rev = p_df['Doanh Thu'].sum() / 1000000
                    qty = p_df['Số lượng'].sum()
                    
                    diem_ban = p_df['Mã KH'].nunique() if 'Mã KH' in p_df.columns else 0
                    nv_count = p_df['MNV'].nunique() if 'MNV' in p_df.columns else 0
                    
                    # Monthly trend for this product
                    monthly = []
                    for m in months_available:
                        m_orders = p_df[p_df['Ngày đặt'].notna() & (p_df['Ngày đặt'].dt.month == m)]
                        m_rev = m_orders['Doanh Thu'].sum() / 1000000
                        monthly.append(float(round(m_rev, 1)))
                        
                    products_list.append({
                        "ma": str(ma),
                        "ten": str(ten),
                        "rev": float(round(rev, 1)),
                        "qty": int(qty),
                        "diem_ban": int(diem_ban),
                        "nv_count": int(nv_count),
                        "monthly": monthly
                    })
                # Sort by revenue descending
                products_list = sorted(products_list, key=lambda x: x['rev'], reverse=True)
            
            # 2. Calculate Channels Breakdown
            kenh_list = []
            if not group_orders.empty:
                total_group_rev = group_orders['Doanh Thu'].sum() / 1000000
                if total_group_rev > 0:
                    channel_grouped = group_orders.groupby('Kênh bán')
                    for channel_name, c_df in channel_grouped:
                        c_rev = c_df['Doanh Thu'].sum() / 1000000
                        c_qty = c_df['Số lượng'].sum()
                        c_pct = (c_rev / total_group_rev * 100)
                        
                        kenh_list.append({
                            "kenh": str(channel_name) if pd.notna(channel_name) else "Khác",
                            "rev": float(round(c_rev, 1)),
                            "qty": int(c_qty),
                            "pct": float(round(c_pct, 1))
                        })
                    # Sort by revenue descending
                    kenh_list = sorted(kenh_list, key=lambda x: x['rev'], reverse=True)
                
            # 3. Calculate Top 5 Products per Employee (nv_top5)
            nv_top5 = {}
            for mnv in group_mnvs:
                nv_orders = group_orders_valid[group_orders_valid['MNV'] == mnv]
                if nv_orders.empty:
                    nv_top5[str(mnv)] = []
                    continue
                    
                nv_prod_grouped = nv_orders.groupby('Mã sản phẩm')
                nv_prod_list = []
                for ma, p_df in nv_prod_grouped:
                    ten = p_df['Tên sản phẩm'].iloc[0] if 'Tên sản phẩm' in p_df.columns and not p_df['Tên sản phẩm'].empty else str(ma)
                    if pd.isna(ten) or not str(ten).strip():
                        ten = str(ma)
                    rev = p_df['Doanh Thu'].sum() / 1000000
                    qty = p_df['Số lượng'].sum()
                    
                    nv_prod_list.append({
                        "ma": str(ma),
                        "ten": str(ten),
                        "rev": float(round(rev, 1)),
                        "qty": int(qty)
                    })
                nv_prod_sorted = sorted(nv_prod_list, key=lambda x: x['rev'], reverse=True)[:5]
                nv_top5[str(mnv)] = nv_prod_sorted
                
            # 4. Map Employee codes to names (nv_info)
            nv_info = {}
            for m in g_data["members"]:
                nv_info[str(m["mnv"])] = str(m["ten"])
                
            # Inject stats into the group structure
            g_data["products"] = products_list
            g_data["kenh"] = kenh_list
            g_data["nv_top5"] = nv_top5
            g_data["nv_info"] = nv_info

        # Trả về kết quả
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(v) for v in d]
            elif pd.isna(d):
                return None
            elif hasattr(d, 'item') and callable(getattr(d, 'item')):
                return d.item()
            else:
                return d
                
        raw_result = {
            "groups": list(groups_dict.values()),
            "Status": "Success"
        }
        
        return clean_dict(raw_result)
        
    except Exception as e:
        return {"Status": "Error", "Message": str(e), "Traceback": traceback.format_exc()}
