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
            df_call = pd.read_excel(xl, '2_Call', dtype={'MNV': str, 'Mã KH': str, 'KHCN': str})
            df_order = pd.read_excel(xl, '3_DonHang', dtype={'MNV': str, 'Mã KH': str, 'Mã KHCN': str})
            df_sp = None
            if '4_SanPham' in xl.sheet_names:
                df_sp = pd.read_excel(xl, '4_SanPham', dtype=str)
        
        def clean_id(x):
            if pd.isna(x): return ""
            s = str(x).strip()
            if s.endswith('.0'): s = s[:-2]
            return s

        def get_base_order_id(val):
            s = clean_id(val)
            if '.' in s:
                parts = s.split('.')
                if parts[-1].isdigit():
                    return ".".join(parts[:-1])
            return s

        def safe_text(x):
            if pd.isna(x): return ""
            return str(x).strip()

        def safe_int_value(x):
            if pd.isna(x): return 0
            try:
                return int(float(x))
            except:
                return 0

        def safe_float_value(x):
            if pd.isna(x): return 0.0
            try:
                return float(x)
            except:
                return 0.0

        def format_dt(val, fmt='%d/%m/%Y %H:%M'):
            if pd.isna(val) or not isinstance(val, (datetime, pd.Timestamp)):
                return ""
            return val.strftime(fmt)

        for col in ['MNV', 'Mã KH', 'KHCN', 'Mã KHCN']:
            if col in df_nv.columns: df_nv[col] = df_nv[col].apply(clean_id)
            if col in df_call.columns: df_call[col] = df_call[col].apply(clean_id)
            if col in df_order.columns: df_order[col] = df_order[col].apply(clean_id)
            
        if df_sp is not None and 'Mã sản phẩm' in df_sp.columns:
            df_sp['Mã sản phẩm'] = df_sp['Mã sản phẩm'].apply(clean_id)
            
        if 'Mã ĐH' in df_order.columns:
            df_order['Mã ĐH'] = df_order['Mã ĐH'].apply(get_base_order_id)
            
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
            
        df_call['Duration_ph'] = df_call.apply(get_duration, axis=1)
        df_call['Is_Bad_Note'] = df_call['Ghi chú'].apply(is_bad_note)
        df_call['Out_Of_Hours'] = df_call['Thời gian checkin'].apply(
            lambda x: 1 if pd.notna(x) and (x.hour < 7 or x.hour >= 18) else 0
        )
        df_call['Under_5m'] = df_call['Duration_ph'].apply(lambda x: 1 if x < 5 and x > 0 else 0)
        
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
                off_calls = nv_calls[nv_calls['Out_Of_Hours'] == 1].sort_values(by='Thời gian checkin', ascending=False)
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
                
            call_details = []
            nv_calls_sorted = nv_calls.sort_values(by='Thời gian checkin', ascending=False)
            for local_idx, (_, c_row) in enumerate(nv_calls_sorted.iterrows(), start=1):
                checkin = c_row.get('Thời gian checkin')
                checkout = c_row.get('Thời gian checkout')
                
                status = 'Hợp lệ'
                if safe_int_value(c_row.get('Out_Of_Hours')) == 1:
                    status = 'Ngoài giờ'
                elif safe_int_value(c_row.get('Under_5m')) == 1:
                    status = 'Dưới 5 phút'
                elif safe_int_value(c_row.get('Is_Bad_Note')) == 1:
                    status = 'Cần bổ sung note'
                
                ma_kh = safe_text(c_row.get('Mã KH'))
                ten_kh = safe_text(c_row.get('Tên KH'))
                khcn_name = safe_text(c_row.get('KHCN.1'))
                note = safe_text(c_row.get('Ghi chú'))
                task = safe_text(c_row.get('Nhiệm vụ')) or 'CSKH theo cung tuyến'
                
                call_details.append({
                    "stt": safe_int_value(c_row.get('STT')) or local_idx,
                    "id": safe_text(c_row.get('ID')) or f"call_{local_idx}",
                    "status": status,
                    "checkin_time": format_dt(checkin, '%H:%M:%S'),
                    "checkin_date": format_dt(checkin, '%d/%m/%Y'),
                    "checkout_time": format_dt(checkout, '%H:%M:%S'),
                    "duration": float(round(safe_float_value(c_row.get('Duration_ph')), 1)),
                    "task": task,
                    "ma_kh": ma_kh,
                    "ten_kh": ten_kh,
                    "khcn": khcn_name,
                    "content": note or 'Giới thiệu sản phẩm',
                    "note": note
                })

            order_details = []
            nv_orders_sorted = nv_orders.sort_values(by='Ngày đặt', ascending=False)
            for local_idx, (_, o_row) in enumerate(nv_orders_sorted.iterrows(), start=1):
                revenue = safe_float_value(o_row.get('Doanh Thu'))
                order_details.append({
                    "stt": safe_int_value(o_row.get('STT')) or local_idx,
                    "order_id": safe_text(o_row.get('Mã ĐH')),
                    "order_time": format_dt(o_row.get('Ngày đặt'), '%H:%M:%S'),
                    "order_date": format_dt(o_row.get('Ngày đặt'), '%d/%m/%Y'),
                    "ma_kh": safe_text(o_row.get('Mã KH')),
                    "ten_kh": safe_text(o_row.get('Tên KH')),
                    "receiver": safe_text(o_row.get('Người nhận')),
                    "phone": safe_text(o_row.get('Liên hệ')),
                    "channel": safe_text(o_row.get('Kênh bán')),
                    "product_code": safe_text(o_row.get('Mã sản phẩm')),
                    "product_name": safe_text(o_row.get('Tên sản phẩm')),
                    "unit": safe_text(o_row.get('ĐVT')),
                    "qty": safe_int_value(o_row.get('Số lượng')),
                    "unit_price": safe_float_value(o_row.get('Đơn giá')),
                    "revenue": float(round(revenue / 1000000, 2))
                })

            product_details = []
            nv_orders_valid = nv_orders[
                nv_orders['Mã sản phẩm'].notna() &
                (nv_orders['Mã sản phẩm'].astype(str).str.strip() != "")
            ]
            if not nv_orders_valid.empty:
                for ma_sp, p_df in nv_orders_valid.groupby('Mã sản phẩm'):
                    product_details.append({
                        "ma": safe_text(ma_sp),
                        "ten": safe_text(p_df['Tên sản phẩm'].iloc[0]) if 'Tên sản phẩm' in p_df.columns else safe_text(ma_sp),
                        "qty": safe_int_value(p_df['Số lượng'].sum()),
                        "orders": safe_int_value(p_df['Mã ĐH'].nunique()) if 'Mã ĐH' in p_df.columns else len(p_df),
                        "customers": safe_int_value(p_df['Mã KH'].nunique()) if 'Mã KH' in p_df.columns else 0,
                        "rev": float(round(p_df['Doanh Thu'].sum() / 1000000, 2))
                    })
                product_details = sorted(product_details, key=lambda x: x['rev'], reverse=True)

            customer_map = {}
            for _, c_row in nv_calls.iterrows():
                ma_kh = safe_text(c_row.get('Mã KH')) or safe_text(c_row.get('KHCN'))
                if not ma_kh:
                    continue
                if ma_kh not in customer_map:
                    customer_map[ma_kh] = {
                        "ma_kh": ma_kh,
                        "ten_kh": safe_text(c_row.get('Tên KH')),
                        "khcn": safe_text(c_row.get('KHCN.1')),
                        "visits": 0,
                        "orders": 0,
                        "revenue": 0.0,
                        "last_call": "",
                        "last_order": "",
                        "_order_ids": set()
                    }
                rec = customer_map[ma_kh]
                rec["visits"] += 1
                call_time = c_row.get('Thời gian checkin')
                if pd.notna(call_time):
                    last_call = datetime.strptime(rec["last_call"], '%d/%m/%Y %H:%M') if rec["last_call"] else None
                    if last_call is None or call_time > last_call:
                        rec["last_call"] = format_dt(call_time, '%d/%m/%Y %H:%M')

            for _, o_row in nv_orders.iterrows():
                ma_kh = safe_text(o_row.get('Mã KH')) or safe_text(o_row.get('Mã KHCN'))
                if not ma_kh:
                    continue
                if ma_kh not in customer_map:
                    customer_map[ma_kh] = {
                        "ma_kh": ma_kh,
                        "ten_kh": safe_text(o_row.get('Tên KH')),
                        "khcn": "",
                        "visits": 0,
                        "orders": 0,
                        "revenue": 0.0,
                        "last_call": "",
                        "last_order": "",
                        "_order_ids": set()
                    }
                rec = customer_map[ma_kh]
                if not rec["ten_kh"]:
                    rec["ten_kh"] = safe_text(o_row.get('Tên KH'))
                order_id = safe_text(o_row.get('Mã ĐH'))
                if order_id:
                    rec["_order_ids"].add(order_id)
                rec["revenue"] += safe_float_value(o_row.get('Doanh Thu')) / 1000000
                order_time = o_row.get('Ngày đặt')
                if pd.notna(order_time):
                    last_order = datetime.strptime(rec["last_order"], '%d/%m/%Y %H:%M') if rec["last_order"] else None
                    if last_order is None or order_time > last_order:
                        rec["last_order"] = format_dt(order_time, '%d/%m/%Y %H:%M')

            customer_details = []
            for rec in customer_map.values():
                order_ids = rec.pop("_order_ids")
                rec["orders"] = len(order_ids)
                rec["revenue"] = float(round(rec["revenue"], 2))
                customer_details.append(rec)
            customer_details = sorted(customer_details, key=lambda x: (x["revenue"], x["visits"]), reverse=True)

            focus_product_details = []
            if df_sp is not None:
                emp_ck = ""
                nhom_str = str(nhom).upper()
                for ck in ['CK1', 'CK2', 'CK3']:
                    if ck in nhom_str:
                        emp_ck = ck
                        break
                
                if emp_ck:
                    df_sp_filtered = df_sp[df_sp['CK'].astype(str).str.strip().str.upper() == emp_ck]
                else:
                    df_sp_filtered = df_sp
                
                for _, sp_row in df_sp_filtered.iterrows():
                    ma_sp = sp_row['Mã sản phẩm']
                    ten_sp = sp_row['Tên sản phẩm']
                    sp_ck = sp_row.get('CK', '')
                    
                    p_orders = nv_orders[nv_orders['Mã sản phẩm'] == ma_sp]
                    
                    qty = safe_int_value(p_orders['Số lượng'].sum())
                    orders = safe_int_value(p_orders['Mã ĐH'].nunique()) if 'Mã ĐH' in p_orders.columns else len(p_orders)
                    customers = safe_int_value(p_orders['Mã KH'].nunique()) if 'Mã KH' in p_orders.columns else 0
                    rev = float(round(p_orders['Doanh Thu'].sum() / 1000000, 2))
                    
                    focus_product_details.append({
                        "ma": str(ma_sp),
                        "ten": str(ten_sp) if pd.notna(ten_sp) else str(ma_sp),
                        "ck": str(sp_ck) if pd.notna(sp_ck) else "",
                        "qty": qty,
                        "orders": orders,
                        "customers": customers,
                        "rev": rev
                    })

            member = {
                "mnv": str(mnv),
                "ten": str(ten_nv),
                "profile": {
                    "phone": safe_text(row_nv.get('SĐT')),
                    "position": safe_text(row_nv.get('Vị trí')),
                    "department": safe_text(row_nv.get('Phòng ban')),
                    "branch": safe_text(row_nv.get('Chi nhánh')),
                    "group": safe_text(nhom)
                },
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
                "monthly": [int(x) for x in monthly_arr],
                "weekly": [int(x) for x in weekly_arr],
                "weekly_rev": [float(x) for x in weekly_rev_arr],
                "call_details": call_details,
                "order_details": order_details,
                "product_details": product_details,
                "customer_details": customer_details,
                "focus_product_details": focus_product_details
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
                nv_prod_sorted = sorted(nv_prod_list, key=lambda x: x['rev'], reverse=True)
                nv_top5[str(mnv)] = nv_prod_sorted
                
            # 4. Map Employee codes to names (nv_info)
            nv_info = {}
            for m in g_data["members"]:
                nv_info[str(m["mnv"])] = str(m["ten"])
                
            # 5. Calculate Conversion Metrics (Khai phá -> Đơn hàng)
            g_calls = df_call[df_call['MNV'].isin(group_mnvs)]
            g_orders = df_order[df_order['MNV'].isin(group_mnvs)]
            
            # Ensure columns exist
            if 'KHCN' not in g_calls.columns:
                g_calls = g_calls.copy()
                g_calls['KHCN'] = ""
            if 'Mã KHCN' not in g_orders.columns:
                g_orders = g_orders.copy()
                g_orders['Mã KHCN'] = ""
                
            g_calls_exploration = g_calls[g_calls['Tên KH'] == 'Khách hàng khai phá']
            
            g_calls_clean = g_calls[
                g_calls['Mã KH'].notna() & 
                (g_calls['Mã KH'].astype(str).str.strip() != "") &
                (g_calls['Mã KH'].astype(str).str.strip().str.len() < 8) &
                (g_calls['Tên KH'] == 'Khách hàng khai phá')
            ]
            called_ma_khs = set(g_calls_clean['Mã KH'].astype(str).str.strip().unique())
            
            g_orders_clean = g_orders[g_orders['Mã KH'].notna() & (g_orders['Mã KH'].astype(str).str.strip() != "")]
            ordered_ma_khs = set(g_orders_clean['Mã KH'].astype(str).str.strip().unique())
            
            converted_ma_khs = called_ma_khs.intersection(ordered_ma_khs)
            
            total_calls_khcn = len(called_ma_khs)
            total_checks_khcn = len(g_calls_exploration)
            converted_khcn_count = len(converted_ma_khs)
            
            g_exploration_rate = (total_calls_khcn / total_checks_khcn * 100) if total_checks_khcn > 0 else 0
            g_conv_rate = (converted_khcn_count / total_calls_khcn * 100) if total_calls_khcn > 0 else 0
            g_total_rate = (converted_khcn_count / total_checks_khcn * 100) if total_checks_khcn > 0 else 0
            
            g_conv_orders = g_orders_clean[g_orders_clean['Mã KH'].isin(converted_ma_khs)]
            g_conv_rev = g_conv_orders['Doanh Thu'].sum() / 1000000
            
            member_conversions = []
            for member_info in g_data["members"]:
                m_mnv = member_info["mnv"]
                m_ten = member_info["ten"]
                
                m_calls_clean = g_calls_clean[g_calls_clean['MNV'] == m_mnv]
                m_called_ma_khs = set(m_calls_clean['Mã KH'].astype(str).str.strip().unique())
                
                m_orders_clean = g_orders_clean[g_orders_clean['MNV'] == m_mnv]
                m_ordered_ma_khs = set(m_orders_clean['Mã KH'].astype(str).str.strip().unique())
                
                m_converted_ma_khs = m_called_ma_khs.intersection(m_ordered_ma_khs)
                m_called_count = len(m_called_ma_khs)
                m_checks_count = len(g_calls_exploration[g_calls_exploration['MNV'] == m_mnv])
                m_converted_count = len(m_converted_ma_khs)
                
                m_exploration_rate = (m_called_count / m_checks_count * 100) if m_checks_count > 0 else 0
                m_conv_rate = (m_converted_count / m_called_count * 100) if m_called_count > 0 else 0
                m_total_rate = (m_converted_count / m_checks_count * 100) if m_checks_count > 0 else 0
                
                m_conv_orders = m_orders_clean[m_orders_clean['Mã KH'].isin(m_converted_ma_khs)]
                m_conv_rev = m_conv_orders['Doanh Thu'].sum() / 1000000
                
                member_conversions.append({
                    "mnv": str(m_mnv),
                    "ten": str(m_ten),
                    "called_count": int(m_called_count),
                    "checks_count": int(m_checks_count),
                    "exploration_rate": float(round(m_exploration_rate, 1)),
                    "converted_count": int(m_converted_count),
                    "conversion_rate": float(round(m_conv_rate, 1)),
                    "total_rate": float(round(m_total_rate, 1)),
                    "revenue": float(round(m_conv_rev, 2))
                })
            
            conversion_details = []
            guid_info = {}
            for _, row_c in g_calls_clean.iterrows():
                ma_kh = str(row_c['Mã KH']).strip()
                if ma_kh not in guid_info:
                    guid_info[ma_kh] = {
                        "khcn_name": str(row_c.get('KHCN.1', '')).strip() if pd.notna(row_c.get('KHCN.1')) else "",
                        "ma_kh": ma_kh,
                        "ten_kh": str(row_c.get('KHCN.1', '')).strip() if pd.notna(row_c.get('KHCN.1')) else "",
                        "latest_call_time": row_c['Thời gian checkin']
                    }
                else:
                    if pd.notna(row_c['Thời gian checkin']) and (pd.isna(guid_info[ma_kh]["latest_call_time"]) or row_c['Thời gian checkin'] < guid_info[ma_kh]["latest_call_time"]):
                        guid_info[ma_kh]["latest_call_time"] = row_c['Thời gian checkin']
                        
            for ma_kh in converted_ma_khs:
                info = guid_info.get(ma_kh, {"khcn_name": "", "ma_kh": ma_kh, "ten_kh": "", "latest_call_time": pd.NaT})
                cust_orders = g_orders_clean[g_orders_clean['Mã KH'] == ma_kh]
                cust_mnvs = cust_orders['MNV'].unique()
                cust_nv_names = [nv_info.get(str(m), str(m)) for m in cust_mnvs]
                
                latest_order_time = cust_orders['Ngày đặt'].min()  # Use min to get the oldest order date
                total_rev = cust_orders['Doanh Thu'].sum() / 1000000
                base_order_ids = cust_orders['Mã ĐH'].dropna().unique().tolist()
                
                # Fetch Tên KH from 3_DonHang (sheet of orders) as requested
                ten_kh_dh = ""
                if not cust_orders.empty:
                    valid_ten_khs = cust_orders['Tên KH'].dropna().tolist()
                    if valid_ten_khs:
                        ten_kh_dh = str(valid_ten_khs[0]).strip()
                
                conversion_details.append({
                    "khcn_guid": ma_kh,
                    "khcn_name": info["khcn_name"],
                    "ma_kh": ma_kh,
                    "ten_kh": ten_kh_dh if ten_kh_dh else info["ten_kh"],
                    "nv_names": ", ".join(cust_nv_names),
                    "latest_call_time": info["latest_call_time"].strftime('%d/%m/%Y %H:%M') if pd.notna(info["latest_call_time"]) else "—",
                    "latest_order_time": latest_order_time.strftime('%d/%m/%Y %H:%M') if pd.notna(latest_order_time) else "—",
                    "base_order_ids": base_order_ids,
                    "revenue": float(round(total_rev, 2))
                })
                
            conversion_details = sorted(conversion_details, key=lambda x: x['revenue'], reverse=True)
            
            conversion_module = {
                "total_calls_khcn": int(total_calls_khcn),
                "total_checks_khcn": int(total_checks_khcn),
                "exploration_rate": float(round(g_exploration_rate, 1)),
                "converted_khcn_count": int(converted_khcn_count),
                "conversion_rate": float(round(g_conv_rate, 1)),
                "total_rate": float(round(g_total_rate, 1)),
                "revenue": float(round(g_conv_rev, 2)),
                "member_conversions": member_conversions,
                "conversion_details": conversion_details
            }
                
            # Inject stats into the group structure
            g_data["products"] = products_list
            g_data["kenh"] = kenh_list
            g_data["nv_top5"] = nv_top5
            g_data["nv_info"] = nv_info
            g_data["conversion_module"] = conversion_module

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
                
        # Calculate dynamic date range from check-in data
        valid_checkins = df_call['Thời gian checkin'].dropna()
        if not valid_checkins.empty:
            min_date = valid_checkins.min()
            max_date = valid_checkins.max()
            min_month = min_date.month
            max_month = max_date.month
            year = max_date.year
            date_range = f"T{min_month}–T{max_month}/{year}"
        else:
            date_range = ""
        
        raw_result = {
            "groups": list(groups_dict.values()),
            "date_range": date_range,
            "Status": "Success"
        }
        
        return clean_dict(raw_result)
        
    except Exception as e:
        return {"Status": "Error", "Message": str(e), "Traceback": traceback.format_exc()}
