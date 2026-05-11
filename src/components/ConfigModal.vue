<script setup>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'
import { X, Save, Loader2, AlertCircle, CheckCircle } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close'])

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref(false)

const config = reactive({
  w_r: '',
  w_f: '',
  w_m: '',
  w_rank: '',
  w_call: '',
  w_cycle: '',
  max_recency: '',
  f_window_months: '',
  max_frequency: '',
  max_monetary: '',
  max_call_days: '',
  threshold_vip: '',
  threshold_gold: '',
  threshold_normal: '',
  ds_window_months: ''
})

const parsePctToNumber = (val) => {
  if (typeof val === 'string' && val.includes('%')) {
    return parseFloat(val.replace('%', '')) / 100
  }
  return parseFloat(val)
}

const loadConfig = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await axios.get('/config')
    // Transform percentage strings to numbers for inputs (e.g. "20%" -> 0.2)
    config.w_r = parsePctToNumber(res.data.w_r) * 100
    config.w_f = parsePctToNumber(res.data.w_f) * 100
    config.w_m = parsePctToNumber(res.data.w_m) * 100
    config.w_rank = parsePctToNumber(res.data.w_rank) * 100
    config.w_call = parsePctToNumber(res.data.w_call) * 100
    config.w_cycle = parsePctToNumber(res.data.w_cycle) * 100
    
    config.max_recency = res.data.max_recency
    config.f_window_months = res.data.f_window_months
    config.max_frequency = res.data.max_frequency
    config.max_monetary = res.data.max_monetary
    config.max_call_days = res.data.max_call_days
    
    config.threshold_vip = res.data.threshold_vip
    config.threshold_gold = res.data.threshold_gold
    config.threshold_normal = res.data.threshold_normal
    config.ds_window_months = res.data.ds_window_months
  } catch (err) {
    console.error(err)
    error.value = 'Không thể tải cấu hình từ máy chủ.'
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  error.value = ''
  success.value = false
  
  const payload = {
    w_r: (config.w_r / 100).toString(),
    w_f: (config.w_f / 100).toString(),
    w_m: (config.w_m / 100).toString(),
    w_rank: (config.w_rank / 100).toString(),
    w_call: (config.w_call / 100).toString(),
    w_cycle: (config.w_cycle / 100).toString(),
    max_recency: config.max_recency,
    f_window_months: config.f_window_months,
    max_frequency: config.max_frequency,
    max_monetary: config.max_monetary,
    max_call_days: config.max_call_days,
    threshold_vip: config.threshold_vip,
    threshold_gold: config.threshold_gold,
    threshold_normal: config.threshold_normal,
    ds_window_months: config.ds_window_months
  }

  try {
    await axios.post('/config', payload)
    success.value = true
    setTimeout(() => {
      success.value = false
      emit('close')
    }, 1500)
  } catch (err) {
    console.error(err)
    error.value = 'Không thể lưu cấu hình.'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (props.show) {
    loadConfig()
  }
})

