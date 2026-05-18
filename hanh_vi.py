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
            visit_duoi_5p = nv_calls['Under_5m'].sum()
            gps_same = nv_calls['GPS_Same'].sum()
            
            # Monthly visits
            monthly_arr = []
            for m in months_available:
                m_cnt = len(nv_calls[nv_calls['Tháng'] == m])
                monthly_arr.append(m_cnt)
                
            # Weekly orders
            weekly_arr = []
            for w in weeks_available:
                w_orders = nv_orders[nv_orders['Tuần ISO'] == w]
                w_cnt = w_orders['Mã ĐH'].nunique() if 'Mã ĐH' in w_orders.columns else len(w_orders)
                weekly_arr.append(w_cnt)
                
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
                "short_visits": int(visit_duoi_5p),
                "gps_same": int(gps_same),
                "monthly": [int(x) for x in monthly_arr],
                "weekly": [int(x) for x in weekly_arr]
            }
            groups_dict[nhom]["members"].append(member)

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
