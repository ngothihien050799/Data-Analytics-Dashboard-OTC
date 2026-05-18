<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from "vue";
import axios from "axios";
import {
  Upload,
  FileSpreadsheet,
  Loader2,
  AlertCircle,
  Maximize2,
  Minimize2,
} from "lucide-vue-next";
import Chart from "chart.js/auto";

// Data state
const file = ref(null);
const isDragging = ref(false);
const loading = ref(false);
const status = ref("idle");
const errorMessage = ref("");

const rawData = ref(null); // { groups: [...] }
const currentGroupIndex = ref(0);
const activeView = ref("overview");
const charts = ref({});
const isFullscreen = ref(false);
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const AVATAR_COLORS = [
  "#a855f7",
  "#818cf8",
  "#ec4899",
  "#6366f1",
  "#f43f5e",
  "#14b8a6",
  "#3b82f6",
  "#f59e0b",
];
const avatarColor = (name, i) => {
  if (!name) return AVATAR_COLORS[i % AVATAR_COLORS.length];
  const lastWord = name.trim().split(" ").pop();
  const nameColorMap = {
    "Duyên": "#3b82f6",
    "Huy": "#10b981",
    "Nguyên": "#818cf8",
    "Bách": "#f59e0b",
    "Nam": "#06b6d4",
    "Tuấn": "#ef4444",
  };
  return nameColorMap[lastWord] || AVATAR_COLORS[i % AVATAR_COLORS.length];
};
const initials = (name) => {
  if (!name) return "";
  const p = name.trim().split(" ");
  return p.length >= 2
    ? p[p.length - 2][0] + p[p.length - 1][0]
    : name.slice(0, 2);
};

const getFirstAndLast = (name) => {
  if (!name) return "";
  const parts = name.trim().split(/\s+/);
  if (parts.length <= 2) return name;
  return `${parts[parts.length - 2]} ${parts[parts.length - 1]}`;
};

const currentGroup = computed(() => {
  if (
    !rawData.value ||
    !rawData.value.groups ||
    rawData.value.groups.length === 0
  )
    return null;
  return rawData.value.groups[currentGroupIndex.value];
});

const groupStats = computed(() => {
  const g = currentGroup.value;
  if (!g) return null;
  const m = g.members;
  const active = m.filter((x) => x.visits > 0);
  return {
    totalVisits: m.reduce((s, x) => s + x.visits, 0),
    totalRev: m.reduce((s, x) => s + x.rev, 0),
    totalOrders: m.reduce((s, x) => s + x.orders, 0),
    totalKhBuy: m.reduce((s, x) => s + x.kh_buy, 0),
    totalKhVisit: m.reduce((s, x) => s + x.kh_visit, 0),
    activeCount: active.length,
    totalCount: m.length,
    avgConv: active.length
      ? active.reduce((s, x) => s + x.conv, 0) / active.length
      : 0,
    avgDur: active.length
      ? active.reduce((s, x) => s + x.avg_dur, 0) / active.length
      : 0,
    noteBadPct: active.length
      ? active.reduce((s, x) => s + x.note_bad_pct, 0) / active.length
      : 0,
    gpsIssues: m.reduce((s, x) => s + x.gps_same, 0),
    offHours: m.reduce((s, x) => s + x.off_hours, 0),
  };
});

const activeMembers = computed(() => {
  if (!currentGroup.value) return [];
  return currentGroup.value.members
    .filter((x) => x.visits > 0)
    .sort((a, b) => b.rev - a.rev);
});

const sortedByRev = computed(() => {
  if (!currentGroup.value) return [];
  return [...currentGroup.value.members].sort((a, b) => b.rev - a.rev);
});

const maxRev = computed(() => {
  const m = sortedByRev.value;
  if (!m.length) return 1;
  return Math.max(...m.map((x) => x.rev), 1);
});

// File Handlers
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
    const response = await axios.post("/process_hanh_vi", formData);
    rawData.value = response.data;
    status.value = "success";
    currentGroupIndex.value = 0;
    activeView.value = "overview";
    await nextTick();
    renderAllCharts();
  } catch (err) {
    console.error(err);
    status.value = "error";
    errorMessage.value =
      err.response?.data?.error || "Có lỗi xảy ra khi xử lý file.";
  } finally {
    loading.value = false;
  }
};

const onReuploadChange = async (e) => {
  const selectedFile = e.target.files[0];
  if (selectedFile) {
    file.value = selectedFile;
    await processFile();
  }
};

const switchGroup = (idx) => {
  currentGroupIndex.value = idx;
  nextTick(() => {
    renderAllCharts();
  });
};

const destroyChart = (id) => {
  if (charts.value[id]) {
    charts.value[id].destroy();
    delete charts.value[id];
  }
};

