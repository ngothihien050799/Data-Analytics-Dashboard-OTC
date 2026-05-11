<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { Upload, FileSpreadsheet, Download, CheckCircle, AlertCircle, Loader2, Settings, User, BookOpen, ExternalLink } from 'lucide-vue-next'
import ConfigModal from './components/ConfigModal.vue'
import ResultTable from './components/ResultTable.vue'
import ExplanationModal from './components/ExplanationModal.vue'

const file = ref(null)
const isDragging = ref(false)
const showConfig = ref(false)
const showExplanation = ref(false)
const loading = ref(false)
const status = ref('idle') // idle, uploading, success, error
const errorMessage = ref('')
const dataTonghop = ref(null)
const dataChamdiem = ref(null)
const dataNhanvien = ref(null)
const fileB64 = ref(null)

const nvHeaders = ['MNV', 'Tên', 'Nhóm', 'Phòng ban', 'Vị trí']

const onFileChange = (e) => {
  const selectedFile = e.target.files[0]
  if (selectedFile) {
    file.value = selectedFile
    status.value = 'idle'
  }
}

const onDrop = (e) => {
  isDragging.value = false
  const selectedFile = e.dataTransfer.files[0]
  if (selectedFile) {
    file.value = selectedFile
    status.value = 'idle'
  }
}

const processFile = async () => {
  if (!file.value) return

  loading.value = true
  status.value = 'uploading'
  errorMessage.value = ''

  const formData = new FormData()
  formData.append('file', file.value)

  try {
    const response = await axios.post('/process', formData)

    dataTonghop.value = response.data.data_tonghop
    dataChamdiem.value = response.data.data_chamdiem
    dataNhanvien.value = response.data.data_nhanvien
    fileB64.value = response.data.file_b64
    
    status.value = 'success'
  } catch (err) {
    console.error(err)
    status.value = 'error'
    errorMessage.value = err.response?.data?.error || 'Có lỗi xảy ra trong quá trình xử lý.'
  } finally {
    loading.value = false
  }
}
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
        <a href="https://drive.google.com/drive/folders/1FJCHDyb4mM7uAADZzVy6fzuKzU4pJFcR" target="_blank" class="icon-btn btn-secondary" title="Mở tài liệu hướng dẫn">
          <ExternalLink size="20" />
          <span>Tài liệu</span>
        </a>
        <button class="icon-btn btn-secondary" @click="showExplanation = true" title="Giải thích tính toán">
          <BookOpen size="20" />
          <span>Hướng dẫn</span>
        </button>
        <button class="icon-btn" @click="showConfig = true" title="Cài đặt cấu hình">
          <Settings size="20" />
          <span>Cài đặt</span>
        </button>
      </div>
    </header>

    <main class="glass-card">
      <div 
        class="upload-zone"
        :class="{ 'active': isDragging }"
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
        >
        
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

    <div v-if="status === 'success' && dataNhanvien && dataNhanvien.length > 0" class="employee-info glass-card mb-4 mt-4">
      <h3 class="flex items-center gap-2 mb-3 text-indigo-400 border-b border-indigo-500/20 pb-2"><User :size="20"/> Thông Tin Nhân Viên</h3>
      <div class="nv-table-wrapper">
        <table class="nv-table">
          <thead>
            <tr>
              <th v-for="col in nvHeaders" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(nv, idx) in dataNhanvien" :key="idx">
              <td v-for="col in nvHeaders" :key="col" class="font-medium text-white">
                {{ nv[col] !== null && nv[col] !== undefined ? nv[col] : '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ResultTable 
      v-if="status === 'success' && dataTonghop && dataChamdiem && fileB64" 
      :data-tonghop="dataTonghop"
      :data-chamdiem="dataChamdiem" 
      :file-b64="fileB64" 
    />

    <section class="features" v-else-if="status !== 'success'">
      <div class="feature-item">
        <h3>📊 Thống kê Tổng hợp</h3>
        <p>Tự động tính toán Recency, Frequency, Monetary và Chu kỳ mua hàng dựa trên lịch sử đơn hàng.</p>
      </div>
      <div class="feature-item">
        <h3>⭐ Chấm điểm & Xếp hạng</h3>
        <p>Chấm điểm khách hàng theo công thức RFM chuẩn hóa, phân loại VIP/Gold/Normal chính xác.</p>
      </div>
      <div class="feature-item">
        <h3>⚙️ Cấu hình Linh hoạt</h3>
        <p>Mọi tham số tính toán đều được tham chiếu từ file Cấu_hình.xlsx, dễ dàng điều chỉnh.</p>
      </div>
    </section>

    <ConfigModal :show="showConfig" @close="showConfig = false" />
    <ExplanationModal :show="showExplanation" @close="showExplanation = false" />
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
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

.nv-table th, .nv-table td {
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

.mt-4 { margin-top: 1rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 0.75rem; }
.pb-2 { padding-bottom: 0.5rem; }
.border-b { border-bottom-width: 1px; }
.border-indigo-500\/20 { border-color: rgba(99, 102, 241, 0.2); }
.text-indigo-400 { color: #818cf8; }
.text-white { color: #f8fafc; }
.font-medium { font-weight: 500; }
.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 0.5rem; }
</style>
