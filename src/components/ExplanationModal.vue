<script setup>
import { X, BookOpen } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close'])
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content glass-card">
      <div class="modal-header">
        <h2 class="flex items-center gap-2"><BookOpen :size="24" class="text-indigo-400" /> Giải Thích Cách Tính Toán</h2>
        <button class="close-btn" @click="emit('close')">
          <X :size="24" />
        </button>
      </div>

      <div class="modal-body">
        <div class="section">
          <h3>1. Bảng Tổng Hợp</h3>
          <ul class="explain-list">
            <li><strong>Ngày mua cuối:</strong> Lấy từ ngày đặt hàng gần đây nhất của khách hàng (chỉ tính trong khoảng thời gian quy định ở cấu hình, mặc định 6 tháng).</li>
            <li><strong>Số lần mua (6T):</strong> Đếm số lần khách hàng có phát sinh đơn hàng (số ngày mua khác nhau) trong khoảng 6 tháng qua.</li>
            <li><strong>Tổng doanh số 6 tháng:</strong> Tổng cộng thành tiền (Số lượng × Đơn giá) của tất cả đơn hàng trong 6 tháng.</li>
            <li><strong>Số ngày mua gần nhất:</strong> Hiệu số ngày giữa ngày hiện tại và <em>Ngày mua cuối</em>. (Càng nhỏ tức là mới mua càng gần đây).</li>
            <li><strong>Số ngày mua gần thứ 2:</strong> Số ngày giữa lần mua cuối cùng (gần nhất) và lần mua trước đó (lần 2).</li>
            <li><strong>Số ngày mua gần thứ 3:</strong> Số ngày giữa lần mua thứ 2 và lần mua thứ 3.</li>
            <li><strong>Số lần đã gặp:</strong> Tổng số cuộc gọi hoặc gặp gỡ được ghi nhận trong sheet Call.</li>
            <li><strong>Số ngày chưa gặp:</strong> Hiệu số ngày giữa ngày hiện tại và lần checkin/gặp mặt cuối cùng.</li>
            <li><strong>Hạng KH:</strong> Phân loại thành VIP, GOLD, NORMAL hoặc NEW dựa trên việc so sánh <em>Tổng doanh số 6 tháng</em> với các ngưỡng DS đã định trong mục Cài đặt.</li>
            <li><strong>DS mục tiêu & Call thiếu:</strong> Được lấy trực tiếp từ bảng định mức giao theo tuần/tháng (sheet FrequencyF).</li>
            <li><strong>DS thiếu:</strong> Bằng <em>DS mục tiêu</em> trừ đi <em>Tổng doanh số 6 tháng</em>. (Nếu số âm tức là đã vượt mục tiêu).</li>
          </ul>
        </div>

        <div class="section mt-6">
          <h3>2. Bảng Chấm Điểm (Công thức RFM)</h3>
          <ul class="explain-list">
            <li><strong>Điểm R (Recency):</strong> <br><code>Max(0, 1 - (Số ngày mua gần nhất / Max_Recency))</code><br>Mua càng gần đây điểm càng cao. Nếu vượt quá giới hạn Max_Recency thì điểm bằng 0.</li>
            <li><strong>Điểm F (Frequency):</strong> <br><code>Min(1, Số lần mua (6T) / Max_Frequency)</code><br>Mua càng nhiều lần điểm càng cao, tối đa 1.0.</li>
            <li><strong>Điểm M (Monetary):</strong> <br><code>Min(1, Tổng DS 6 tháng / Max_Monetary)</code><br>Doanh số càng lớn điểm càng cao, tối đa 1.0.</li>
            <li><strong>Điểm Hạng:</strong> Được quy đổi cố định: <code>VIP = 1.0</code>, <code>GOLD = 0.8</code>, <code>NORMAL = 0.6</code>, <code>NEW = 0.4</code>.</li>
            <li><strong>Điểm Call:</strong> <br><code>Max(0, 1 - (Số ngày chưa gặp / Max_Call))</code><br>Chăm sóc (gặp/gọi) càng gần đây điểm càng cao.</li>
            <li><strong>Điểm Chu kỳ:</strong> <br><code>Min(1, Số ngày mua gần nhất / Trung bình chu kỳ)</code><br>(Trong đó Trung bình chu kỳ = <code>(Số ngày mua gần thứ 2 + Số ngày mua gần thứ 3) / 2</code>). Điểm này dự đoán khách hàng đã đến kỳ mua tiếp theo hay chưa.</li>
            <li><strong>ĐIỂM TỔNG:</strong> <br>Là tổng của tất cả các điểm thành phần nhân với <strong>Trọng số (%)</strong> cấu hình tương ứng. Điểm tối đa là 1.0, dùng để xếp hạng mức độ ưu tiên chăm sóc khách hàng.</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
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
}

.mt-6 {
  margin-top: 2rem;
}

.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 0.5rem; }
.text-indigo-400 { color: #818cf8; }
</style>