const renderAllCharts = () => {
  if (!currentGroup.value) return;
  const active = activeMembers.value;
  const top10 = active.slice(0, 10);
  const months = ["T1", "T2", "T3", "T4"];

  if (activeView.value === "overview") {
    destroyChart("rev");
    destroyChart("conv");
    destroyChart("monthly");

    // Chart Doanh Thu
    const ctxRev = document.getElementById("chart-rev");
    if (ctxRev) {
      charts.value["rev"] = new Chart(ctxRev, {
        type: "bar",
        data: {
          labels: top10.map((m) => getFirstAndLast(m.ten)),
          datasets: [
            {
              label: "Doanh thu (M)",
              data: top10.map((m) => m.rev),
              backgroundColor: top10.map((_, i) => {
                if (i === 0) return "#3b82f6";
                if (i === 1) return "#10b981";
                if (i === 2) return "#818cf8";
                return "#2c3b52";
              }),
              borderRadius: 4,
              borderSkipped: false,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (c) => `${c.raw}M VND` } },
          },
          scales: {
            x: {
              ticks: { color: "#8892a4", font: { size: 10 }, maxRotation: 30 },
              grid: { color: "rgba(255,255,255,0.04)" },
            },
            y: {
              ticks: {
                color: "#8892a4",
                font: { size: 10 },
                callback: (v) => v + "M",
              },
              grid: { color: "rgba(255,255,255,0.06)" },
              border: { display: false },
            },
          },
        },
      });
    }

    // Chart Conversion
    const sortedConv = [...active].sort((a, b) => b.conv - a.conv).slice(0, 10);
    const ctxConv = document.getElementById("chart-conv");
    if (ctxConv) {
      charts.value["conv"] = new Chart(ctxConv, {
        type: "bar",
        data: {
          labels: sortedConv.map((m) => getFirstAndLast(m.ten)),
          datasets: [
            {
              label: "Conv%",
              data: sortedConv.map((m) => m.conv),
              backgroundColor: sortedConv.map((m) =>
                m.conv >= 85 ? "#10b981" : m.conv >= 60 ? "#f59e0b" : "#ef4444",
              ),
              borderRadius: 4,
              borderSkipped: false,
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (c) => `${c.raw}%` } },
          },
          scales: {
            x: {
              min: 0,
              max: 100,
              ticks: {
                color: "#8892a4",
                font: { size: 10 },
                callback: (v) => v + "%",
              },
              grid: { color: "rgba(255,255,255,0.06)" },
              border: { display: false },
            },
            y: {
              ticks: { color: "#8892a4", font: { size: 10 } },
              grid: { display: false },
            },
          },
        },
      });
    }

    // Chart Monthly
    const ctxMonthly = document.getElementById("chart-monthly");
    if (ctxMonthly) {
      const nameColorMap = {
        "Duyên": "#3b82f6",
        "Huy": "#10b981",
        "Nguyên": "#818cf8",
        "Bách": "#f59e0b",
        "Nam": "#06b6d4",
        "Tuấn": "#ef4444",
      };
      const datasets = active.slice(0, 6).map((m, i) => {
        const lastWord = m.ten.split(" ").pop();
        const color = nameColorMap[lastWord] || AVATAR_COLORS[i % AVATAR_COLORS.length];
        return {
          label: lastWord,
          data: m.monthly,
          borderColor: color,
          backgroundColor: "transparent",
          borderWidth: 2.5,
          pointRadius: 4,
          tension: 0.3,
        };
      });
      charts.value["monthly"] = new Chart(ctxMonthly, {
        type: "line",
        data: { labels: months, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              labels: {
                color: "#8892a4",
                font: { size: 10 },
                boxWidth: 10,
                padding: 12,
              },
            },
          },
          scales: {
            x: {
              ticks: { color: "#8892a4", font: { size: 10 } },
              grid: { color: "rgba(255,255,255,0.04)" },
            },
            y: {
              ticks: { color: "#8892a4", font: { size: 10 } },
              grid: { color: "rgba(255,255,255,0.06)" },
              border: { display: false },
            },
          },
        },
      });
    }
  }

  if (activeView.value === "trend") {
    destroyChart("weekly");
    const ctxWeekly = document.getElementById("chart-weekly");
    if (ctxWeekly) {
      const wks = currentGroup.value.weeks.map((w) => w.split("\n")[0]);
      const actWeekly = currentGroup.value.members.filter((x) =>
        x.weekly.some((v) => v > 0),
      );
      const totals = wks.map((_, i) =>
        actWeekly.reduce((s, m) => s + (m.weekly[i] || 0), 0),
      );
      charts.value["weekly"] = new Chart(ctxWeekly, {
        type: "line",
        data: {
          labels: wks,
          datasets: [
            {
              label: "Tổng đơn",
              data: totals,
              borderColor: "#a855f7",
              backgroundColor: "rgba(168, 85, 247, 0.15)",
              fill: true,
              borderWidth: 3,
              pointRadius: 5,
              pointBackgroundColor: "#a855f7",
              tension: 0.3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (c) => `${c.raw} đơn` } },
          },
          scales: {
            x: {
              ticks: { color: "#8892a4", font: { size: 10 } },
              grid: { color: "rgba(255,255,255,0.04)" },
            },
            y: {
              ticks: { color: "#8892a4", font: { size: 10 } },
              grid: { color: "rgba(255,255,255,0.06)" },
              border: { display: false },
            },
          },
        },
      });
    }
  }
};

watch(activeView, () => {
  nextTick(() => {
    renderAllCharts();
  });
});

watch(isFullscreen, () => {
  nextTick(() => {
    setTimeout(() => {
      Object.values(charts.value).forEach((chart) => {
        if (chart) {
          chart.resize();
        }
      });
    }, 150);
  });
});

// Helpers for Trend view
const hmColor = (v, mx) => {
  if (!v) return "#1a1f2e";
  const r = v / mx;
  if (r < 0.2) return "#1a3550";
  if (r < 0.4) return "#1e5a7a";
  if (r < 0.6) return "#1a7faa";
  if (r < 0.8) return "#2196d3";
  return "#4fc3f7";
};
const hmText = (v, mx) => {
  if (!v) return "#555f72";
  return v / mx >= 0.4 ? "#ffffff" : "#9ecfed";
};
const activeTrendMembers = computed(() => {
  if (!currentGroup.value) return [];
  return currentGroup.value.members
    .filter((x) => x.weekly.some((v) => v > 0))
    .sort(
      (a, b) =>
        b.weekly.reduce((s, v) => s + v, 0) -
        a.weekly.reduce((s, v) => s + v, 0),
    );
});
const trendMax = computed(() => {
  const m = activeTrendMembers.value;
  if (!m.length) return 1;
  return Math.max(...m.flatMap((x) => x.weekly), 1);
});

