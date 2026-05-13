<script setup>
import { ref } from "vue";
import axios from "axios";
import {
  Upload,
  FileSpreadsheet,
  Download,
  CheckCircle,
  AlertCircle,
  Loader2,
  Settings,
  User,
  BookOpen,
  ExternalLink,
  Users,
  ShoppingBag,
  PhoneCall,
  CheckCircle2,
  TrendingUp,
  Hash,
  UserX,
  ShoppingCart,
  UserPlus,
  UserMinus,
} from "lucide-vue-next";
import ConfigModal from "./components/ConfigModal.vue";
import ResultTable from "./components/ResultTable.vue";
import ExplanationModal from "./components/ExplanationModal.vue";

const file = ref(null);
const isDragging = ref(false);
const showConfig = ref(false);
const showExplanation = ref(false);
const loading = ref(false);
const status = ref("idle"); // idle, uploading, success, error
const errorMessage = ref("");
const dataTonghop = ref(null);
const dataChamdiem = ref(null);
const dataNhanvien = ref(null);
const dataCasualOrders = ref(null);
const dataCasualCalls = ref(null);
const stats = ref(null);
const fileB64 = ref(null);

const nvHeaders = ["MNV", "Tên", "Nhóm", "Phòng ban", "Vị trí"];

const onFileChange = (e) => {
  const selectedFile = e.target.files[0];
  if (selectedFile) {
    file.value = selectedFile;
    status.value = "idle";
  }
};

const onDrop = (e) => {
  isDragging.value = false;
  const selectedFile = e.dataTransfer.files[0];
  if (selectedFile) {
    file.value = selectedFile;
    status.value = "idle";
  }
};