// Watch for show prop changes to reload if needed
import { watch } from 'vue'
watch(() => props.show, (newVal) => {
  if (newVal) {
    loadConfig()
  }
})
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content glass-card">
      <div class="modal-header">
        <h2>Cài đặt Cấu hình</h2>
        <button class="close-btn" @click="emit('close')">
          <X :size="24" />
        </button>
      </div>

      <div class="modal-body" v-if="loading">
        <div class="loading-state">
          <Loader2 class="animate-spin" :size="32" />
          <p>Đang tải cấu hình...</p>
        </div>
      </div>

      <div class="modal-body" v-else>
        <div v-if="error" class="feedback error mb-4">
          <AlertCircle :size="20" />
          <p>{{ error }}</p>
        </div>
        
        <div v-if="success" class="feedback success mb-4">
          <CheckCircle :size="20" />
          <p>Đã lưu cấu hình thành công!</p>
        </div>

        <form @submit.prevent="saveConfig" class="config-form">
          <div class="form-section">
            <h3>1. Trọng số tính điểm (Tổng = 100%)</h3>
            <div class="grid-2">
              <div class="form-group">
                <label>Recency (%)</label>
                <p class="hint">Thời gian từ lần mua cuối</p>
                <input type="number" v-model="config.w_r" required min="0" max="100">
              </div>
              <div class="form-group">
                <label>Frequency (%)</label>
                <p class="hint">Tần suất mua hàng</p>
                <input type="number" v-model="config.w_f" required min="0" max="100">
              </div>
              <div class="form-group">
                <label>Monetary (%)</label>
                <p class="hint">Giá trị đơn hàng</p>
                <input type="number" v-model="config.w_m" required min="0" max="100">
              </div>
              <div class="form-group">
                <label>Hạng KH (%)</label>
                <p class="hint">Phân loại VIP / Thường / Mới</p>
                <input type="number" v-model="config.w_rank" required min="0" max="100">
              </div>
              <div class="form-group">
                <label>Call (%)</label>
                <p class="hint">Thời gian từ lần gặp cuối</p>
                <input type="number" v-model="config.w_call" required min="0" max="100">
              </div>
              <div class="form-group">
                <label>Chu kỳ (%)</label>
                <p class="hint">Dự đoán kỳ mua tiếp theo</p>
                <input type="number" v-model="config.w_cycle" required min="0" max="100">
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>2. Thông số hệ thống</h3>
            <div class="grid-2">
              <div class="form-group">
                <label>Max ngày Recency</label>
                <p class="hint">Khách > giá trị này → điểm R = 0</p>
                <input type="number" v-model="config.max_recency" required>
              </div>
              <div class="form-group">
                <label>Max lần mua (Frequency)</label>
                <p class="hint">Số lần mua tối đa → điểm F = 1.0</p>
                <input type="number" v-model="config.max_frequency" required>
              </div>
              <div class="form-group">
                <label>Max doanh số (Monetary)</label>
                <p class="hint">Doanh số tối đa → điểm M = 1.0 (ngưỡng VIP)</p>
                <input type="number" v-model="config.max_monetary" required>
              </div>
              <div class="form-group">
                <label>Max ngày Call</label>
                <p class="hint">Số ngày chưa gặp tối đa → điểm Call = 0</p>
                <input type="number" v-model="config.max_call_days" required>
              </div>
              <div class="form-group">
                <label>Cửa sổ tính Frequency (tháng)</label>
                <p class="hint">Số tháng nhìn lại để đếm lần mua</p>
                <input type="number" v-model="config.f_window_months" required>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>3. Ngưỡng phân hạng</h3>
            <div class="grid-2">
              <div class="form-group">
                <label>Ngưỡng VIP (DS 6 tháng)</label>
                <p class="hint">DS 6T ≥ giá trị này → xếp hạng VIP</p>
                <input type="number" v-model="config.threshold_vip" required>
              </div>
              <div class="form-group">
                <label>Ngưỡng GOLD</label>
                <p class="hint">DS 6T ≥ giá trị này VÀ < Ngưỡng VIP</p>
                <input type="number" v-model="config.threshold_gold" required>
              </div>
              <div class="form-group">
                <label>Ngưỡng NORMAL</label>
                <p class="hint">DS 6T ≥ giá trị này VÀ < Ngưỡng GOLD</p>
                <input type="number" v-model="config.threshold_normal" required>
              </div>
              <div class="form-group">
                <label>Cửa sổ tính DS (tháng)</label>
                <p class="hint">Số tháng nhìn lại để tính Tổng doanh số</p>
                <input type="number" v-model="config.ds_window_months" required>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="emit('close')" :disabled="saving">Hủy</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              <Loader2 v-if="saving" class="animate-spin mr-2" :size="18" />
              <Save v-else class="mr-2" :size="18" />
              Lưu thay đổi
            </button>
          </div>
        </form>
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
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
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
  color: #f8fafc;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
  color: #94a3b8;
}

.loading-state p {
  margin-top: 1rem;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section h3 {
  font-size: 1.1rem;
  color: #cbd5e1;
  margin-bottom: 1rem;
  border-left: 3px solid #6366f1;
  padding-left: 0.75rem;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #e2e8f0;
}

.hint {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: -0.25rem;
  margin-bottom: 0.25rem;
  line-height: 1.2;
}

.form-group input {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: #f8fafc;
  font-size: 1rem;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.mr-2 {
  margin-right: 0.5rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.feedback {
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
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

@media (max-width: 640px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
</style>