// Alerts
const generatedAlerts = computed(() => {
  if (!currentGroup.value) return [];
  const g = currentGroup.value;
  const alerts = [];
  const noAct = g.members.filter((x) => x.visits === 0);
  if (noAct.length)
    alerts.push({
      type: "err",
      icon: "⛔",
      title: `${noAct.length} NV không có hoạt động`,
      sub: `0 visit: ${noAct.map((x) => x.ten).join(", ")}`,
    });
  const badNote = g.members.filter((x) => x.visits > 0 && x.note_bad_pct >= 80);
  if (badNote.length)
    alerts.push({
      type: "err",
      icon: "📝",
      title: `${badNote.length} NV có note CRM kém >80%`,
      sub: badNote.map((x) => `${x.ten} (${x.note_bad_pct}%)`).join(" · "),
    });
  const lowConv = g.members.filter((x) => x.visits > 100 && x.conv < 30);
  lowConv.forEach((m) =>
    alerts.push({
      type: "err",
      icon: "📉",
      title: `${m.ten}: Conversion ${m.conv}%`,
      sub: `${m.kh_visit} KH thăm, chỉ ${m.kh_buy} KH mua hàng — cần coaching gấp`,
    }),
  );
  const offH = g.members.filter((x) => x.off_hours >= 10);
  offH.forEach((m) =>
    alerts.push({
      type: "warn",
      icon: "🕐",
      title: `${m.ten}: ${m.off_hours} check-in ngoài giờ`,
      sub: "Check-in trước 7h hoặc sau 20h — cần xác minh tính xác thực",
    }),
  );
  const gpsHigh = g.members.filter(
    (x) => x.visits > 0 && x.gps_same / x.visits >= 0.3,
  );
  gpsHigh.forEach((m) =>
    alerts.push({
      type: "warn",
      icon: "📍",
      title: `${m.ten}: GPS trùng ${m.gps_same}/${m.visits} visits (${Math.round((m.gps_same / m.visits) * 100)}%)`,
      sub: "Tọa độ check-in = checkout — nghi vấn không di chuyển thực sự",
    }),
  );
  const stoppedNV = g.members.filter(
    (x) => x.visits > 50 && x.weekly.slice(-4).every((v) => v === 0),
  );
  stoppedNV.forEach((m) =>
    alerts.push({
      type: "warn",
      icon: "⚠️",
      title: `${m.ten}: Ngừng hoạt động`,
      sub: "Không có đơn hàng trong 4 tuần gần nhất",
    }),
  );

  return alerts;
});

const getSparkH = (m) => Math.max(...m.weekly, 1);
const getSparkClass = (v) => (v ? "bg-accent" : "bg-bg3");
const getBadgeHTML = (m) => {
  if (m.visits === 0) return { cls: "badge err", txt: "Không HĐ" };
  if (m.note_bad_pct >= 80) return { cls: "badge err", txt: "Note kém" };
  if (m.conv < 30) return { cls: "badge warn", txt: "Conv thấp" };
  if (m.conv >= 90 && m.rev > 300) return { cls: "badge ok", txt: "Xuất sắc" };
  if (m.rev > 500) return { cls: "badge ok", txt: "DT cao" };
  return { cls: "badge off", txt: "Bình thường" };
};
</script>

