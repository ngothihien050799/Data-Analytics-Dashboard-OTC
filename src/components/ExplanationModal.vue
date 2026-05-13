<script setup>
import { X, BookOpen } from "lucide-vue-next";

const props = defineProps({
  show: Boolean,
});

const emit = defineEmits(["close"]);
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content glass-card">
      <div class="modal-header">
        <h2 class="flex items-center gap-2">
          <BookOpen :size="24" class="text-indigo-400" /> Giải Thích Cách Tính
          Toán
        </h2>
        <button class="close-btn" @click="emit('close')">
          <X :size="24" />
        </button>
      </div>

      <div class="modal-body">
        <div class="section">
          <h3>1. YÊU CẦU BẢNG "7_TongHop" — TỔNG HỢP THỐNG KÊ KHÁCH HÀNG</h3>
          <div class="explain-content">
            <h4>1. MỤC ĐÍCH</h4>
            <p>
              Sheet tổng hợp toàn bộ chỉ số hoạt động của từng khách hàng trọng
              tâm trong kỳ báo cáo, phục vụ cho hệ thống chấm điểm RFM và quản
              lý ghé thăm. Mỗi dòng = 1 khách hàng.
            </p>

            <h4>2. NGUỒN DỮ LIỆU ĐẦU VÀO</h4>
            <ul>
              <li>
                <strong>2_KHTrongTam:</strong> Danh sách khách hàng trọng tâm
                (Mã KH, Tên KH)
              </li>
              <li>
                <strong>3_Đơn hàng:</strong> Lịch sử đơn hàng (ngày đặt, số
                lượng, đơn giá, mã KH)
              </li>
              <li>
                <strong>4_Call:</strong> Lịch sử ghé thăm thực địa (ngày
                checkin, mã KH)
              </li>
              <li>
                <strong>5_FrequencyF:</strong> Tần suất ghé thăm kế hoạch và
                doanh số mục tiêu theo KH
              </li>
              <li>
                <strong>Cấu hình:</strong> Các ngưỡng cấu hình để tham chiếu,
                thay đổi thì thác đổi các giá trị ở bảng khác
              </li>
            </ul>

            <h4>3. CẤU TRÚC CỘT</h4>

            <h5>Nhóm A — THÔNG TIN KH</h5>
            <ul>
              <li><strong>Mã KH:</strong> Lấy toàn bộ từ 2_KHTrongTam</li>
              <li>
                <strong>Tên khách hàng:</strong> Tra theo Mã KH từ 2_KHTrongTam
              </li>
            </ul>

            <h5>Nhóm B — LỊCH SỬ MUA HÀNG (từ 3_Đơn hàng)</h5>
            <ul>
              <li><strong>Ngày mua cuối:</strong> MAX(Ngày đặt) theo Mã KH</li>
              <li>
                <strong>Số lần mua trong 6 tháng:</strong> COUNT(ngày khác nhau
                có đơn) trong 6 tháng gần nhất
              </li>
              <li>
                <strong>Tổng doanh số 6 tháng (VNĐ):</strong> SUM(Số lượng × Đơn
                giá) trong 6 tháng gần nhất
              </li>
              <li>
                <strong>Số ngày mua gần nhất:</strong> Ngày hôm nay − Ngày mua
                cuối
              </li>
              <li>
                <strong>Số ngày mua gần thứ hai:</strong> Ngày mua 1 − Ngày mua
                2 (khoảng cách 2 lần gần nhất)
              </li>
              <li>
                <strong>Số ngày mua gần thứ ba:</strong> Ngày mua 2 − Ngày mua 3
                (khoảng cách lần 2 và 3)
              </li>
              <p class="note">
                <em
                  >Lưu ý: Dùng để tính chu kỳ mua trung bình = (G + H) / 2. Nếu
                  KH chưa đủ 2–3 lần mua thì để trống.</em
                >
              </p>
            </ul>

            <h5>Nhóm C — HOẠT ĐỘNG GHÉ THĂM (từ 4_Call)</h5>
            <ul>
              <li>
                <strong>Số lần đã gặp:</strong> COUNT(checkin) trong tháng hiện
                tại theo Mã KH
              </li>
              <li>
                <strong>Số ngày chưa gặp:</strong> Ngày hôm nay − MAX(Ngày
                checkin) theo Mã KH
              </li>
            </ul>

            <h5>Nhóm D — PHÂN LOẠI & DOANH SỐ THÁNG</h5>
            <ul>
              <li>
                <strong>Hạng KH:</strong> Phân hạng theo Tổng DS 6 tháng: VIP ≥
                18tr / GOLD 6–18tr / NORMAL 1–6tr / NEW &lt; 1tr
              </li>
              <li>
                <strong>Tổng DS tháng (VNĐ):</strong> SUM(Số lượng × Đơn giá)
                trong tháng hiện tại theo Mã KH
              </li>
            </ul>

            <h5>Nhóm E — CHỈ SỐ THIẾU HỤT (từ 5_FrequencyF)</h5>
            <ul>
              <li>
                <strong>Call thiếu:</strong> MAX(Tần suất F) − Số lần đã gặp. Âm
                = đã đủ / vượt
              </li>
              <li>
                <strong>DS thiếu (VNĐ):</strong> MAX(Doanh số KH mục tiêu) − DS
                tháng. Âm = đã vượt mục tiêu
              </li>
              <p class="note">
                <em
                  >Lưu ý: Nếu 1 KH có nhiều dòng trong 5_FrequencyF thì lấy giá
                  trị lớn nhất.</em
                >
              </p>
            </ul>

            <h5>Nhóm F — Xu hướng & Hành động</h5>
            <ul>
              <li>
                <strong>Xu hướng mua:</strong> So sánh DS tháng hiện tại với DS
                tháng trước để nhận diện xu hướng ("📈 Tăng" / "📉 Giảm" / "➡ Ổn
                định")
              </li>
              <li>
                <strong>Chu kỳ TB:</strong> = (Số ngày mua gần thứ hai + Số ngày
                mua gần thứ ba) / 2
              </li>
              <li>
                <strong>Dự báo ngày mua tiếp:</strong> = Ngày mua cuối + Chu kỳ
                TB
              </li>
              <li>
                <strong>Trạng thái hoạt động:</strong>
                "Hoạt động": Ngày mua cuối ≤ 60 ngày, "Cảnh báo": 60 &lt; Ngày
                mua cuối ≤ 120 ngày, "Ngủ đông": Ngày mua cuối &gt; 120 ngày,
                "Chưa mua": Không có đơn hàng nào
              </li>
            </ul>

            <h4>4. QUY TẮC TÍNH TOÁN CHI TIẾT</h4>
            <ul>
              <li>
                <strong>Ngày tham chiếu:</strong> Lấy ngày hôm nay. "Tháng hiện
                tại" = tháng và năm của ngày hôm nay. "6 tháng gần nhất" = từ
                ngày đầu tháng cách đây 6 tháng đến hôm nay.
              </li>
              <li>
                <strong>Tính doanh số:</strong> Doanh thu 1 dòng = Số lượng ×
                Đơn giá. Tổng DS 6T = SUM trong 6 tháng gần nhất. DS tháng = SUM
                trong tháng hiện tại.
              </li>
              <li>
                <strong>Phân hạng KH:</strong> Tham chiếu từ sheet Cấu hình.
              </li>
              <li>
                <strong>Xử lý thiếu dữ liệu:</strong> KH chưa có đơn hàng ->
                trống/0. KH chỉ có 1 lần mua -> G, H trống. KH chưa từng được
                ghé thăm -> Số lần gặp = 0, Số ngày chưa gặp = trống.
              </li>
            </ul>
          </div>
        </div>

        <div class="section mt-6">
          <h3>2. Bảng Chấm Điểm (Công thức RFM)</h3>
          <ul class="explain-list">
            <li>
              <strong>Điểm R (Recency):</strong> <br /><code
                >Max(0, 1 - (Số ngày mua gần nhất / Max_Recency))</code
              ><br />Mua càng gần đây điểm càng cao. Nếu vượt quá giới hạn
              Max_Recency thì điểm bằng 0.
            </li>
            <li>
              <strong>Điểm F (Frequency):</strong> <br /><code
                >Min(1, Số lần mua (6T) / Max_Frequency)</code
              ><br />Mua càng nhiều lần điểm càng cao, tối đa 1.0.
            </li>
            <li>
              <strong>Điểm M (Monetary):</strong> <br /><code
                >Min(1, Tổng DS 6 tháng / Max_Monetary)</code
              ><br />Doanh số càng lớn điểm càng cao, tối đa 1.0.
            </li>
            <li>
              <strong>Điểm Hạng:</strong> Được quy đổi cố định:
              <code>VIP = 1.0</code>, <code>GOLD = 0.8</code>,
              <code>NORMAL = 0.6</code>, <code>NEW = 0.4</code>.
            </li>
            <li>
              <strong>Điểm Call:</strong> <br /><code
                >Max(0, 1 - (Số ngày chưa gặp / Max_Call))</code
              ><br />Chăm sóc (gặp/gọi) càng gần đây điểm càng cao.
            </li>
            <li>
              <strong>Điểm Chu kỳ:</strong> <br /><code
                >Min(1, Số ngày mua gần nhất / Trung bình chu kỳ)</code
              ><br />(Trong đó Trung bình chu kỳ =
              <code>(Số ngày mua gần thứ 2 + Số ngày mua gần thứ 3) / 2</code>).
              Điểm này dự đoán khách hàng đã đến kỳ mua tiếp theo hay chưa.
            </li>
            <li>
              <strong>ĐIỂM TỔNG:</strong> <br />Là tổng của tất cả các điểm
              thành phần nhân với <strong>Trọng số (%)</strong> cấu hình tương
              ứng. Điểm tối đa là 1.0, dùng để xếp hạng mức độ ưu tiên chăm sóc
              khách hàng.
            </li>
          </ul>
        </div>
        <div class="section mt-6">
          <h3>3. Lấy dữ liệu tổng hợp</h3>
          <ul class="explain-list">
            <li>
              <img src="/Mau.png" alt="Mau" class="mau-test" />
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: #1e293b;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: 16px;
  padding: 2rem;
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.5),
    0 10px 10px -5px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.4rem;
  color: #f8fafc;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ef4444;
}