const processFile = async () => {
  if (!file.value) return;

  loading.value = true;
  status.value = "uploading";
  errorMessage.value = "";

  const formData = new FormData();
  formData.append("file", file.value);

  try {
    const response = await axios.post("/process", formData);

    dataTonghop.value = response.data.data_tonghop;
    dataChamdiem.value = response.data.data_chamdiem;
    dataNhanvien.value = response.data.data_nhanvien;
    dataCasualOrders.value = response.data.data_casual_orders;
    dataCasualCalls.value = response.data.data_casual_calls;
    stats.value = {
      total_customers: response.data.stats?.total_customers ?? 0,
      customers_with_orders: response.data.stats?.customers_with_orders ?? 0,
      customers_with_calls: response.data.stats?.customers_with_calls ?? 0,
      customers_with_both: response.data.stats?.customers_with_both ?? 0,
      customers_order_no_call: response.data.stats?.customers_order_no_call ?? 0,
      total_revenue: response.data.stats?.total_revenue ?? 0,
      total_orders: response.data.stats?.total_orders ?? 0,
      total_calls: response.data.stats?.total_calls ?? 0,
      casual_with_orders: response.data.stats?.casual_with_orders ?? 0,
      casual_with_calls: response.data.stats?.casual_with_calls ?? 0,
    };
    fileB64.value = response.data.file_b64;
    console.log("Dữ liệu nhận được:", response.data);

    status.value = "success";
  } catch (err) {
    console.error(err);
    status.value = "error";
    const data = err.response?.data;
    if (data && data.error) {
      errorMessage.value = `${data.error}`;
      if (data.traceback) {
        console.error("Server Traceback:", data.traceback);
      }
    } else if (err.code === "ECONNABORTED") {
      errorMessage.value = "Yêu cầu quá hạn. Vui lòng thử lại.";
    } else if (!err.response) {
      errorMessage.value = "Không thể kết nối đến server. Vui lòng kiểm tra server backend (app.py).";
    } else {
      errorMessage.value = "Có lỗi xảy ra trong quá trình xử lý.";
    }
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="container">
    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <img src="/logo.png" alt="CPC1HN Logo" class="app-logo" />
        </div>
        <h1>Data Analytics Dashboard</h1>
      </div>
      <div class="header-right">
        <!-- <a href="https://drive.google.com/drive/folders/1FJCHDyb4mM7uAADZzVy6fzuKzU4pJFcR" target="_blank" class="icon-btn btn-secondary" title="Mở tài liệu hướng dẫn">
          <ExternalLink size="20" />
          <span>Tài liệu</span>
        </a> -->
        <button
          class="icon-btn btn-secondary"
          @click="showExplanation = true"
          title="Giải thích tính toán"
        >
          <BookOpen size="20" />
          <span>Hướng dẫn</span>
        </button>
        <button
          class="icon-btn"
          @click="showConfig = true"
          title="Cài đặt cấu hình"
        >
          <Settings size="20" />
          <span>Cài đặt</span>
        </button>
      </div>
    </header>

    <main class="glass-card">
      <div
        class="upload-zone"
        :class="{ active: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
        @click="$refs.fileInput.click()"
      >
        <input
          type="file"
          ref="fileInput"
          hidden
          accept=".xlsx, .xls"
          @change="onFileChange"
        />

        <div v-if="!file" class="upload-prompt">
          <Upload :size="48" color="#6366f1" />
          <p>Kéo thả file Excel vào đây hoặc <span>chọn từ máy tính</span></p>
          <p class="hint">Hỗ trợ .xlsx, .xls (File Thống kê tổng)</p>
        </div>

        <div v-else class="file-selected">
          <FileSpreadsheet :size="48" color="#10b981" />
          <p class="filename">{{ file.name }}</p>
          <p class="filesize">{{ (file.size / 1024).toFixed(2) }} KB</p>
        </div>
      </div>

      <div class="actions">
        <!-- <a
          href="https://docs.google.com/spreadsheets/d/1YrSaIufQJzRe_5CuXSFc4EJDzXKzYTS_39z2-HwWOVI/edit?usp=sharing"
          target="_blank"
          class="icon-btn btn-secondary"
          title="Tải file dữ liệu mẫu"
          style="
            text-decoration: none;
            padding: 0.75rem 2rem;
            font-size: 1rem;
            border-radius: 12px;
            height: auto;
            font-weight: 600;
          "
        >
          <FileSpreadsheet :size="20" />
          <span>Tải mẫu</span>
        </a> -->
        <button
          class="btn-primary"
          :disabled="!file || loading"
          @click="processFile"
        >
          <template v-if="loading">
            <Loader2 class="animate-spin" />
            Đang xử lý...
          </template>
          <template v-else>
            <Download v-if="status === 'success'" />
            <span v-if="status === 'success'">Xử lý lại</span>
            <span v-else>Bắt đầu xử lý</span>
          </template>
        </button>
      </div>

      <div v-if="status === 'success'" class="feedback success">
        <CheckCircle color="#10b981" />
        <p>Xử lý thành công! Dữ liệu đã sẵn sàng.</p>
      </div>

      <div v-if="status === 'error'" class="feedback error">
        <AlertCircle color="#ef4444" />
        <p>{{ errorMessage }}</p>
      </div>
    </main>

    <div
      v-if="status === 'success' && dataNhanvien && dataNhanvien.length > 0"
      class="employee-info glass-card mb-4 mt-4"
    >
      <h3
        class="flex items-center gap-2 mb-3 text-indigo-400 border-b border-indigo-500/20 pb-2"
      >
        <User :size="20" /> Thông Tin Nhân Viên
      </h3>
      <div class="nv-table-wrapper">
        <table class="nv-table">
          <thead>
            <tr>
              <th v-for="col in nvHeaders" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(nv, idx) in dataNhanvien" :key="idx">
              <td
                v-for="col in nvHeaders"
                :key="col"
                class="font-medium text-white"
              >
                {{ nv[col] !== null && nv[col] !== undefined ? nv[col] : "-" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Monthly Statistics Section -->
    <div v-if="stats" class="stats-container mb-4 mt-4">
      <h3 class="flex items-center gap-2 mb-3 text-indigo-400 border-b border-indigo-500/20 pb-2">
        <TrendingUp :size="20" /> Thống Kê Hoạt Động Trong Tháng
      </h3>
      <div class="stats-grid">
      <div class="stats-card">
        <div class="stats-icon bg-blue-500/20 text-blue-400">
          <Users :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Tổng khách hàng</p>
          <h4 class="stats-value">{{ stats.total_customers.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon bg-green-500/20 text-green-400">
          <ShoppingBag :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">KH có đơn</p>
          <h4 class="stats-value">{{ stats.customers_with_orders.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon bg-purple-500/20 text-purple-400">
          <PhoneCall :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">KH có Call</p>
          <h4 class="stats-value">{{ stats.customers_with_calls.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon bg-indigo-500/20 text-indigo-400">
          <CheckCircle2 :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Call có đơn</p>
          <h4 class="stats-value">{{ stats.customers_with_both.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon bg-red-500/20 text-red-400">
          <UserX :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Đơn không Call</p>
          <h4 class="stats-value">{{ stats.customers_order_no_call.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

     

      <div class="stats-card">
        <div class="stats-icon bg-orange-500/20 text-orange-400">
          <ShoppingCart :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Tổng đơn</p>
          <h4 class="stats-value">{{ stats.total_orders.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon bg-pink-500/20 text-pink-400">
          <Hash :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Tổng Call</p>
          <h4 class="stats-value">{{ stats.total_calls.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon bg-cyan-500/20 text-cyan-400">
          <UserPlus :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Vãng lai có đơn</p>
          <h4 class="stats-value">{{ stats.casual_with_orders.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>

      <div class="stats-card">
        <div class="stats-icon bg-teal-500/20 text-teal-400">
          <UserMinus :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Vãng lai có Call</p>
          <h4 class="stats-value">{{ stats.casual_with_calls.toLocaleString('vi-VN') }}</h4>
        </div>
      </div>
       <div class="stats-card">
        <div class="stats-icon bg-yellow-500/20 text-yellow-400">
          <TrendingUp :size="24" />
        </div>
        <div class="stats-info">
          <p class="stats-label">Tổng doanh số</p>
          <h4 class="stats-value">{{ Math.round(stats.total_revenue).toLocaleString('vi-VN') }}</h4>
        </div>
      </div>
      </div>
    </div>

    <ResultTable
      v-if="status === 'success' && dataTonghop && dataChamdiem && fileB64"
      :data-tonghop="dataTonghop"
      :data-chamdiem="dataChamdiem"
      :data-casual-orders="dataCasualOrders"
      :data-casual-calls="dataCasualCalls"
      :file-b64="fileB64"
    />

    <section class="features" v-else-if="status !== 'success'">
      <div class="feature-item">
        <h3>📊 Thống kê Tổng hợp</h3>
        <p>
          Tự động tính toán Recency, Frequency, Monetary và Chu kỳ mua hàng dựa
          trên lịch sử đơn hàng.
        </p>
      </div>
      <div class="feature-item">
        <h3>⭐ Chấm điểm & Xếp hạng</h3>
        <p>
          Chấm điểm khách hàng theo công thức RFM chuẩn hóa, phân loại
          VIP/Gold/Normal chính xác.
        </p>
      </div>
      <div class="feature-item">
        <h3>⚙️ Cấu hình Linh hoạt</h3>
        <p>
          Mọi tham số tính toán đều được tham chiếu từ file Cấu_hình.xlsx, dễ
          dàng điều chỉnh.
        </p>
      </div>
    </section>

    <ConfigModal :show="showConfig" @close="showConfig = false" />
    <ExplanationModal
      :show="showExplanation"
      @close="showExplanation = false"
    />
  </div>
</template>

<style scoped>
.app-logo {
  width: 48px;
  height: auto;
  object-fit: contain;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-right {
  display: flex;
  gap: 1rem;
}

.icon-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  color: #e2e8f0;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.5);
  color: #fff;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.upload-prompt span {
  color: #6366f1;
  text-decoration: underline;
  font-weight: 600;
}

.hint {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 1rem;
}

.filename {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-top: 1rem;
}

.filesize {
  color: #94a3b8;
  font-size: 0.9rem;
}

.actions {
  margin-top: 2rem;
  display: flex;
  gap: 1rem;
  justify-content: center;
  align-items: stretch;
}

.feedback {
  margin-top: 2rem;
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.feedback.success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.feedback.error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Dashboard NV styles */
.employee-info {
  padding: 1.5rem;
}

.employee-info h3 {
  margin: 0;
  font-size: 1.1rem;
}

.nv-table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(15, 23, 42, 0.4);
}

.nv-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.nv-table th,
.nv-table td {
  padding: 0.875rem 1rem;
  white-space: nowrap;
}

.nv-table th {
  background: rgba(15, 23, 42, 0.8);
  color: #94a3b8;
  font-size: 0.85rem;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.nv-table td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.95rem;
}

.nv-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.02);
}

.mt-4 {
  margin-top: 1rem;
}
.mb-4 {
  margin-bottom: 1rem;
}
.mb-3 {
  margin-bottom: 0.75rem;
}
.pb-2 {
  padding-bottom: 0.5rem;
}
.border-b {
  border-bottom-width: 1px;
}
.border-indigo-500\/20 {
  border-color: rgba(99, 102, 241, 0.2);
}
.text-indigo-400 {
  color: #818cf8;
}
.text-white {
  color: #f8fafc;
}
.font-medium {
  font-weight: 500;
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

/* Statistics Grid Styles */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stats-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.stats-card:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 10px 20px -10px rgba(0, 0, 0, 0.5);
  background: rgba(15, 23, 42, 0.8);
}

.stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stats-info {
  display: flex;
  flex-direction: column;
}

.stats-label {
  font-size: 0.8rem;
  color: #94a3b8;
  margin: 0;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.stats-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #f8fafc;
  margin: 0.25rem 0 0 0;
}

/* Color utilities if not using tailwind properly */
.bg-blue-500\/20 { background: rgba(59, 130, 246, 0.2); }
.text-blue-400 { color: #60a5fa; }
.bg-green-500\/20 { background: rgba(16, 185, 129, 0.2); }
.text-green-400 { color: #4ade80; }
.bg-purple-500\/20 { background: rgba(168, 85, 247, 0.2); }
.text-purple-400 { color: #c084fc; }
.bg-indigo-500\/20 { background: rgba(99, 102, 241, 0.2); }
.text-indigo-400 { color: #818cf8; }
.bg-red-500\/20 { background: rgba(239, 68, 68, 0.2); }
.text-red-400 { color: #f87171; }
.bg-yellow-500\/20 { background: rgba(234, 179, 8, 0.2); }
.text-yellow-400 { color: #facc15; }
.bg-pink-500\/20 { background: rgba(236, 72, 153, 0.2); }
.text-pink-400 { color: #f472b6; }
.bg-orange-500\/20 { background: rgba(249, 115, 22, 0.2); }
.text-orange-400 { color: #fb923c; }
.bg-cyan-500\/20 { background: rgba(6, 182, 212, 0.2); }
.text-cyan-400 { color: #22d3ee; }
.bg-teal-500\/20 { background: rgba(20, 184, 166, 0.2); }
.text-teal-400 { color: #2dd4bf; }
</style>