<template>
  <div
    class="kpi-dashboard-wrapper"
    :class="{ 'fullscreen-mode': isFullscreen }"
  >
    <!-- UPLOAD STATE -->
    <div
      class="upload-section glass-card mx-auto max-w-2xl mt-12"
      v-if="status !== 'success'"
    >
      <h2 class="text-xl font-bold text-accent mb-2 text-center">
        Module Phân Tích Hành Vi Bán Hàng
      </h2>
      <p class="text-text2 mb-6 text-sm text-center">
        Upload file dữ liệu để sinh báo cáo Dashboard
      </p>

      <div
        class="upload-zone"
        :class="{ active: isDragging, 'has-file': file }"
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
        <div
          v-if="!file"
          class="upload-prompt flex flex-col items-center gap-4 text-text3"
        >
          <Upload size="32" class="text-accent" />
          <p>Kéo thả hoặc nhấn để chọn file .xlsx</p>
        </div>
        <div v-else class="file-selected flex flex-col items-center gap-4">
          <FileSpreadsheet size="32" class="text-green" />
          <div class="text-center">
            <p class="font-bold text-text">{{ file.name }}</p>
            <p class="text-xs text-text3 mt-1">
              {{ (file.size / 1024 / 1024).toFixed(2) }} MB
            </p>
          </div>
          <button
            class="btn-primary"
            @click.stop="processFile"
            :disabled="loading"
          >
            <template v-if="loading">
              <Loader2 class="animate-spin mr-2" size="20" /> Đang xử lý...
            </template>
            <template v-else> Bắt đầu Phân tích </template>
          </button>
        </div>
      </div>
      <div
        v-if="status === 'error'"
        class="mt-4 p-3 bg-red/10 text-red rounded-lg flex items-center gap-2 text-sm"
      >
        <AlertCircle size="18" /> {{ errorMessage }}
      </div>
    </div>

    <!-- DASHBOARD VIEW -->
    <div v-else class="shell fade-in">
      <!-- SIDEBAR -->
      <aside class="sidebar">
        <div class="sidebar-logo">
          <div class="logo-mark">OTC</div>
          <h1>Sales Dashboard</h1>
          <p>T1–T4 / 2026</p>
        </div>

        <div class="nav-section">
          <div class="nav-label">Phân tích</div>
          <div
            class="nav-item"
            :class="{ active: activeView === 'overview' }"
            @click="activeView = 'overview'"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
            </svg>
            Tổng quan
          </div>
          <div
            class="nav-item"
            :class="{ active: activeView === 'nv' }"
            @click="activeView = 'nv'"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            Nhân viên
          </div>
          <div
            class="nav-item"
            :class="{ active: activeView === 'trend' }"
            @click="activeView = 'trend'"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            Xu hướng 8 tuần
          </div>
          <div
            class="nav-item"
            :class="{ active: activeView === 'alerts' }"
            @click="activeView = 'alerts'"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            Cảnh báo
          </div>
        </div>

        <div class="group-switcher">
          <div
            class="text-[10px] text-text3 font-bold uppercase tracking-wider mb-2 px-1"
          >
            Nhóm
          </div>
          <button
            v-for="(g, idx) in rawData.groups"
            :key="g.id"
            class="group-btn"
            :class="{ active: currentGroupIndex === idx }"
            @click="switchGroup(idx)"
          >
            <span class="gname">{{ g.name }}</span>
            <span class="ginfo"
              >{{ g.members.length }} NV ·
              {{ g.members.reduce((s, x) => s + x.rev, 0).toFixed(0) }}M
              VND</span
            >
          </button>
        </div>
      </aside>

      <!-- MAIN CONTENT -->
      <main class="main-content">
        <div class="topbar">
          <div>
            <div class="topbar-title">
              {{ currentGroup.name }} — Báo cáo hành vi bán hàng
            </div>
            <div class="topbar-sub">
              Dữ liệu từ hệ thống CRM & đơn hàng · T1–T4/2026
            </div>
          </div>
          <div class="topbar-right">
            <div class="timestamp">Cập nhật: Mới nhất</div>
            <div class="badge-live">Phân tích thực</div>
            <button class="btn-fullscreen" @click="toggleFullscreen">
              <component
                :is="isFullscreen ? Minimize2 : Maximize2"
                :size="14"
              />
              <span>{{ isFullscreen ? "Thu nhỏ" : "Toàn màn hình" }}</span>
            </button>
            <button
              class="btn-reupload"
              @click="$refs.reInput.click()"
              :disabled="loading"
            >
              <template v-if="loading">
                <Loader2 class="animate-spin" :size="14" />
                <span>Đang xử lý...</span>
              </template>
              <template v-else>
                <Upload :size="14" />
                <span>Đẩy lại Excel</span>
              </template>
            </button>
            <input
              type="file"
              ref="reInput"
              hidden
              accept=".xlsx, .xls"
              @change="onReuploadChange"
            />
          </div>
        </div>

        <div class="content">
          <!-- ── VIEW: OVERVIEW ── -->
          <div v-show="activeView === 'overview'">
            <div class="section-title">Chỉ số tổng hợp</div>
            <div class="kpi-grid">
              <!-- KPI 1 -->
              <div class="kpi-card c-blue">
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm8 11c2.21 0 4 .89 4 2v2"
                    /></svg
                  >Tổng visit
                </div>
                <div class="kpi-value">
                  {{ groupStats.totalVisits.toLocaleString("vi-VN") }}
                </div>
                <div class="kpi-sub neutral">Lượt thăm khách hàng</div>
              </div>
              <!-- KPI 2 -->
              <div class="kpi-card c-green">
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                    /></svg
                  >Doanh thu
                </div>
                <div class="kpi-value">
                  {{ groupStats.totalRev.toFixed(1) }}<span>M</span>
                </div>
                <div class="kpi-sub neutral">VND T1–T4/2026</div>
              </div>
              <!-- KPI 3 -->
              <div class="kpi-card c-teal">
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8"
                    /></svg
                  >Tổng đơn hàng
                </div>
                <div class="kpi-value">
                  {{ groupStats.totalOrders.toLocaleString("vi-VN") }}
                </div>
                <div class="kpi-sub neutral">Đơn duy nhất</div>
              </div>
              <!-- KPI 4 -->
              <div class="kpi-card c-purple">
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"
                    /></svg
                  >KH mua hàng
                </div>
                <div class="kpi-value">
                  {{ groupStats.totalKhBuy.toLocaleString("vi-VN") }}
                </div>
                <div class="kpi-sub neutral">
                  trên {{ groupStats.totalKhVisit }} KH thăm
                </div>
              </div>
              <!-- KPI 5 -->
              <div
                class="kpi-card"
                :class="
                  groupStats.totalKhVisit > 0 &&
                  Math.round(
                    (groupStats.totalKhBuy / groupStats.totalKhVisit) * 100,
                  ) >= 80
                    ? 'c-green'
                    : groupStats.totalKhVisit > 0 &&
                        Math.round(
                          (groupStats.totalKhBuy / groupStats.totalKhVisit) *
                            100,
                        ) >= 60
                      ? 'c-amber'
                      : 'c-red'
                "
              >
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4 12 14.01l-3-3"
                    /></svg
                  >Conversion
                </div>
                <div class="kpi-value">
                  {{
                    groupStats.totalKhVisit > 0
                      ? Math.round(
                          (groupStats.totalKhBuy / groupStats.totalKhVisit) *
                            100,
                        )
                      : 0
                  }}<span>%</span>
                </div>
                <div
                  class="kpi-sub"
                  :class="
                    groupStats.totalKhVisit > 0 &&
                    Math.round(
                      (groupStats.totalKhBuy / groupStats.totalKhVisit) * 100,
                    ) >= 80
                      ? 'up'
                      : groupStats.totalKhVisit > 0 &&
                          Math.round(
                            (groupStats.totalKhBuy / groupStats.totalKhVisit) *
                              100,
                          ) >= 60
                        ? 'warn'
                        : 'down'
                  "
                >
                  Tỷ lệ KH có phát sinh đơn
                </div>
              </div>
              <!-- KPI 6 -->
              <div class="kpi-card c-blue">
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2"
                    /></svg
                  >Avg visit
                </div>
                <div class="kpi-value">
                  {{ groupStats.avgDur.toFixed(1) }}<span>ph</span>
                </div>
                <div class="kpi-sub neutral">Thời gian TB/visit</div>
              </div>
              <!-- KPI 7 -->
              <div
                class="kpi-card"
                :class="
                  groupStats.noteBadPct > 60
                    ? 'c-red'
                    : groupStats.noteBadPct > 30
                      ? 'c-amber'
                      : 'c-green'
                "
              >
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"
                    /></svg
                  >Note CRM kém
                </div>
                <div class="kpi-value">
                  {{ Math.round(groupStats.noteBadPct) }}<span>%</span>
                </div>
                <div
                  class="kpi-sub"
                  :class="
                    groupStats.noteBadPct > 60
                      ? 'down'
                      : groupStats.noteBadPct > 30
                        ? 'warn'
                        : 'up'
                  "
                >
                  Tỷ lệ ghi chú kém
                </div>
              </div>
              <!-- KPI 8 -->
              <div class="kpi-card c-teal">
                <div class="kpi-label">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"
                    /></svg
                  >NV hoạt động
                </div>
                <div class="kpi-value">
                  {{ groupStats.activeCount }}/{{ groupStats.totalCount }}
                </div>
                <div
                  class="kpi-sub"
                  :class="
                    groupStats.totalCount - groupStats.activeCount > 0
                      ? 'warn'
                      : 'up'
                  "
                >
                  {{ groupStats.totalCount - groupStats.activeCount }} NV không
                  có visit
                </div>
              </div>
            </div>

            <div class="section-title">Doanh thu & Conversion</div>
            <div class="charts-row">
              <div class="chart-card">
                <div class="card-head">
                  <div>
                    <div class="card-title">Doanh thu theo nhân viên</div>
                    <div class="card-sub">Triệu VND — T1–T4/2026</div>
                  </div>
                </div>
                <div class="chart-wrap" style="height: 260px">
                  <canvas id="chart-rev"></canvas>
                </div>
              </div>
              <div class="chart-card">
                <div class="card-head">
                  <div>
                    <div class="card-title">Conversion rate</div>
                    <div class="card-sub">% KH thăm → KH mua</div>
                  </div>
                </div>
                <div class="chart-wrap" style="height: 260px">
                  <canvas id="chart-conv"></canvas>
                </div>
              </div>
            </div>

            <div class="charts-row thirds">
              <div class="chart-card">
                <div class="card-head">
                  <div>
                    <div class="card-title">Visit theo tháng</div>
                    <div class="card-sub">T1 → T4/2026</div>
                  </div>
                </div>
                <div class="chart-wrap" style="height: 200px">
                  <canvas id="chart-monthly"></canvas>
                </div>
              </div>
              <div class="chart-card">
                <div class="card-head">
                  <div class="card-title">Chất lượng note CRM</div>
                </div>
                <div>
                  <div
                    v-for="m in [...activeMembers]
                      .sort((a, b) => b.note_bad_pct - a.note_bad_pct)
                      .slice(0, 8)"
                    :key="m.mnv"
                    class="note-row"
                  >
                    <div class="note-meta">
                      <span class="text-[11px] text-text2">{{
                        getFirstAndLast(m.ten)
                      }}</span>
                      <span
                        class="text-[11px]"
                        :style="{
                          color:
                            m.note_bad_pct > 80
                              ? '#f05252'
                              : m.note_bad_pct > 30
                                ? '#f5a623'
                                : '#3ecf8e',
                        }"
                      >
                        {{ m.note_bad_pct }}% kém
                      </span>
                    </div>
                    <div class="note-bar-wrap">
                      <div
                        class="nb-good"
                        :style="{ width: `${100 - m.note_bad_pct}%` }"
                      ></div>
                      <div
                        class="nb-bad"
                        :style="{ width: `${m.note_bad_pct}%` }"
                      ></div>
                    </div>
                  </div>
                  <div class="crm-note-legend-row">
                    <div class="legend-item">
                      <span class="color-swatch swatch-good"></span>
                      <span class="legend-text">Note tốt</span>
                    </div>
                    <div class="legend-item">
                      <span class="color-swatch swatch-bad"></span>
                      <span class="legend-text">Note kém</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── VIEW: NV TABLE ── -->
          <div v-show="activeView === 'nv'">
            <div class="section-title">Bảng chi tiết nhân viên</div>
            <div class="chart-card !p-0">
              <div class="table-wrap">
                <table class="nv-table">
                  <thead>
                    <tr>
                      <th>Nhân viên</th>
                      <th class="r">Visit</th>
                      <th class="r">DT (M)</th>
                      <th class="r">Đơn</th>
                      <th class="r">Conv%</th>
                      <th class="r">Avg visit</th>
                      <th>Note CRM</th>
                      <th class="r">Ngoài giờ</th>
                      <th class="r">GPS ≡</th>
                      <th>Xu hướng</th>
                      <th>Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(m, i) in sortedByRev" :key="m.mnv">
                      <td>
                        <div class="name-cell">
                          <div
                            class="avatar"
                            :style="{
                              background: avatarColor(m.ten, i) + '20',
                              color: avatarColor(m.ten, i),
                            }"
                          >
                            {{ initials(m.ten) }}
                          </div>
                          <div>
                            <div class="font-medium">{{ m.ten }}</div>
                            <div class="text-[10px] text-text3">
                              {{ m.mnv }} · {{ m.tuoi_nghe }}y
                            </div>
                          </div>
                        </div>
                      </td>
                      <td class="r mono">
                        {{ m.visits.toLocaleString("vi-VN") }}
                      </td>
                      <td class="r">
                        <div class="rev-bar-wrap">
                          <div class="rev-bar-bg">
                            <div
                              class="rev-bar-fill"
                              :style="{
                                width: `${Math.round((m.rev / maxRev) * 100)}%`,
                              }"
                            ></div>
                          </div>
                          <span
                            class="font-mono text-xs text-right min-w-[46px]"
                            >{{ m.rev }}M</span
                          >
                        </div>
                      </td>
                      <td class="r mono">{{ m.orders }}</td>
                      <td
                        class="r mono"
                        :style="{
                          color:
                            m.conv >= 85
                              ? '#3ecf8e'
                              : m.conv >= 60
                                ? '#f5a623'
                                : '#f05252',
                        }"
                      >
                        {{ m.conv }}%
                      </td>
                      <td class="r mono">{{ m.avg_dur }}ph</td>
                      <td>
                        <div class="flex items-center gap-1.5">
                          <div
                            class="w-10 h-1.5 rounded-[3px] bg-bg4 overflow-hidden"
                          >
                            <div
                              class="h-full"
                              :style="{
                                width: `${m.note_bad_pct}%`,
                                background:
                                  m.note_bad_pct > 80
                                    ? '#f05252'
                                    : m.note_bad_pct > 30
                                      ? '#f5a623'
                                      : '#3ecf8e',
                              }"
                            ></div>
                          </div>
                          <span
                            class="text-[11px]"
                            :style="{
                              color:
                                m.note_bad_pct > 80
                                  ? '#f05252'
                                  : m.note_bad_pct > 30
                                    ? '#f5a623'
                                    : '#3ecf8e',
                            }"
                            >{{ m.note_bad_pct }}%</span
                          >
                        </div>
                      </td>
                      <td
                        class="r mono"
                        :style="{
                          color:
                            m.off_hours >= 15
                              ? '#f05252'
                              : m.off_hours >= 5
                                ? '#f5a623'
                                : 'var(--text3)',
                        }"
                      >
                        {{ m.off_hours }}
                      </td>
                      <td
                        class="r mono"
                        :style="{
                          color:
                            m.visits > 0 && m.gps_same / m.visits >= 0.3
                              ? '#f05252'
                              : m.gps_same >= 50
                                ? '#f5a623'
                                : 'var(--text3)',
                        }"
                      >
                        {{ m.gps_same }}
                      </td>
                      <td>
                        <div class="spark">
                          <div
                            v-for="(v, vi) in m.weekly"
                            :key="vi"
                            class="spark-b"
                            :class="getSparkClass(v)"
                            :style="{
                              height: v
                                ? Math.max(
                                    3,
                                    Math.round((v / getSparkH(m)) * 22),
                                  ) + 'px'
                                : '2px',
                            }"
                          ></div>
                        </div>
                      </td>
                      <td>
                        <span :class="getBadgeHTML(m).cls">{{
                          getBadgeHTML(m).txt
                        }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- ── VIEW: TREND ── -->
          <div v-show="activeView === 'trend'">
            <div class="section-title">Xu hướng đơn hàng — 8 tuần gần nhất</div>
            <div class="chart-card mb-4">
              <div class="card-head">
                <div>
                  <div class="card-title">Heatmap số đơn theo tuần</div>
                  <div class="card-sub">* W cuối có thể chưa đủ tuần</div>
                </div>
                <div class="heatmap-legend-row">
                  <div class="legend-item">
                    <span class="color-swatch swatch-zero"></span>
                    <span class="legend-text">0</span>
                  </div>
                  <div class="legend-item">
                    <span class="color-swatch" style="background: #1a3550"></span>
                    <span class="legend-text">Thấp</span>
                  </div>
                  <div class="legend-item">
                    <span class="color-swatch" style="background: #1a7faa"></span>
                    <span class="legend-text">TB</span>
                  </div>
                  <div class="legend-item">
                    <span class="color-swatch" style="background: #2196d3"></span>
                    <span class="legend-text">Cao</span>
                  </div>
                  <div class="legend-item">
                    <span class="color-swatch" style="background: #4fc3f7"></span>
                    <span class="legend-text">Đỉnh</span>
                  </div>
                </div>
              </div>
              <div
                class="heatmap-grid"
                :style="{
                  gridTemplateColumns: `140px repeat(${currentGroup.weeks.length}, 1fr)`,
                }"
              >
                <div class="hm-head text-left pl-1">Nhân viên</div>
                <div
                  v-for="w in currentGroup.weeks"
                  :key="w"
                  class="hm-head whitespace-pre-wrap leading-tight"
                >
                  {{ w }}
                </div>

                <template v-for="m in activeTrendMembers" :key="m.mnv">
                  <div class="hm-name">{{ getFirstAndLast(m.ten) }}</div>
                  <div
                    v-for="(v, vi) in m.weekly"
                    :key="vi"
                    class="hm-cell"
                    :style="{
                      background: hmColor(v, trendMax),
                      color: hmText(v, trendMax),
                    }"
                  >
                    {{ v || "—" }}
                  </div>
                </template>
              </div>
            </div>

            <div class="chart-card">
              <div class="card-head">
                <div class="card-title">Xu hướng tổng đơn toàn nhóm</div>
              </div>
              <div class="chart-wrap" style="height: 180px">
                <canvas id="chart-weekly"></canvas>
              </div>
            </div>
          </div>

          <!-- ── VIEW: ALERTS ── -->
          <div v-show="activeView === 'alerts'">
            <div class="section-title">Cảnh báo & phát hiện bất thường</div>
            <div
              v-if="generatedAlerts.length === 0"
              class="text-text3 p-5 text-center"
            >
              Không có cảnh báo nào cho nhóm này.
            </div>
            <div v-else class="space-y-1.5">
              <div
                v-for="(a, i) in generatedAlerts"
                :key="i"
                class="alert-item"
                :class="a.type"
              >
                <div class="alert-icon">{{ a.icon }}</div>
                <div>
                  <div class="alert-title">{{ a.title }}</div>
                  <div class="alert-sub">{{ a.sub }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap");

.kpi-dashboard-wrapper {
  --bg: transparent;
  --bg2: rgba(15, 23, 42, 0.4);
  --bg3: rgba(255, 255, 255, 0.05);
  --bg4: rgba(255, 255, 255, 0.08);
  --border: rgba(255, 255, 255, 0.08);
  --border2: rgba(255, 255, 255, 0.15);
  --text: #f8fafc;
  --text2: #94a3b8;
  --text3: #64748b;
  --accent: #818cf8;
  --green: #10b981;
  --red: #ef4444;
  --amber: #f5a623;
  --purple: #a855f7;
  --teal: #14b8a6;
  --font: "Inter", system-ui, -apple-system, sans-serif;
  --mono: "IBM Plex Mono", monospace;
  --r: 10px;
  --r2: 16px;

  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  min-height: auto;
  margin: 0;
  text-align: left;
}

.heatmap-legend-row .legend-item span.color-swatch.swatch-zero {
  background: #1a1f2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.heatmap-legend-row .legend-item .legend-text {
  font-size: 11px;
  color: #555f72;
  font-weight: 500;
}

.upload-section {
  padding: 3rem;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.upload-zone {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 3rem 2rem;
  transition: all 0.3s;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.2);
}

.upload-zone:hover,
.upload-zone.active {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.05);
}

