<script setup>
import { computed, ref } from 'vue'
import { Search, Download, ChevronLeft, ChevronRight, Award, LayoutList } from 'lucide-vue-next'

const props = defineProps({
  dataTonghop: {
    type: Array,
    required: true
  },
  dataChamdiem: {
    type: Array,
    required: true
  },
  fileB64: {
    type: String,
    required: true
  }
})

const activeTab = ref('chamdiem') // 'chamdiem' or 'tonghop'
const searchQuery = ref('')
const currentPage = ref(1)
const itemsPerPage = ref(50)

const currentData = computed(() => {
  return activeTab.value === 'chamdiem' ? props.dataChamdiem : props.dataTonghop
})

const filteredData = computed(() => {
  if (!searchQuery.value) return currentData.value
  const query = searchQuery.value.toLowerCase()
  return currentData.value.filter(item => {
    return (item['Tên KH']?.toLowerCase().includes(query)) || 
           (item['Mã KH']?.toString().toLowerCase().includes(query)) ||
           (item['Hạng KH']?.toLowerCase().includes(query))
  })
})

const totalPages = computed(() => Math.ceil(filteredData.value.length / itemsPerPage.value) || 1)

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredData.value.slice(start, end)
})

const switchTab = (tab) => {
  activeTab.value = tab
  currentPage.value = 1
}