.section h3 {
  font-size: 1.15rem;
  color: #818cf8;
  margin-bottom: 1rem;
  border-left: 4px solid #6366f1;
  padding-left: 0.75rem;
}

.section:first-child {
  text-align: left;
}

.section:last-child {
  text-align: center;
}

.section:last-child .explain-list li {
  width: 100%;
  text-align: center;
}

.explain-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.explain-list li {
  background: rgba(255, 255, 255, 0.03);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.95rem;
  line-height: 1.5;
  color: #cbd5e1;
  word-break: break-word;
  overflow-wrap: break-word;
}

.explain-list li strong {
  color: #f8fafc;
  font-weight: 600;
  display: inline-block;
  min-width: 160px;
  margin-bottom: 0.25rem;
}

.explain-list li code {
  background: rgba(15, 23, 42, 0.6);
  color: #10b981;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
  word-break: break-all;
  white-space: pre-wrap;
  display: inline-block;
  max-width: 100%;
}

.explain-content h4 {
  font-size: 1.05rem;
  color: #e2e8f0;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-weight: 700;
}

.explain-content h5 {
  font-size: 0.95rem;
  color: #94a3b8;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 0.25rem;
}

.explain-content p {
  font-size: 0.9rem;
  color: #cbd5e1;
  line-height: 1.5;
  margin-bottom: 1rem;
}

.explain-content ul {
  list-style: disc;
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.explain-content ul li {
  font-size: 0.9rem;
  color: #cbd5e1;
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.explain-content ul li strong {
  color: #f8fafc;
}

.note {
  font-size: 0.85rem !important;
  color: #64748b !important;
  margin-top: 0.25rem;
}

.mt-6 {
  margin-top: 2rem;
}

.flex {
  display: flex;
}
.items-center {
  align-items: center;
}
.gap-2 {
  gap: 0.5rem;
}
.text-indigo-400 {
  color: #818cf8;
}
.mau-test {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