.btn-primary {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
}

.btn-primary:hover:not(:disabled) {
  transform: scale(1.03);
  box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.5);
}
.btn-primary:disabled {
  background: #475569;
  cursor: not-allowed;
  transform: none;
}

.btn-reupload {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  color: white;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
  transition: all 0.2s ease;
}
.btn-reupload:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(99, 102, 241, 0.45);
}
.btn-reupload:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* LAYOUT */
.shell {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: calc(100vh - 64px);
}

/* SIDEBAR */
.sidebar {
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: calc(100vh - 64px);
  overflow-y: auto;
}
.sidebar-logo {
  padding: 20px 18px 16px;
  border-bottom: 1px solid var(--border);
}
.logo-mark {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 10px;
  font-family: var(--mono);
}
.sidebar-logo h1 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  letter-spacing: -0.01em;
}
.sidebar-logo p {
  font-size: 11px;
  color: var(--text3);
  margin: 2px 0 0 0;
}

.nav-section {
  padding: 14px 12px 6px;
}
.nav-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0 6px;
  margin-bottom: 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 10px;
  border-radius: var(--r);
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
  color: var(--text2);
  margin-bottom: 1px;
}
.nav-item:hover {
  background: var(--bg3);
  color: var(--text);
}
.nav-item.active {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
}
.nav-item svg {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.group-switcher {
  padding: 12px;
  margin-top: auto;
  border-top: 1px solid var(--border);
}
.group-btn {
  display: block;
  width: 100%;
  padding: 8px 12px;
  margin-bottom: 6px;
  border-radius: var(--r);
  border: 1px solid var(--border2);
  background: transparent;
  color: var(--text2);
  font-family: var(--font);
  font-size: 12px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.group-btn:hover {
  background: var(--bg3);
  color: var(--text);
}
.group-btn.active {
  background: rgba(168, 85, 247, 0.15);
  border-color: #c084fc;
  color: #c084fc;
}
.group-btn .gname {
  font-weight: 500;
  display: block;
}
.group-btn .ginfo {
  font-size: 10px;
  color: var(--text3);
  margin-top: 1px;
}
.group-btn.active .ginfo {
  color: rgba(192, 132, 252, 0.8);
}

/* MAIN */
.main-content {
  overflow-y: auto;
  background: transparent;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 14px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.topbar-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text);
}
.topbar-sub {
  font-size: 12px;
  color: var(--text3);
  margin-top: 2px;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.timestamp {
  font-size: 11px;
  color: var(--text3);
  font-family: var(--mono);
}
.badge-live {
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.25);
  color: var(--green);
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
}
.badge-live::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
}