const downloadExcel = () => {
  const link = document.createElement('a')
  link.href = `data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${props.fileB64}`
  link.setAttribute('download', `Ket_Qua_Thong_Ke_${new Date().toLocaleDateString('vi-VN')}.xlsx`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  if (typeof num === 'number') {
    return Math.ceil(num).toLocaleString('vi-VN')
  }
  return num
}

const getRankColor = (rank) => {
  switch(rank) {
    case 'VIP': return 'badge-vip'
    case 'GOLD': return 'badge-gold'
    case 'NORMAL': return 'badge-normal'
    case 'NEW': return 'badge-new'
    default: return 'badge-default'
  }
}

const interpolateColor = (c1, c2, factor) => {
  return c1.map((val, i) => Math.round(val + factor * (c2[i] - val)))
}

const getScoreGradientStyle = (score) => {
  if (score === null || score === undefined) return {}
  
  const s = Math.max(0, Math.min(1, score))
  
  const GRAY = [100, 116, 139]
  const BLUE = [59, 130, 246]
  const ORANGE = [249, 115, 22]
  const RED = [239, 68, 68]
  const DEEP_RED = [220, 38, 38]
  
  let rgb;
  if (s >= 0.75) {
    const factor = (s - 0.75) / 0.25;
    rgb = interpolateColor(RED, DEEP_RED, factor);
  } else if (s >= 0.55) {
    const factor = (s - 0.55) / 0.20;
    rgb = interpolateColor(ORANGE, RED, factor);
  } else if (s >= 0.40) {
    const factor = (s - 0.40) / 0.15;
    rgb = interpolateColor(BLUE, ORANGE, factor);
  } else {
    const factor = s / 0.40;
    rgb = interpolateColor(GRAY, BLUE, factor);
  }
  
  return {
    background: `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.15)`,
    color: `rgb(${rgb[0] + 30}, ${rgb[1] + 30}, ${rgb[2] + 30})`, // Slightly lighter for text
    textShadow: `0 0 10px rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.3)`,
    borderLeft: `3px solid rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`
  }
}

const getAlertStyle = (col, val) => {
  if (val === null || val === undefined || val === '-' || val === '') return {}
  
  if (col === 'Call còn lại' || col === 'Call thiếu' || col === 'DS thiếu') {
    const num = parseFloat(val)
    if (isNaN(num)) return {}
    if (num > 0) return { background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5' }
    return { background: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7' }
  }
  
  if (col === 'Số ngày chưa gặp') {
    const num = parseFloat(val)
    if (isNaN(num)) return {}
    if (num > 14) return { background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5' }
    return { background: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7' }
  }
  
  return {}
}

const getGroupClass = (col) => {
  const history = ['Ngày mua cuối', 'Số lần mua trong 6 tháng', 'Tổng doanh số 6 tháng', 'Số ngày mua gần nhất', 'Số ngày mua gần thứ 2', 'Số ngày mua gần thứ 3']
  const hoatdong = ['Số lần đã gặp', 'Số ngày chưa gặp']
  const tonghop = ['Hạng KH', 'Tổng DS tháng', 'Tổng DS tháng trước']
  const gap = ['Call thiếu', 'DS mục tiêu', 'DS thiếu']
  const trend = ['Xu hướng mua', 'Chu kỳ TB', 'Dự báo ngày mua tiếp', 'Trạng thái hoạt động']
  
  if (['Mã KH', 'Tên khách hàng'].includes(col)) return 'group-kh'
  if (history.includes(col)) return 'group-history'
  if (hoatdong.includes(col)) return 'group-hoatdong'
  if (tonghop.includes(col)) return 'group-tonghop'
  if (gap.includes(col)) return 'group-gap'
  if (trend.includes(col)) return 'group-trend'
  
  return ''
}

// Extract headers for tonghop dynamically
const tonghopHeaders = computed(() => {
  if (props.dataTonghop.length === 0) return []
  return [
    'Mã KH', 'Tên khách hàng', 
    'Ngày mua cuối', 'Số lần mua trong 6 tháng', 'Tổng doanh số 6 tháng', 'Số ngày mua gần nhất', 'Số ngày mua gần thứ 2', 'Số ngày mua gần thứ 3', 
    'Số lần đã gặp', 'Số ngày chưa gặp', 
    'Hạng KH', 'Tổng DS tháng', 'Tổng DS tháng trước',
    'Call thiếu', 'DS mục tiêu', 'DS thiếu',
    'Xu hướng mua', 'Chu kỳ TB', 'Dự báo ngày mua tiếp', 'Trạng thái hoạt động'
  ]
})
</script>

<template>
  <div class="result-container glass-card">
    <div class="tabs-wrapper">
      <div class="tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'chamdiem' }"
          @click="switchTab('chamdiem')"
        >
          <Award :size="18" /> Bảng Chấm Điểm
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'tonghop' }"
          @click="switchTab('tonghop')"
        >
          <LayoutList :size="18" /> Bảng Tổng Hợp
        </button>
      </div>
      <button class="btn-primary flex items-center gap-2 download-btn" @click="downloadExcel">
        <Download :size="18" />
        Tải xuống Excel
      </button>
    </div>

    <div class="toolbar">
      <div class="search-box">
        <Search :size="18" class="text-gray-400" />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Tìm kiếm Mã KH, Tên, Hạng..."
          @input="currentPage = 1"
        >
      </div>
      <div class="actions">
        <span class="total-badge">Tổng: {{ filteredData.length }} KH</span>
      </div>
    </div>

    <div class="table-wrapper">
      <!-- Bảng Chấm Điểm -->
      <table v-if="activeTab === 'chamdiem'" class="table-chamdiem">
        <thead>
          <tr class="group-header">
            <th colspan="3" class="text-center group-kh">THÔNG TIN KH</th>
            <th colspan="6" class="text-center group-rfm">ĐIỂM THÀNH PHẦN RFM</th>
            <th colspan="1" class="text-center group-tonghop">TỔNG HỢP</th>
            <th colspan="3" class="text-center group-hoatdong">HOẠT ĐỘNG</th>
            <th colspan="1" class="text-center group-chon">CHỌN</th>
          </tr>
          <tr class="sub-header">
            <th class="group-kh">Mã KH</th>
            <th class="group-kh">Tên KH</th>
            <th class="group-kh">Hạng KH</th>
            
            <th class="text-right group-rfm">Điểm R</th>
            <th class="text-right group-rfm">Điểm F</th>
            <th class="text-right group-rfm">Điểm M</th>
            <th class="text-right group-rfm">Điểm Hạng</th>
            <th class="text-right group-rfm">Điểm Call</th>
            <th class="text-right group-rfm">Điểm Chu kỳ</th>
            
            <th class="text-right group-tonghop">ĐIỂM TỔNG</th>
            
            <th class="text-right group-hoatdong">Call còn lại</th>
            <th class="text-right group-hoatdong">Số ngày chưa gặp</th>
            <th class="text-right group-hoatdong">Ngày gặp cuối</th>
            
            <th class="text-center group-chon">Chọn</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paginatedData.length === 0">
            <td colspan="13" class="empty-state">Không tìm thấy dữ liệu phù hợp</td>
          </tr>
          <tr v-for="row in paginatedData" :key="row['Mã KH']">
            <td><span class="font-mono text-sm">{{ row['Mã KH'] }}</span></td>
            <td class="font-medium text-white">{{ row['Tên KH'] }}</td>
            <td>
              <span class="badge" :class="getRankColor(row['Hạng KH'])">
                <Award v-if="row['Hạng KH'] === 'VIP'" :size="14" class="mr-1" />
                {{ row['Hạng KH'] || '-' }}
              </span>
            </td>
            
            <td class="text-right text-gray-300">{{ formatNumber(row['Điểm R']) }}</td>
            <td class="text-right text-gray-300">{{ formatNumber(row['Điểm F']) }}</td>
            <td class="text-right text-gray-300">{{ formatNumber(row['Điểm M']) }}</td>
            <td class="text-right text-gray-300">{{ formatNumber(row['Điểm Hạng']) }}</td>
            <td class="text-right text-gray-300">{{ formatNumber(row['Điểm Call']) }}</td>
            <td class="text-right text-gray-300">{{ formatNumber(row['Điểm Chu kỳ']) }}</td>
            
            <td class="text-right font-bold" :style="getScoreGradientStyle(row['ĐIỂM TỔNG'])">
              {{ formatNumber(row['ĐIỂM TỔNG']) }}
            </td>
            
            <td class="text-right" :style="getAlertStyle('Call còn lại', row['Call còn lại'])">{{ formatNumber(row['Call còn lại']) }}</td>
            <td class="text-right" :style="getAlertStyle('Số ngày chưa gặp', row['Số ngày chưa gặp'])">{{ formatNumber(row['Số ngày chưa gặp']) }}</td>
            <td class="text-right text-gray-300">{{ row['Ngày gặp cuối'] || '-' }}</td>
            
            <td class="text-center">
              <input type="checkbox" class="row-checkbox">
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Bảng Tổng Hợp -->
      <table v-else class="table-tonghop">
        <thead>
          <tr class="group-header">
            <th colspan="2" class="text-center group-kh">THÔNG TIN KH</th>
            <th colspan="6" class="text-center group-history">LỊCH SỬ MUA HÀNG</th>
            <th colspan="2" class="text-center group-hoatdong">HOẠT ĐỘNG GHÉ THĂM</th>
            <th colspan="3" class="text-center group-tonghop">PHÂN LOẠI & DOANH SỐ THÁNG</th>
            <th colspan="3" class="text-center group-gap">CHỈ SỐ THIẾU HỤT</th>
            <th colspan="4" class="text-center group-trend">XU HƯỚNG & HÀNH ĐỘNG</th>
          </tr>
          <tr class="sub-header">
            <th v-for="col in tonghopHeaders" :key="col" class="text-center" :class="getGroupClass(col)">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paginatedData.length === 0">
            <td :colspan="tonghopHeaders.length" class="empty-state">Không tìm thấy dữ liệu phù hợp</td>
          </tr>
          <tr v-for="(row, idx) in paginatedData" :key="row['Mã KH'] || idx">
            <td v-for="col in tonghopHeaders" :key="col" :class="{'text-right': typeof row[col] === 'number'}" :style="getAlertStyle(col, row[col])">
              <span v-if="col === 'Hạng KH'" class="badge" :class="getRankColor(row[col])">{{ row[col] }}</span>
              <span v-else-if="col === 'Mã KH'" class="font-mono text-sm">{{ row[col] }}</span>
              <span v-else>{{ formatNumber(row[col]) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination-container" v-if="filteredData.length > 0">
      <div class="page-size">
        <label>Hiển thị:</label>
        <select v-model="itemsPerPage" @change="currentPage = 1">
          <option :value="10">10 dòng</option>
          <option :value="20">20 dòng</option>
          <option :value="50">50 dòng</option>
          <option :value="100">100 dòng</option>
        </select>
      </div>

      <div class="pagination" v-if="totalPages > 1">
        <button 
          class="page-btn" 
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          <ChevronLeft :size="18" />
        </button>
        <span class="page-info">Trang {{ currentPage }} / {{ totalPages }}</span>
        <button 
          class="page-btn" 
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          <ChevronRight :size="18" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-container {
  margin-top: 2rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tabs-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 1rem;
}

.tabs {
  display: flex;
  gap: 1rem;
}

.tab-btn {
  background: none;
  border: none;
  color: #94a3b8;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  border-radius: 6px 6px 0 0;
}

.tab-btn:hover {
  color: #f8fafc;
  background: rgba(255, 255, 255, 0.05);
}

.tab-btn.active {
  color: #818cf8;
  border-bottom-color: #818cf8;
  background: rgba(99, 102, 241, 0.1);
}

.download-btn {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  width: 100%;
  max-width: 350px;
}

.search-box input {
  background: transparent;
  border: none;
  color: #f8fafc;
  width: 100%;
  font-size: 0.95rem;
}

.search-box input:focus {
  outline: none;
}

.total-badge {
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  max-height: calc(100vh - 280px);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(15, 23, 42, 0.4);
}

thead {
  position: sticky;
  top: 0;
  z-index: 20;
}

table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

th, td {
  padding: 0.75rem 1rem;
  white-space: nowrap;
}

/* Multi-level header styles */
.group-header th {
  font-size: 0.85rem;
  font-weight: 900 !important;
  color: #ffffff !important;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.group-kh { background: #1e3a8a !important; }
.group-rfm { background: #064e3b !important; }
.group-tonghop { background: #4c1d95 !important; }
.group-hoatdong { background: #78350f !important; }
.group-chon { background: #1e293b !important; border-right: none !important; }

/* New groups for TongHop */
.group-history { background: #065f46 !important; border-right: 1px solid rgba(255,255,255,0.05); }
.group-gap { background: #9f1239 !important; border-right: 1px solid rgba(255,255,255,0.05); }
.group-trend { background: #0f766e !important; border-right: none !important; }

.sub-header th {
  background: #0f172a;
  color: #94a3b8;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.table-tonghop th {
  background: #0f172a;
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.9rem;
  border-right: 1px solid rgba(255, 255, 255, 0.02);
}

tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

.highlight-col {
  background: rgba(99, 102, 241, 0.05);
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
}

.text-center { text-align: center; }
.text-right { text-align: right; }
.text-gray-300 { color: #cbd5e1; }
.text-gray-400 { color: #94a3b8; }
.font-mono { font-family: monospace; }
.font-medium { font-weight: 500; }
.font-bold { font-weight: 700; }
.text-sm { font-size: 0.85rem; }
.text-white { color: #f8fafc; }
.text-indigo-400 { color: #818cf8; }
.mr-1 { margin-right: 0.25rem; }
.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 0.5rem; }

.row-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #6366f1;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-vip { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); }
.badge-gold { background: rgba(245, 158, 11, 0.15); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-normal { background: rgba(59, 130, 246, 0.15); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.3); }
.badge-new { background: rgba(100, 116, 139, 0.15); color: #cbd5e1; border: 1px solid rgba(100, 116, 139, 0.3); }
.badge-default { background: rgba(255, 255, 255, 0.1); color: #e2e8f0; }

.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-size {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #94a3b8;
  font-size: 0.9rem;
}

.page-size select {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #f8fafc;
  padding: 0.3rem 0.5rem;
  border-radius: 6px;
  outline: none;
  cursor: pointer;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
}

.page-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  padding: 0.4rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.page-btn:not(:disabled):hover {
  background: rgba(255, 255, 255, 0.1);
  color: #f8fafc;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.9rem;
  color: #94a3b8;
}
</style>