.content {
  padding: 24px 28px;
}
.section-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 12px;
  margin-top: 24px;
}
.section-title:first-child {
  margin-top: 0;
}

/* KPI CARDS */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.kpi-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px 18px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}
.kpi-card:hover {
  border-color: rgba(168, 85, 247, 0.4);
  box-shadow: 0 10px 25px -5px rgba(168, 85, 247, 0.15);
  transform: translateY(-2px);
}
.kpi-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
}
.kpi-card.c-blue::before {
  background: var(--accent);
}
.kpi-card.c-green::before {
  background: var(--green);
}
.kpi-card.c-amber::before {
  background: var(--amber);
}
.kpi-card.c-red::before {
  background: var(--red);
}
.kpi-card.c-purple::before {
  background: var(--purple);
}
.kpi-card.c-teal::before {
  background: var(--teal);
}
.kpi-label {
  font-size: 11px;
  color: var(--text3);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.kpi-label svg {
  width: 13px;
  height: 13px;
}
.kpi-value {
  font-size: 26px;
  font-weight: 300;
  color: var(--text);
  letter-spacing: -0.03em;
  font-family: var(--mono);
  line-height: 1;
}
.kpi-value span {
  font-size: 14px;
  font-weight: 400;
  color: var(--text2);
  margin-left: 2px;
}
.kpi-sub {
  font-size: 11px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.kpi-sub.up {
  color: var(--green);
}
.kpi-sub.down {
  color: var(--red);
}
.kpi-sub.warn {
  color: var(--amber);
}
.kpi-sub.neutral {
  color: var(--text3);
}

/* CHARTS GRID */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.charts-row.thirds {
  grid-template-columns: 2fr 1fr;
}
.chart-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}
.chart-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.card-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
}
.card-sub {
  font-size: 11px;
  color: var(--text3);
}
.chart-wrap {
  position: relative;
}

/* TABLE */
.table-wrap {
  overflow-x: auto;
}
table.nv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
table.nv-table th {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 23, 42, 0.6);
  white-space: nowrap;
}
table.nv-table th.r {
  text-align: right;
}
table.nv-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
  vertical-align: middle;
  white-space: nowrap;
}
table.nv-table tr:last-child td {
  border-bottom: none;
}
table.nv-table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}
table.nv-table td.r {
  text-align: right;
  font-family: var(--mono);
}
table.nv-table td.mono {
  font-family: var(--mono);
}
.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
}
.rev-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rev-bar-bg {
  flex: 1;
  height: 4px;
  background: var(--bg4);
  border-radius: 2px;
  min-width: 60px;
}
.rev-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--accent);
}

/* BADGES & SPARK */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}
.badge.ok {
  background: rgba(62, 207, 142, 0.12);
  color: var(--green);
  border: 1px solid rgba(62, 207, 142, 0.2);
}
.badge.warn {
  background: rgba(245, 166, 35, 0.12);
  color: var(--amber);
  border: 1px solid rgba(245, 166, 35, 0.2);
}
.badge.err {
  background: rgba(240, 82, 82, 0.12);
  color: var(--red);
  border: 1px solid rgba(240, 82, 82, 0.2);
}
.badge.off {
  background: rgba(136, 146, 164, 0.12);
  color: var(--text3);
  border: 1px solid var(--border);
}
.spark {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 22px;
}
.spark-b {
  width: 5px;
  border-radius: 1px 1px 0 0;
  flex-shrink: 0;
}

/* HEATMAP */
.heatmap-grid {
  display: grid;
  gap: 2px;
}
.hm-cell {
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 500;
  font-family: var(--mono);
  min-height: 26px;
  transition: opacity 0.15s;
}
.hm-cell:hover {
  opacity: 0.8;
}
.hm-head {
  font-size: 10px;
  color: var(--text3);
  text-align: center;
  padding: 3px 0;
}
.hm-name {
  font-size: 11px;
  color: var(--text2);
  padding: 3px 4px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

/* NOTE BARS */
.note-row {
  margin-bottom: 10px;
}
.note-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  margin-bottom: 4px;
}
.note-bar-wrap {
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
  background: var(--bg4);
  display: flex;
}
.nb-good {
  background: var(--green);
}
.nb-bad {
  background: var(--red);
}

/* ALERTS */
.alert-item {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--r);
  border-left: 3px solid;
}
.alert-item.err {
  background: rgba(240, 82, 82, 0.08);
  border-color: var(--red);
}
.alert-item.warn {
  background: rgba(245, 166, 35, 0.08);
  border-color: var(--amber);
}
.alert-item.info {
  background: rgba(79, 142, 247, 0.08);
  border-color: var(--accent);
}
.alert-icon {
  font-size: 15px;
  flex-shrink: 0;
  margin-top: 1px;
}
.alert-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
}
.alert-sub {
  font-size: 11px;
  color: var(--text3);
  margin-top: 2px;
}

.fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Extra utility colors for dynamic binding */
.bg-bg3 {
  background-color: var(--bg3);
}
.bg-accent {
  background-color: var(--accent);
}

/* FULLSCREEN MODE styles */
.kpi-dashboard-wrapper.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 99999;
  background: radial-gradient(circle at top left, #1e293b, #0f172a);
  margin: 0;
  padding: 0;
}

.kpi-dashboard-wrapper.fullscreen-mode .shell {
  height: 100vh;
  min-height: 100vh;
}

.kpi-dashboard-wrapper.fullscreen-mode .sidebar {
  height: 100vh;
}

.btn-fullscreen {
  background: rgba(255, 255, 255, 0.05);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.4rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.2s ease;
}
.btn-fullscreen:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.chart-wrap canvas {
  width: 100% !important;
  height: 100% !important;
}

/* Custom Scoped Legends */
.heatmap-legend-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.heatmap-legend-row .legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.heatmap-legend-row .legend-item span.color-swatch {
  width: 9px;
  height: 9px;
  border-radius: 1.5px;
  flex-shrink: 0;
  display: inline-block;
}
.heatmap-legend-row .legend-item span.color-swatch.swatch-zero {
  background: #1a1f2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.heatmap-legend-row .legend-item .legend-text {
  font-size: 11px;
  color: #555f72;
  font-weight: 500;
}

.crm-note-legend-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.crm-note-legend-row .legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.crm-note-legend-row .legend-item span.color-swatch {
  width: 9px;
  height: 9px;
  border-radius: 1.5px;
  flex-shrink: 0;
  display: inline-block;
}
.crm-note-legend-row .legend-item span.color-swatch.swatch-good {
  background: #10b981;
}
.crm-note-legend-row .legend-item span.color-swatch.swatch-bad {
  background: #ef4444;
}
.crm-note-legend-row .legend-item .legend-text {
  font-size: 11px;
  color: #555f72;
  font-weight: 500;
}
</style>
