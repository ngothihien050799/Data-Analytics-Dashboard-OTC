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
const conversionSearch = ref("");
const conversionSelectedMnv = ref("");

const filteredConversionDetails = computed(() => {
  const g = currentGroup.value;
  if (!g || !g.conversion_module || !g.conversion_module.conversion_details)
    return [];

  let list = g.conversion_module.conversion_details;

  if (conversionSelectedMnv.value) {
    const selectedMember = g.members.find(
      (m) => m.mnv === conversionSelectedMnv.value,
    );
    if (selectedMember) {
      const name = selectedMember.ten;
      list = list.filter((item) => item.nv_names.includes(name));
    }
  }

  const query = conversionSearch.value.trim().toLowerCase();
  if (query) {
    list = list.filter((item) => {
      return (
        item.khcn_name.toLowerCase().includes(query) ||
        item.ma_kh.toLowerCase().includes(query) ||
        item.ten_kh.toLowerCase().includes(query) ||
        item.nv_names.toLowerCase().includes(query) ||
        (item.base_order_ids &&
          item.base_order_ids.some((id) => id.toLowerCase().includes(query)))
      );
    });
  }

  return list;
});

const charts = ref({});
const processedAt = ref("");
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
    Duyên: "#3b82f6",
    Huy: "#10b981",
    Nguyên: "#818cf8",
    Bách: "#f59e0b",
    Nam: "#06b6d4",
    Tuấn: "#ef4444",
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

const compressFile = async (file) => {
  const arrayBuffer = await file.arrayBuffer();
  const stream = new Blob([arrayBuffer]).stream();
  const compressedStream = stream.pipeThrough(new CompressionStream("gzip"));
  const compressedBlob = await new Response(compressedStream).blob();
  return compressedBlob;
};

const processFile = async () => {
  if (!file.value) return;
  loading.value = true;
  status.value = "uploading";
  errorMessage.value = "";

  try {
    let uploadBlob = file.value;
    let useCompression = false;

    // Compress if file > 3MB to stay under Vercel's 4.5MB limit
    if (file.value.size > 3 * 1024 * 1024) {
      uploadBlob = await compressFile(file.value);
      useCompression = true;
    }

    const formData = new FormData();
    formData.append("file", uploadBlob, file.value.name);

    const headers = {};
    if (useCompression) {
      headers["x-content-encoding"] = "gzip";
      headers["x-file-name"] = file.value.name;
    }

    const response = await axios.post("/process_hanh_vi", formData, {
      headers,
    });
    rawData.value = response.data;
    status.value = "success";
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    processedAt.value = `${pad(now.getHours())}:${pad(now.getMinutes())} ${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${String(now.getFullYear()).slice(-2)}`;
    currentGroupIndex.value = 0;
    activeView.value = "overview";
    await nextTick();
    triggerRender();
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
    triggerRender();
  });
};

const destroyChart = (id, canvasId = null) => {
  if (charts.value[id]) {
    try {
      charts.value[id].destroy();
    } catch (e) {
      console.warn("Error destroying chart instance", id, e);
    }
    delete charts.value[id];
  }
  if (canvasId) {
    const el = document.getElementById(canvasId);
    if (el) {
      const instance = Chart.getChart(el);
      if (instance) {
        try {
          instance.destroy();
        } catch (e) {
          console.warn("Error destroying orphaned chart", canvasId, e);
        }
      }
    }
  }
};

const selectedEmployeeId = ref("");
const expandedAlerts = ref({});

// Set initial selectedEmployeeId when data or group changes
watch(
  [currentGroupIndex, rawData],
  () => {
    if (currentGroup.value && currentGroup.value.nv_info) {
      const keys = Object.keys(currentGroup.value.nv_info);
      if (keys.length > 0) {
        selectedEmployeeId.value = keys[0];
      } else {
        selectedEmployeeId.value = "";
      }
    } else {
      selectedEmployeeId.value = "";
    }
  },
  { immediate: true },
);

const renderNVSpChart = () => {
  destroyChart("nv-sp", "chart-nv-sp");
  const pd = currentGroup.value;
  if (!pd || !selectedEmployeeId.value || !pd.nv_top5) return;

  const allProds = pd.nv_top5[selectedEmployeeId.value] || [];
  if (!allProds.length) return;

  const ctxNvSp = document.getElementById("chart-nv-sp");
  if (ctxNvSp) {
    const COLS = [
      "#3b82f6",
      "#10b981",
      "#f59e0b",
      "#a855f7",
      "#14b8a6",
      "#64748b",
    ];
    const top5 = allProds.slice(0, 5);
    const rest = allProds.slice(5);
    const restRev = rest.reduce((s, p) => s + p.rev, 0);
    const totalNVRev = allProds.reduce((s, p) => s + p.rev, 0);

    const chartLabels = top5.map((p) => p.ten);
    const chartData = top5.map((p) => p.rev);
    const chartColors = COLS.slice(0, top5.length);
    if (rest.length > 0 && restRev > 0) {
      chartLabels.push(`Khác (${rest.length} SP)`);
      chartData.push(parseFloat(restRev.toFixed(1)));
      chartColors.push(COLS[5]);
    }

    charts.value["nv-sp"] = new Chart(ctxNvSp, {
      type: "doughnut",
      data: {
        labels: chartLabels,
        datasets: [
          {
            data: chartData,
            backgroundColor: chartColors,
            borderWidth: 2,
            borderColor: "#0f172a",
            hoverOffset: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "60%",
        animation: {
          duration: 1500,
          easing: "easeOutExpo",
          delay: (context) =>
            context.type === "data" && context.mode === "default"
              ? context.dataIndex * 100
              : 0,
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (c) =>
                `${c.raw}M VND (${Math.round((c.raw / (totalNVRev || 1)) * 100)}%)`,
            },
          },
        },
      },
    });
  }
};

// Watch selectedEmployeeId and render the chart
watch(selectedEmployeeId, () => {
  if (activeView.value === "products") {
    nextTick(() => {
      renderNVSpChart();
    });
  }
});

const renderAllCharts = () => {
  if (!currentGroup.value) return;

  // Unified cleanup of charts not needed in current view
  if (activeView.value !== "overview") {
    destroyChart("rev", "chart-rev");
    destroyChart("conv", "chart-conv");
    destroyChart("monthly", "chart-monthly");
  }
  if (activeView.value !== "trend") {
    destroyChart("weekly", "chart-weekly");
    destroyChart("weekly-rev", "chart-weekly-rev");
  }
  if (activeView.value !== "products") {
    destroyChart("sp-bar", "chart-sp-bar");
    destroyChart("kenh", "chart-kenh");
    destroyChart("nv-sp", "chart-nv-sp");
  }

  const active = activeMembers.value;
  const top10 = active.slice(0, 10);
  const months = ["T1", "T2", "T3", "T4"];

  if (activeView.value === "overview") {
    // Chart Doanh Thu
    destroyChart("rev", "chart-rev");
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
          animation: {
            duration: 1500,
            easing: "easeOutExpo",
            delay: (context) =>
              context.type === "data" && context.mode === "default"
                ? context.dataIndex * 50
                : 0,
          },
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
    destroyChart("conv", "chart-conv");
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
          animation: {
            duration: 1500,
            easing: "easeOutExpo",
            delay: (context) =>
              context.type === "data" && context.mode === "default"
                ? context.dataIndex * 50
                : 0,
          },
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
    destroyChart("monthly", "chart-monthly");
    const ctxMonthly = document.getElementById("chart-monthly");
    if (ctxMonthly) {
      const nameColorMap = {
        Duyên: "#3b82f6",
        Huy: "#10b981",
        Nguyên: "#818cf8",
        Bách: "#f59e0b",
        Nam: "#06b6d4",
        Tuấn: "#ef4444",
      };
      const datasets = active.slice(0, 6).map((m, i) => {
        const lastWord = m.ten.split(" ").pop();
        const color =
          nameColorMap[lastWord] || AVATAR_COLORS[i % AVATAR_COLORS.length];
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
          animation: {
            duration: 1500,
            easing: "easeOutExpo",
            delay: (context) =>
              context.type === "data" && context.mode === "default"
                ? context.datasetIndex * 100 + context.dataIndex * 30
                : 0,
          },
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
    destroyChart("weekly", "chart-weekly");
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
          animation: {
            duration: 1500,
            easing: "easeOutExpo",
            delay: (context) =>
              context.type === "data" && context.mode === "default"
                ? context.dataIndex * 50
                : 0,
          },
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

    destroyChart("weekly-rev", "chart-weekly-rev");
    const ctxWeeklyRev = document.getElementById("chart-weekly-rev");
    if (ctxWeeklyRev) {
      const wks = currentGroup.value.weeks.map((w) => w.split("\n")[0]);
      const actWeekly = currentGroup.value.members.filter(
        (x) => x.weekly_rev && x.weekly_rev.some((v) => v > 0),
      );
      const totalsRev = wks.map((_, i) =>
        actWeekly.reduce((s, m) => s + (m.weekly_rev[i] || 0), 0),
      );
      charts.value["weekly-rev"] = new Chart(ctxWeeklyRev, {
        type: "line",
        data: {
          labels: wks,
          datasets: [
            {
              label: "Doanh số toàn nhóm (M VND)",
              data: totalsRev,
              borderColor: "#10b981",
              backgroundColor: "rgba(16, 185, 129, 0.15)",
              fill: true,
              borderWidth: 3,
              pointRadius: 5,
              pointBackgroundColor: "#10b981",
              tension: 0.3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 1500,
            easing: "easeOutExpo",
            delay: (context) =>
              context.type === "data" && context.mode === "default"
                ? context.dataIndex * 50
                : 0,
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: { label: (c) => `${c.raw.toFixed(2)} M VND` },
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

  if (activeView.value === "products") {
    const pd = currentGroup.value;
    if (!pd || !pd.products || !pd.products.length) return;

    // 1. Chart SP Bar
    destroyChart("sp-bar", "chart-sp-bar");
    const ctxSpBar = document.getElementById("chart-sp-bar");
    if (ctxSpBar) {
      const top8 = pd.products.slice(0, 8);
      const COLORS_SP = [
        "#3b82f6",
        "#10b981",
        "#a855f7",
        "#f59e0b",
        "#14b8a6",
        "#ef4444",
        "#ec4899",
        "#6366f1",
      ];
      charts.value["sp-bar"] = new Chart(ctxSpBar, {
        type: "bar",
        data: {
          labels: top8.map((p) =>
            p.ten.length > 28 ? p.ten.slice(0, 26) + "…" : p.ten,
          ),
          datasets: [
            {
              label: "Doanh thu (M)",
              data: top8.map((p) => p.rev),
              backgroundColor: top8.map(
                (_, i) => COLORS_SP[i % COLORS_SP.length] + "cc",
              ),
              borderColor: top8.map((_, i) => COLORS_SP[i % COLORS_SP.length]),
              borderWidth: 1,
              borderRadius: 4,
              borderSkipped: false,
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 1500,
            easing: "easeOutExpo",
            delay: (context) =>
              context.type === "data" && context.mode === "default"
                ? context.dataIndex * 50
                : 0,
          },
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (c) => `${c.raw}M VND` } },
          },
          scales: {
            x: {
              ticks: {
                color: "#8892a4",
                font: { size: 10 },
                callback: (v) => v + "M",
              },
              grid: { color: "rgba(255,255,255,0.06)" },
              border: { display: false },
            },
            y: {
              ticks: { color: "#d0d8ea", font: { size: 10 } },
              grid: { display: false },
            },
          },
        },
      });
    }

    // 2. Chart Kenh Doughnut
    destroyChart("kenh", "chart-kenh");
    const ctxKenh = document.getElementById("chart-kenh");
    if (ctxKenh && pd.kenh && pd.kenh.length) {
      const top5k = pd.kenh.slice(0, 5);
      const KENH_COLORS = [
        "#3b82f6",
        "#10b981",
        "#f59e0b",
        "#a855f7",
        "#ef4444",
      ];
      charts.value["kenh"] = new Chart(ctxKenh, {
        type: "doughnut",
        data: {
          labels: top5k.map((k) => k.kenh),
          datasets: [
            {
              data: top5k.map((k) => k.rev),
              backgroundColor: KENH_COLORS,
              borderWidth: 2,
              borderColor: "#0f172a",
              hoverOffset: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "65%",
          animation: {
            duration: 1500,
            easing: "easeOutExpo",
            delay: (context) =>
              context.type === "data" && context.mode === "default"
                ? context.dataIndex * 100
                : 0,
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (c) =>
                  `${c.label}: ${c.raw}M (${top5k[c.dataIndex]?.pct}%)`,
              },
            },
          },
        },
      });
    }

    // 3. Chart NV SP Doughnut
    renderNVSpChart();
  }
};

const renderTimeout = ref(null);

const triggerRender = () => {
  if (renderTimeout.value) {
    clearTimeout(renderTimeout.value);
  }
  renderTimeout.value = setTimeout(() => {
    renderAllCharts();
    renderTimeout.value = null;
  }, 100);
};

watch(activeView, () => {
  nextTick(() => {
    triggerRender();
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

// Helpers for Weekly Revenue Heatmap
const hmColorRev = (v, mx) => {
  if (!v) return "#1a1f2e";
  const r = v / mx;
  if (r < 0.2) return "#064e3b"; // dark green
  if (r < 0.4) return "#047857";
  if (r < 0.6) return "#10b981";
  if (r < 0.8) return "#34d399";
  return "#6ee7b7"; // light mint green
};
const hmTextRev = (v, mx) => {
  if (!v) return "#555f72";
  return v / mx >= 0.4 ? "#ffffff" : "#a7f3d0";
};
const activeTrendMembersRev = computed(() => {
  if (!currentGroup.value) return [];
  return currentGroup.value.members
    .filter((x) => x.weekly_rev && x.weekly_rev.some((v) => v > 0))
    .sort(
      (a, b) =>
        b.weekly_rev.reduce((s, v) => s + v, 0) -
        a.weekly_rev.reduce((s, v) => s + v, 0),
    );
});
const trendMaxRev = computed(() => {
  const m = activeTrendMembersRev.value;
  if (!m.length) return 1;
  return Math.max(...m.flatMap((x) => x.weekly_rev || []), 1);
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
  const offH = g.members.filter((x) => x.off_hours > 0);
  offH.forEach((m) =>
    alerts.push({
      id: "off-" + m.mnv,
      type: "warn",
      icon: "🕐",
      title: `${m.ten}: ${m.off_hours} check-in ngoài giờ`,
      sub: "Check-in trước 7h hoặc sau 18h — cần xác minh tính xác thực",
      details: m.off_hours_list || [],
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

const guideSearch = ref("");
const guideCategories = [
  {
    id: "kpis",
    title: "Chỉ số hiệu năng (KPIs)",
    items: [
      {
        name: "Doanh số (Revenue)",
        desc: "Tổng doanh thu bán hàng thực tế được ghi nhận cho nhóm hoặc cá nhân TDV (tính theo đơn vị Triệu VND - M VND).",
        formula: "Tổng doanh thu đơn hàng thành công",
      },
      {
        name: "Khách hàng thăm (Visits)",
        desc: "Tổng số lượng khách hàng độc bản (Mã KH) được nhân viên thực hiện check-in viếng thăm trong kỳ.",
        formula: "Count(Unique Mã KH check-in)",
      },
      {
        name: "Khách hàng mua (Buyers)",
        desc: "Số lượng khách hàng thực tế có phát sinh đơn hàng thành công trong kỳ.",
        formula: "Count(Unique Mã KH mua hàng)",
      },
      {
        name: "Tỷ lệ chuyển đổi (Conversion Rate)",
        desc: "Tỷ lệ chuyển đổi từ khách hàng được viếng thăm sang khách hàng mua hàng thực tế.",
        formula: "(Khách hàng mua / Khách hàng thăm) * 100",
      },
    ],
  },
  {
    id: "behavior",
    title: "Chỉ số hành vi & Cảnh báo",
    items: [
      {
        name: "Note CRM kém (Bad CRM Note)",
        desc: "Tỷ lệ các cuộc gọi ghi chú CRM sơ sài, quá ngắn (dưới 15 ký tự) hoặc ghi chú không có ý nghĩa.",
        formula: "(Số note ngắn / Tổng số visit) * 100",
      },
      {
        name: "Check-in ngoài giờ (Out-of-Hours)",
        desc: "Lượt viếng thăm khách hàng được thực hiện ngoài khung giờ hành chính tiêu chuẩn (Trước 7:00 hoặc Sau 18:00).",
        formula: "Thời gian check-in < 7h00 hoặc >= 18h00",
      },

      {
        name: "Ngừng hoạt động (Inactive Alert)",
        desc: "Hệ thống tự động phát hiện nhân viên có lịch sử kinh doanh tích cực nhưng không phát sinh bất kỳ đơn hàng nào trong 4 tuần liên tục gần nhất.",
        formula: "Doanh số 4 tuần gần nhất = 0",
      },
    ],
  },
  {
    id: "behavior1",
    title: "Tỷ lệ chuyển đổi",
    items: [
      {
        name: "Tỷ lệ khai phá thành công",
        desc: "",
        formula: "(Số khách hàng khai phá / Số call đã check) * 100",
      },
      {
        name: "Tỷ lệ chuyển đổi",
        desc: "Hiệu quả bán hàng",
        formula: "(Đơn chốt thành công / Số khách hàng khai phá) * 100",
      },

      {
        name: "Tỷ lệ chốt tổng",
        desc: "Hiệu quả toàn pipeline",
        formula: "(Đơn chốt thành công / Số call đã check) * 100",
      },
    ],
  },
];

const filteredGuide = computed(() => {
  if (!guideSearch.value) return guideCategories;
  const q = guideSearch.value.toLowerCase().trim();
  return guideCategories
    .map((cat) => {
      const items = cat.items.filter(
        (it) =>
          it.name.toLowerCase().includes(q) ||
          it.desc.toLowerCase().includes(q) ||
          (it.formula && it.formula.toLowerCase().includes(q)),
      );
      return { ...cat, items };
    })
    .filter((cat) => cat.items.length > 0);
});

const getMostCoveredProductCount = () => {
  if (
    !currentGroup.value ||
    !currentGroup.value.products ||
    !currentGroup.value.products.length
  )
    return 0;
  return Math.max(...currentGroup.value.products.map((p) => p.diem_ban));
};

const getMostCoveredProductTen = () => {
  if (
    !currentGroup.value ||
    !currentGroup.value.products ||
    !currentGroup.value.products.length
  )
    return "";
  const maxD = getMostCoveredProductCount();
  const prod = currentGroup.value.products.find((p) => p.diem_ban === maxD);
  return prod ? prod.ten : "";
};

const getTop3SharePct = () => {
  if (
    !currentGroup.value ||
    !currentGroup.value.products ||
    !currentGroup.value.products.length
  )
    return 0;
  const total = currentGroup.value.products.reduce((s, p) => s + p.rev, 0);
  if (total === 0) return 0;
  const top3 = currentGroup.value.products
    .slice(0, 3)
    .reduce((s, p) => s + p.rev, 0);
  return Math.round((top3 / total) * 100);
};

const getTopProductRev = () => {
  if (
    !currentGroup.value ||
    !currentGroup.value.products ||
    !currentGroup.value.products.length
  )
    return 0;
  return currentGroup.value.products[0].rev;
};

const getTopProductTen = () => {
  if (
    !currentGroup.value ||
    !currentGroup.value.products ||
    !currentGroup.value.products.length
  )
    return "";

  return currentGroup.value.products[0].ten;
};

const getMaxProductRev = () => {
  if (
    !currentGroup.value ||
    !currentGroup.value.products ||
    !currentGroup.value.products.length
  )
    return 1;
  return currentGroup.value.products[0].rev;
};

const getActiveNVCount = () => {
  if (!currentGroup.value || !currentGroup.value.members) return 1;
  return currentGroup.value.members.filter((x) => x.visits > 0).length || 1;
};

const getPhuNVColor = (count) => {
  const pct = Math.round((count / getActiveNVCount()) * 100);
  return pct >= 70 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";
};

const getMaxMonthlyVal = (arr) => {
  if (!arr || !arr.length) return 1;
  return Math.max(...arr, 0.1);
};

const getProductBadge = (p) => {
  const totalNV = getActiveNVCount();
  const phuNV = Math.round((p.nv_count / totalNV) * 100);
  const mTrend = p.monthly;
  const lateRev = (mTrend[2] || 0) + (mTrend[3] || 0);
  const earlyRev = (mTrend[0] || 0) + (mTrend[1] || 0);
  const trend =
    earlyRev === 0
      ? "Mới"
      : lateRev > earlyRev * 1.2
        ? "Tăng"
        : lateRev < earlyRev * 0.8
          ? "Giảm"
          : "Ổn định";

  if (p.diem_ban >= 300) return { cls: "badge ok", txt: "Phủ rộng" };
  if (p.nv_count < 5) return { cls: "badge warn", txt: "Ít NV bán" };
  if (trend === "Giảm") return { cls: "badge err", txt: "Đang giảm" };
  return { cls: "badge off", txt: "Bình thường" };
};

const getNVSumRev = (arr) => {
  if (!arr || !arr.length) return 1;
  return arr.reduce((s, p) => s + p.rev, 0);
};

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
          <div class="logo-mark">OTC/ETC/PS/GP</div>
          <h1>Sales Dashboard</h1>
          <p>{{ rawData?.date_range || "" }}</p>
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
            :class="{ active: activeView === 'products' }"
            @click="activeView = 'products'"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
              />
              <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
              <line x1="12" y1="22.08" x2="12" y2="12" />
            </svg>
            Sản phẩm
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
          <div
            class="nav-item"
            :class="{ active: activeView === 'conversion' }"
            @click="activeView = 'conversion'"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
            Chuyển đổi
          </div>
          <div
            class="nav-item"
            :class="{ active: activeView === 'guide' }"
            @click="activeView = 'guide'"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path
                d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"
              />
            </svg>
            Cẩm nang
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
              {{ currentGroup.name }}
            </div>
            <div class="topbar-sub">
              Dữ liệu từ hệ thống CRM & đơn hàng ·
              {{ rawData?.date_range || "" }}
            </div>
          </div>
          <div class="topbar-right">
            <div class="timestamp">{{ processedAt || "" }}</div>
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
          <div v-if="activeView === 'overview'">
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
                <div class="kpi-sub neutral">
                  VND {{ rawData?.date_range || "" }}
                </div>
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
                    <div class="card-sub">{{ rawData?.date_range || "" }}</div>
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
          <div v-if="activeView === 'nv'">
            <div class="section-title">Bảng chi tiết nhân viên</div>
            <div class="chart-card !p-0">
              <div class="table-wrap scrollable-x-nv">
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
                            <div
                              style="
                                font-size: 11px;
                                color: #555f72;
                                font-weight: normal;
                              "
                            >
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
          <div v-if="activeView === 'trend'">
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
                    <span
                      class="color-swatch"
                      style="background: #1a3550"
                    ></span>
                    <span class="legend-text">Thấp</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #1a7faa"
                    ></span>
                    <span class="legend-text">TB</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #2196d3"
                    ></span>
                    <span class="legend-text">Cao</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #4fc3f7"
                    ></span>
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

            <!-- Heatmap Doanh Số Theo Tuần -->
            <div class="chart-card mb-4 mt-4">
              <div class="card-head">
                <div>
                  <div class="card-title">
                    Heatmap doanh số theo tuần (Triệu VND)
                  </div>
                  <div class="card-sub">
                    * Doanh thu thực tế phát sinh theo tuần
                  </div>
                </div>
                <div class="heatmap-legend-row">
                  <div class="legend-item">
                    <span class="color-swatch swatch-zero"></span>
                    <span class="legend-text">0</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #064e3b"
                    ></span>
                    <span class="legend-text">Thấp</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #047857"
                    ></span>
                    <span class="legend-text">TB</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #10b981"
                    ></span>
                    <span class="legend-text">Khá</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #34d399"
                    ></span>
                    <span class="legend-text">Cao</span>
                  </div>
                  <div class="legend-item">
                    <span
                      class="color-swatch"
                      style="background: #6ee7b7"
                    ></span>
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

                <template v-for="m in activeTrendMembersRev" :key="m.mnv">
                  <div class="hm-name">{{ getFirstAndLast(m.ten) }}</div>
                  <div
                    v-for="(v, vi) in m.weekly_rev"
                    :key="vi"
                    class="hm-cell"
                    :style="{
                      background: hmColorRev(v, trendMaxRev),
                      color: hmTextRev(v, trendMaxRev),
                    }"
                  >
                    {{ v ? v.toFixed(1) : "—" }}
                  </div>
                </template>
              </div>
            </div>

            <div class="charts-row">
              <div class="chart-card">
                <div class="card-head">
                  <div class="card-title">Xu hướng tổng đơn toàn nhóm</div>
                </div>
                <div class="chart-wrap" style="height: 180px">
                  <canvas id="chart-weekly"></canvas>
                </div>
              </div>

              <div class="chart-card">
                <div class="card-head">
                  <div class="card-title">Xu hướng doanh số toàn nhóm</div>
                </div>
                <div class="chart-wrap" style="height: 180px">
                  <canvas id="chart-weekly-rev"></canvas>
                </div>
              </div>
            </div>
          </div>

          <!-- ── VIEW: PRODUCTS ── -->
          <div v-if="activeView === 'products'">
            <div class="section-title">Tổng quan danh mục sản phẩm</div>
            <div
              class="kpi-grid mb-4"
              style="grid-template-columns: repeat(4, 1fr)"
            >
              <!-- Card 1 -->
              <div class="kpi-card c-blue">
                <div class="kpi-label">Tổng SKU bán</div>
                <div class="kpi-value">
                  {{ currentGroup.products?.length || 0 }}<span> sản phẩm</span>
                </div>
                <div class="kpi-sub neutral">
                  Trong kỳ {{ rawData?.date_range || "" }}
                </div>
              </div>
              <!-- Card 2 -->
              <div class="kpi-card c-teal">
                <div class="kpi-label">SP phủ nhất</div>
                <div class="kpi-value">
                  {{ getMostCoveredProductCount() }}<span> điểm bán</span>
                </div>
                <div class="kpi-sub neutral">
                  {{ getMostCoveredProductTen() }}
                </div>
              </div>
              <!-- Card 3 -->
              <div class="kpi-card c-amber">
                <div class="kpi-label">Top 3 SP % DT</div>
                <div class="kpi-value">
                  {{ getTop3SharePct() }}<span>% DT</span>
                </div>
                <div
                  class="kpi-sub"
                  :class="getTop3SharePct() > 60 ? 'down' : 'up'"
                >
                  {{
                    getTop3SharePct() > 60
                      ? "⚠ Rủi ro tập trung Cao"
                      : "✅ Rủi ro tập trung Vừa phải"
                  }}
                </div>
              </div>
              <!-- Card 4 -->
              <div class="kpi-card c-green">
                <div class="kpi-label">SP dẫn đầu</div>
                <div class="kpi-value">
                  {{ getTopProductRev() }}<span> M VND</span>
                </div>
                <div class="kpi-sub neutral">{{ getTopProductTen() }}</div>
              </div>
            </div>

            <div class="section-title">Doanh thu theo sản phẩm & kênh bán</div>
            <div class="charts-row thirds mb-4">
              <div class="chart-card flex-[2]">
                <div class="card-head">
                  <div>
                    <div class="card-title">Top sản phẩm theo doanh thu</div>
                    <div class="card-sub">Triệu VND · T1–T4/2026</div>
                  </div>
                </div>
                <div class="chart-wrap" style="height: 320px">
                  <canvas id="chart-sp-bar"></canvas>
                </div>
              </div>
              <div class="chart-card">
                <div class="card-head">
                  <div class="card-title">Cơ cấu kênh bán</div>
                </div>
                <div class="chart-wrap" style="height: 180px">
                  <canvas id="chart-kenh"></canvas>
                </div>
                <div style="margin-top: 12px">
                  <div
                    v-for="(k, i) in currentGroup.kenh?.slice(0, 5) || []"
                    :key="k.kenh"
                    style="
                      display: flex;
                      align-items: center;
                      justify-content: space-between;
                      margin-bottom: 7px;
                      font-size: 11px;
                    "
                  >
                    <span style="display: flex; align-items: center; gap: 6px">
                      <span
                        style="
                          width: 8px;
                          height: 8px;
                          border-radius: 2px;
                          display: inline-block;
                        "
                        :style="{
                          background: [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#a855f7',
                            '#ef4444',
                          ][i % 5],
                        }"
                      ></span>
                      <span class="text-text2">{{ k.kenh }}</span>
                    </span>
                    <span class="font-mono text-text">
                      {{ k.rev }}M
                      <span class="text-text3">({{ k.pct }}%)</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="section-title">Bảng chi tiết sản phẩm</div>
            <div class="chart-card !p-0 mb-4" style="margin-bottom: 16px">
              <div class="table-wrap scrollable-y">
                <table class="nv-table">
                  <thead>
                    <tr>
                      <th
                        style="
                          width: 42px;
                          min-width: 42px;
                          max-width: 42px;
                          text-align: center;
                          padding: 10px 4px;
                        "
                      >
                        #
                      </th>
                      <th>Tên sản phẩm</th>
                      <th class="r">DT (M)</th>
                      <th class="r">SL bán</th>
                      <th class="r">Điểm bán</th>
                      <th class="r">NV bán</th>
                      <th class="r">Độ phủ NV</th>
                      <th>Xu hướng T1→T4</th>
                      <th>Nhận xét</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(p, i) in currentGroup.products" :key="p.ma">
                      <td
                        style="
                          width: 42px;
                          min-width: 42px;
                          max-width: 42px;
                          text-align: center;
                          padding: 10px 4px;
                          color: var(--text3);
                          font-family: var(--mono);
                        "
                      >
                        {{ i + 1 }}
                      </td>
                      <td
                        style="
                          min-width: 260px;
                          max-width: 320px;
                          white-space: normal;
                          word-break: break-word;
                        "
                      >
                        <div
                          style="
                            font-weight: 500;
                            font-size: 11px;
                            line-height: 1.4;
                          "
                        >
                          {{ p.ten }}
                        </div>
                        <div
                          style="
                            font-size: 10px;
                            color: var(--text3);
                            margin-top: 4px;
                          "
                        >
                          {{ p.ma }}
                        </div>
                      </td>
                      <td class="r">
                        <div
                          style="
                            display: flex;
                            align-items: center;
                            gap: 6px;
                            justify-content: flex-end;
                          "
                        >
                          <div
                            style="
                              width: 50px;
                              height: 4px;
                              background: var(--bg4);
                              border-radius: 2px;
                              overflow: hidden;
                            "
                          >
                            <div
                              style="height: 100%; background: #3b82f6"
                              :style="{
                                width: `${Math.round((p.rev / (getMaxProductRev() || 1)) * 100)}%`,
                              }"
                            ></div>
                          </div>
                          <span
                            style="font-family: var(--mono); font-size: 12px"
                            >{{ p.rev }}M</span
                          >
                        </div>
                      </td>
                      <td class="r mono">
                        {{ p.qty.toLocaleString("vi-VN") }}
                      </td>
                      <td class="r mono" style="color: #10b981">
                        {{ p.diem_ban }}
                      </td>
                      <td class="r mono">{{ p.nv_count }}</td>
                      <td class="r">
                        <span
                          style="font-size: 11px"
                          :style="{ color: getPhuNVColor(p.nv_count) }"
                        >
                          {{
                            Math.round(
                              (p.nv_count / (getActiveNVCount() || 1)) * 100,
                            )
                          }}%
                        </span>
                      </td>
                      <td>
                        <div
                          style="
                            display: flex;
                            align-items: flex-end;
                            gap: 2px;
                            height: 32px;
                          "
                        >
                          <div
                            v-for="(v, mi) in p.monthly"
                            :key="mi"
                            style="
                              width: 10px;
                              border-radius: 2px 2px 0 0;
                              flex-shrink: 0;
                            "
                            :style="{
                              height: `${Math.max(4, Math.round((v / (getMaxMonthlyVal(p.monthly) || 0.1)) * 28))}px`,
                              background: [
                                '#3b82f6',
                                '#10b981',
                                '#f59e0b',
                                '#a855f7',
                              ][mi % 4],
                            }"
                          ></div>
                        </div>
                      </td>
                      <td>
                        <span :class="getProductBadge(p).cls">{{
                          getProductBadge(p).txt
                        }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="section-title">Top 5 sản phẩm của từng nhân viên</div>
            <div class="chart-card mb-4">
              <div
                style="
                  margin-bottom: 14px;
                  display: flex;
                  align-items: center;
                  gap: 10px;
                  flex-wrap: wrap;
                "
              >
                <span
                  style="font-size: 11px; color: var(--text3); opacity: 0.85"
                  >Chọn nhân viên:</span
                >
                <select v-model="selectedEmployeeId" class="employee-select">
                  <option
                    v-for="(ten, mnv) in currentGroup.nv_info"
                    :key="mnv"
                    :value="mnv"
                  >
                    {{ ten }}
                  </option>
                </select>
              </div>
              <div
                style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px"
              >
                <!-- Left panel: List -->
                <div class="chart-card !bg-bg3 !p-4">
                  <div class="card-title" style="margin-bottom: 10px">
                    Top 5 SP ·
                    {{
                      currentGroup.nv_info?.[selectedEmployeeId] ||
                      selectedEmployeeId
                    }}
                  </div>
                  <div
                    v-if="!currentGroup.nv_top5?.[selectedEmployeeId]?.length"
                    style="
                      color: var(--text3);
                      padding: 20px;
                      text-align: center;
                      font-size: 11px;
                    "
                  >
                    Không có dữ liệu đơn hàng
                  </div>
                  <div v-else style="padding: 4px 0">
                    <div
                      v-for="(p, i) in (
                        currentGroup.nv_top5?.[selectedEmployeeId] || []
                      ).slice(0, 5)"
                      :key="p.ma"
                      style="
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        padding: 9px 0;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                      "
                    >
                      <span style="font-size: 16px; flex-shrink: 0">
                        {{ ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i] || "📦" }}
                      </span>
                      <div style="flex: 1; min-width: 0">
                        <div
                          style="
                            font-size: 11px;
                            font-weight: 500;
                            color: var(--text);
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                          "
                        >
                          {{ p.ten }}
                        </div>
                        <div
                          style="
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            margin-top: 4px;
                          "
                        >
                          <div
                            style="
                              flex: 1;
                              height: 4px;
                              background: var(--bg4);
                              border-radius: 2px;
                              overflow: hidden;
                            "
                          >
                            <div
                              style="height: 100%; border-radius: 2px"
                              :style="{
                                width: `${Math.round((p.rev / (currentGroup.nv_top5?.[selectedEmployeeId]?.[0]?.rev || 1)) * 100)}%`,
                                background: [
                                  '#3b82f6',
                                  '#10b981',
                                  '#f59e0b',
                                  '#a855f7',
                                  '#14b8a6',
                                ][i % 5],
                              }"
                            ></div>
                          </div>
                          <span
                            class="font-mono text-xs flex-shrink: 0"
                            :style="{
                              color: [
                                '#3b82f6',
                                '#10b981',
                                '#f59e0b',
                                '#a855f7',
                                '#14b8a6',
                              ][i % 5],
                            }"
                          >
                            {{ p.rev }}M
                          </span>
                        </div>
                        <div
                          style="
                            font-size: 10px;
                            color: var(--text3);
                            margin-top: 2px;
                          "
                        >
                          {{ p.qty.toLocaleString("vi-VN") }} đơn vị ·
                          {{
                            Math.round(
                              (p.rev /
                                (getNVSumRev(
                                  currentGroup.nv_top5?.[selectedEmployeeId],
                                ) || 1)) *
                                100,
                            )
                          }}% DT
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Right panel: Donut -->
                <div class="chart-card !bg-bg3 !p-4">
                  <div class="card-title" style="margin-bottom: 10px">
                    Tỷ trọng doanh thu
                  </div>
                  <div
                    v-if="!currentGroup.nv_top5?.[selectedEmployeeId]?.length"
                    style="
                      color: var(--text3);
                      padding: 20px;
                      text-align: center;
                      font-size: 11px;
                    "
                  >
                    Không có dữ liệu đơn hàng
                  </div>
                  <div v-else>
                    <div
                      style="position: relative; height: 200px; margin-top: 8px"
                    >
                      <canvas id="chart-nv-sp"></canvas>
                    </div>
                    <div style="margin-top: 10px">
                      <div
                        v-for="(p, i) in (
                          currentGroup.nv_top5?.[selectedEmployeeId] || []
                        ).slice(0, 5)"
                        :key="p.ma"
                        style="
                          display: flex;
                          align-items: center;
                          justify-content: space-between;
                          font-size: 11px;
                          margin-bottom: 5px;
                        "
                      >
                        <span
                          style="display: flex; align-items: center; gap: 5px"
                        >
                          <span
                            style="
                              width: 8px;
                              height: 8px;
                              border-radius: 50%;
                              display: inline-block;
                            "
                            :style="{
                              background: [
                                '#3b82f6',
                                '#10b981',
                                '#f59e0b',
                                '#a855f7',
                                '#14b8a6',
                              ][i % 5],
                            }"
                          ></span>
                          <span class="text-text2">{{ p.ten }}</span>
                        </span>
                        <span class="font-mono text-text">{{ p.rev }}M</span>
                      </div>
                      <!-- Khác -->
                      <div
                        v-if="
                          (currentGroup.nv_top5?.[selectedEmployeeId] || [])
                            .length > 5
                        "
                        style="
                          display: flex;
                          align-items: center;
                          justify-content: space-between;
                          font-size: 11px;
                          margin-bottom: 5px;
                        "
                      >
                        <span
                          style="display: flex; align-items: center; gap: 5px"
                        >
                          <span
                            style="
                              width: 8px;
                              height: 8px;
                              border-radius: 50%;
                              display: inline-block;
                              background: #64748b;
                            "
                          ></span>
                          <span class="text-text2"
                            >Khác ({{
                              (currentGroup.nv_top5?.[selectedEmployeeId] || [])
                                .length - 5
                            }}
                            SP)</span
                          >
                        </span>
                        <span class="font-mono text-text"
                          >{{
                            (currentGroup.nv_top5?.[selectedEmployeeId] || [])
                              .slice(5)
                              .reduce((s, x) => s + x.rev, 0)
                              .toFixed(1)
                          }}M</span
                        >
                      </div>
                    </div>
                  </div>
                </div>
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
                <div style="flex: 1; min-width: 0">
                  <div class="alert-title">{{ a.title }}</div>
                  <div class="alert-sub">{{ a.sub }}</div>

                  <div
                    v-if="a.details && a.details.length"
                    style="margin-top: 10px"
                  >
                    <button
                      @click="expandedAlerts[a.id] = !expandedAlerts[a.id]"
                      style="
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        padding: 4px 10px;
                        border-radius: 6px;
                        font-size: 11px;
                        color: var(--text2);
                        cursor: pointer;
                        transition: all 0.2s;
                        outline: none;
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                      "
                      onmouseover="
                        this.style.background = 'rgba(255,255,255,0.1)'
                      "
                      onmouseout="
                        this.style.background = 'rgba(255,255,255,0.05)'
                      "
                    >
                      <span>{{ expandedAlerts[a.id] ? "▼" : "▶" }}</span>
                      <span
                        >Xem danh sách check call ({{ a.details.length }})</span
                      >
                    </button>

                    <div
                      v-show="expandedAlerts[a.id]"
                      style="
                        margin-top: 8px;
                        max-height: 250px;
                        overflow-y: auto;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 8px;
                        background: rgba(15, 23, 42, 0.4);
                        padding: 6px 12px;
                      "
                    >
                      <table
                        style="
                          width: 100%;
                          border-collapse: collapse;
                          text-align: left;
                          font-size: 11px;
                        "
                      >
                        <thead>
                          <tr
                            style="
                              border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                              color: var(--text3);
                            "
                          >
                            <th style="padding: 6px 4px">Mã KH</th>
                            <th style="padding: 6px 4px">Tên khách hàng</th>
                            <th style="padding: 6px 4px">
                              Khách cá nhân (KHCN)
                            </th>
                            <th style="padding: 6px 4px">Giờ Check-in</th>
                            <th style="padding: 6px 4px">Giờ Check-out</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="(call, ci) in a.details"
                            :key="ci"
                            style="
                              border-bottom: 1px solid rgba(255, 255, 255, 0.04);
                              color: var(--text2);
                            "
                          >
                            <td
                              style="
                                padding: 6px 4px;
                                font-family: var(--mono);
                                color: var(--accent);
                              "
                            >
                              {{ call.ma_kh || "—" }}
                            </td>
                            <td style="padding: 6px 4px; font-weight: 500">
                              {{ call.ten_kh || "—" }}
                            </td>
                            <td style="padding: 6px 4px">
                              <span
                                v-if="call.khcn"
                                style="
                                  background: rgba(59, 130, 246, 0.1);
                                  border: 1px solid rgba(59, 130, 246, 0.2);
                                  padding: 1px 4px;
                                  border-radius: 3px;
                                  font-size: 9px;
                                  color: #60a5fa;
                                "
                              >
                                {{ call.khcn }}
                              </span>
                              <span v-else style="color: var(--text3)">—</span>
                            </td>
                            <td
                              style="
                                padding: 6px 4px;
                                font-family: var(--mono);
                                color: var(--amber);
                              "
                            >
                              {{ call.checkin || "—" }}
                            </td>
                            <td
                              style="padding: 6px 4px; font-family: var(--mono)"
                            >
                              {{ call.checkout || "—" }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── VIEW: CONVERSION ── -->
          <div v-if="activeView === 'conversion'" class="fade-in">
            <div class="section-title">Hiệu quả Chuyển đổi Khai phá (KHCN)</div>

            <div
              v-if="!currentGroup || !currentGroup.conversion_module"
              class="text-text3 p-5 text-center"
            >
              Chưa có dữ liệu chuyển đổi cho nhóm này.
            </div>

            <div v-else>
              <!-- KPI Cards -->
              <div
                class="kpi-grid"
                style="grid-template-columns: repeat(3, 1fr)"
              >
                <!-- Card 1 -->
                <div class="kpi-card c-blue">
                  <div class="kpi-label">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                      style="
                        width: 14px;
                        height: 14px;
                        display: inline-block;
                        vertical-align: text-top;
                        margin-right: 4px;
                      "
                    >
                      <path
                        d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"
                      />
                    </svg>
                    KH khai phá
                  </div>
                  <div class="kpi-value">
                    {{ currentGroup.conversion_module.total_calls_khcn }}
                  </div>
                  <div class="kpi-sub">
                    Đã thực hiện
                    {{ currentGroup.conversion_module.total_checks_khcn }} lượt
                    check call
                  </div>
                </div>
                <!-- Card 2 -->
                <div class="kpi-card c-teal">
                  <div class="kpi-label">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                      style="
                        width: 14px;
                        height: 14px;
                        display: inline-block;
                        vertical-align: text-top;
                        margin-right: 4px;
                      "
                    >
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="16" x2="12" y2="12" />
                      <line x1="12" y1="8" x2="12.01" y2="8" />
                    </svg>
                    Tỷ lệ khai phá
                  </div>
                  <div class="kpi-value">
                    {{ currentGroup.conversion_module.exploration_rate }}%
                  </div>
                  <div class="kpi-sub">KH khai phá / Lượt check call</div>
                </div>
                <!-- Card 3 -->
                <div class="kpi-card c-green">
                  <div class="kpi-label">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                      style="
                        width: 14px;
                        height: 14px;
                        display: inline-block;
                        vertical-align: text-top;
                        margin-right: 4px;
                      "
                    >
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                      <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                    Đơn chốt thành công
                  </div>
                  <div class="kpi-value">
                    {{ currentGroup.conversion_module.converted_khcn_count }}
                  </div>
                  <div class="kpi-sub">KHTC phát sinh đơn hàng</div>
                </div>
                <!-- Card 4 -->
                <div class="kpi-card c-amber">
                  <div class="kpi-label">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                      style="
                        width: 14px;
                        height: 14px;
                        display: inline-block;
                        vertical-align: text-top;
                        margin-right: 4px;
                      "
                    >
                      <line x1="18" y1="20" x2="18" y2="10" />
                      <line x1="12" y1="20" x2="12" y2="4" />
                      <line x1="6" y1="20" x2="6" y2="14" />
                    </svg>
                    Tỷ lệ chuyển đổi đơn
                  </div>
                  <div class="kpi-value">
                    {{ currentGroup.conversion_module.conversion_rate }}%
                  </div>
                  <div class="kpi-sub">Đơn chốt / KH khai phá</div>
                </div>
                <!-- Card 5 -->
                <div class="kpi-card c-red">
                  <div class="kpi-label">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                      style="
                        width: 14px;
                        height: 14px;
                        display: inline-block;
                        vertical-align: text-top;
                        margin-right: 4px;
                      "
                    >
                      <circle cx="12" cy="12" r="10" />
                      <path d="m9 12 2 2 4-4" />
                    </svg>
                    Tỷ lệ chốt tổng
                  </div>
                  <div class="kpi-value">
                    {{ currentGroup.conversion_module.total_rate }}%
                  </div>
                  <div class="kpi-sub">Đơn chốt / Lượt check call</div>
                </div>
                <!-- Card 6 -->
                <div class="kpi-card c-purple">
                  <div class="kpi-label">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.5"
                      style="
                        width: 14px;
                        height: 14px;
                        display: inline-block;
                        vertical-align: text-top;
                        margin-right: 4px;
                      "
                    >
                      <line x1="12" y1="1" x2="12" y2="23" />
                      <path
                        d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"
                      />
                    </svg>
                    Doanh thu khai phá
                  </div>
                  <div class="kpi-value">
                    {{ currentGroup.conversion_module.revenue.toFixed(1) }}M
                  </div>
                  <div class="kpi-sub">Doanh số từ các đơn hàng</div>
                </div>
              </div>

              <!-- Main Content: Stacked layout for maximum readability -->
              <div
                style="
                  display: flex;
                  flex-direction: column;
                  gap: 20px;
                  margin-top: 20px;
                "
              >
                <!-- Top: Employee Rankings -->
                <div style="display: flex; flex-direction: column; gap: 8px">
                  <div
                    class="section-title"
                    style="
                      display: flex;
                      justify-content: space-between;
                      align-items: center;
                      margin-bottom: 0;
                      margin-top: 0;
                    "
                  >
                    <span>Hiệu quả theo Nhân viên</span>
                    <button
                      v-if="conversionSelectedMnv"
                      @click="conversionSelectedMnv = ''"
                      style="
                        font-size: 11px;
                        color: var(--accent);
                        background: none;
                        border: none;
                        cursor: pointer;
                        text-decoration: underline;
                        text-transform: none;
                        letter-spacing: normal;
                      "
                    >
                      Xóa bộ lọc nhân viên
                    </button>
                  </div>
                  <div class="chart-card !p-0" style="margin-bottom: 0">
                    <div class="table-wrap scrollable-x-nv">
                      <table class="nv-table" style="width: 100%">
                        <thead>
                          <tr>
                            <th style="font-size: 11px; padding: 10px 8px">
                              Nhân viên
                            </th>
                            <th
                              class="r"
                              style="font-size: 11px; padding: 10px 8px"
                            >
                              Số call đã check
                            </th>
                            <th
                              class="r"
                              style="font-size: 11px; padding: 10px 8px"
                            >
                              Số khách hàng khai phá
                            </th>
                            <th
                              class="r"
                              style="font-size: 11px; padding: 10px 8px"
                            >
                              Tỷ lệ khai phá
                            </th>
                            <th
                              class="r"
                              style="font-size: 11px; padding: 10px 8px"
                            >
                              Đơn chốt thành công
                            </th>
                            <th
                              class="r"
                              style="font-size: 11px; padding: 10px 8px"
                            >
                              Tỷ lệ chuyển đổi
                            </th>
                            <th
                              class="r"
                              style="font-size: 11px; padding: 10px 8px"
                            >
                              Tỷ lệ chốt tổng
                            </th>
                            <th
                              class="r"
                              style="font-size: 11px; padding: 10px 8px"
                            >
                              Doanh thu khai phá
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="(m, i) in currentGroup.conversion_module
                              .member_conversions"
                            :key="m.mnv"
                            @click="
                              conversionSelectedMnv =
                                conversionSelectedMnv === m.mnv ? '' : m.mnv
                            "
                            style="cursor: pointer; transition: all 0.2s"
                            :style="{
                              background:
                                conversionSelectedMnv === m.mnv
                                  ? 'rgba(59, 130, 246, 0.15)'
                                  : '',
                              boxShadow:
                                conversionSelectedMnv === m.mnv
                                  ? 'inset 3px 0 0 var(--accent)'
                                  : '',
                            }"
                          >
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
                                  <div
                                    style="font-size: 10px; color: var(--text3)"
                                  >
                                    Mã NV: {{ m.mnv }}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td
                              class="r mono"
                              style="
                                font-size: 13px;
                                padding: 12px 8px;
                                color: var(--accent);
                              "
                            >
                              {{ m.checks_count }}
                            </td>
                            <td
                              class="r mono"
                              style="font-size: 13px; padding: 12px 8px"
                            >
                              {{ m.called_count }}
                            </td>
                            <td
                              class="r mono"
                              style="
                                font-size: 13px;
                                padding: 12px 8px;
                                color: var(--teal);
                                font-weight: 500;
                              "
                            >
                              {{ m.exploration_rate }}%
                            </td>
                            <td
                              class="r mono"
                              style="
                                font-size: 13px;
                                color: var(--emerald);
                                padding: 12px 8px;
                              "
                            >
                              {{ m.converted_count }}
                            </td>
                            <td
                              class="r mono"
                              style="
                                font-size: 13px;
                                color: var(--amber);
                                font-weight: 700;
                                padding: 12px 8px;
                              "
                            >
                              {{ m.conversion_rate }}%
                            </td>
                            <td
                              class="r mono"
                              style="
                                font-size: 13px;
                                color: var(--red);
                                font-weight: 600;
                                padding: 12px 8px;
                              "
                            >
                              {{ m.total_rate }}%
                            </td>
                            <td
                              class="r mono"
                              style="
                                font-size: 13px;
                                color: var(--purple);
                                padding: 12px 8px;
                                font-weight: 600;
                              "
                            >
                              {{ m.revenue.toFixed(1) }}M
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                <!-- Bottom: Converted Details List -->
                <div class="chart-card" style="padding: 20px">
                  <div
                    style="
                      display: flex;
                      justify-content: space-between;
                      align-items: center;
                      gap: 15px;
                      margin-bottom: 8px;
                      flex-wrap: wrap;
                    "
                  >
                    <div
                      class="section-title"
                      style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 0;
                        margin-top: 0;
                      "
                    >
                      Danh sách chi tiết khách hàng chuyển đổi
                      <span
                        v-if="conversionSelectedMnv"
                        style="
                          color: var(--accent);
                          font-weight: 500;
                          font-size: 13px;
                          margin-left: 8px;
                        "
                      >
                        (Đang lọc theo:
                        {{
                          currentGroup.members.find(
                            (x) => x.mnv === conversionSelectedMnv,
                          )?.ten
                        }})
                      </span>
                    </div>
                    <input
                      v-model="conversionSearch"
                      type="text"
                      placeholder="Tìm theo Tên KH, Mã KH, Mã đơn..."
                      style="
                        background: rgba(15, 23, 42, 0.6);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        color: var(--text);
                        padding: 8px 16px;
                        border-radius: 8px;
                        font-size: 11px;
                        outline: none;
                        width: 260px;
                        transition: all 0.2s;
                      "
                      onfocus="this.style.borderColor = 'var(--accent)'"
                      onblur="
                        this.style.borderColor = 'rgba(255, 255, 255, 0.1)'
                      "
                    />
                  </div>

                  <div
                    class="table-wrap"
                    style="max-height: 600px; overflow-y: auto"
                  >
                    <div
                      v-if="filteredConversionDetails.length === 0"
                      class="text-text3 p-5 text-center text-xs"
                    >
                      Không tìm thấy dữ liệu chuyển đổi nào phù hợp.
                    </div>
                    <table v-else class="nv-table" style="width: 100%">
                      <thead>
                        <tr>
                          <th style="font-size: 11px; padding: 10px 8px">
                            Khách hàng tổ chức
                          </th>
                          <th style="font-size: 11px; padding: 10px 8px">
                            KHCN
                          </th>
                          <th style="font-size: 11px; padding: 10px 8px">
                            Nhân viên
                          </th>
                          <th style="font-size: 11px; padding: 10px 8px">
                            Lịch sử
                          </th>
                          <th style="font-size: 11px; padding: 10px 8px">
                            Đơn hàng
                          </th>
                          <th
                            class="r"
                            style="font-size: 11px; padding: 10px 8px"
                          >
                            Tổng doanh số
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="c in filteredConversionDetails"
                          :key="c.khcn_guid"
                        >
                          <td style="padding: 12px 8px">
                            <div style="color: #e2e8f0; font-size: 11px">
                              {{ c.ten_kh }}
                            </div>
                            <div
                              style="
                                font-size: 10px;
                                color: var(--accent);
                                font-family: var(--mono);
                                margin-top: 2px;
                              "
                            >
                              {{ c.ma_kh }}
                            </div>
                          </td>
                          <td style="padding: 12px 8px">
                            <div
                              style="
                                font-size: 11px;
                                color: var(--text2);
                                font-weight: 500;
                              "
                            >
                              {{ c.khcn_name || "—" }}
                            </div>
                          </td>
                          <td style="padding: 12px 8px">
                            <div
                              style="
                                font-size: 11px;
                                color: var(--text2);
                                font-weight: 500;
                              "
                            >
                              {{ c.nv_names }}
                            </div>
                          </td>
                          <td style="padding: 12px 8px">
                            <div style="font-size: 11px; color: var(--amber)">
                              Call: {{ c.latest_call_time }}
                            </div>
                            <div
                              style="
                                font-size: 11px;
                                color: var(--emerald);
                                margin-top: 2px;
                              "
                            >
                              Đơn: {{ c.latest_order_time }}
                            </div>
                          </td>
                          <td style="padding: 12px 8px">
                            <div
                              style="
                                display: flex;
                                flex-wrap: wrap;
                                gap: 4px;
                                max-width: 250px;
                              "
                            >
                              <span
                                v-for="id in c.base_order_ids"
                                :key="id"
                                style="
                                  background: rgba(168, 85, 247, 0.1);
                                  border: 1px solid rgba(168, 85, 247, 0.2);
                                  color: #c084fc;
                                  font-size: 10px;
                                  padding: 2px 6px;
                                  border-radius: 4px;
                                  font-family: var(--mono);
                                "
                              >
                                {{ id }}
                              </span>
                            </div>
                          </td>
                          <td
                            class="r mono"
                            style="
                              font-weight: 700;
                              color: var(--purple);
                              font-size: 13px;
                              padding: 12px 8px;
                            "
                          >
                            {{ c.revenue.toFixed(2) }}M
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── VIEW: GUIDE ── -->
          <div v-if="activeView === 'guide'" class="fade-in">
            <div class="section-title">Cẩm nang & Tra cứu Thuật ngữ</div>

            <div class="mb-4">
              <input
                v-model="guideSearch"
                type="text"
                placeholder="Tìm kiếm khái niệm, chỉ số, công thức..."
                style="
                  width: 100%;
                  background: rgba(15, 23, 42, 0.6);
                  border: 1px solid rgba(255, 255, 255, 0.1);
                  color: var(--text);
                  padding: 12px 16px;
                  border-radius: 8px;
                  font-size: 13px;
                  outline: none;
                  transition: all 0.2s;
                "
                onfocus="this.style.borderColor = 'var(--accent)'"
                onblur="this.style.borderColor = 'rgba(255, 255, 255, 0.1)'"
              />
            </div>

            <div class="space-y-4">
              <div
                v-for="cat in filteredGuide"
                :key="cat.id"
                class="chart-card !p-5"
              >
                <h3
                  style="
                    font-size: 14px;
                    font-weight: 600;
                    color: var(--accent);
                    margin-bottom: 12px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                    padding-bottom: 6px;
                  "
                >
                  {{ cat.title }}
                </h3>
                <div
                  style="
                    display: grid;
                    grid-template-columns: repeat(
                      auto-fill,
                      minmax(320px, 1fr)
                    );
                    gap: 16px;
                  "
                >
                  <div
                    v-for="it in cat.items"
                    :key="it.name"
                    style="
                      background: rgba(255, 255, 255, 0.02);
                      border: 1px solid rgba(255, 255, 255, 0.04);
                      border-radius: 8px;
                      padding: 14px;
                    "
                  >
                    <h4
                      style="
                        font-size: 13px;
                        font-weight: 500;
                        color: var(--text);
                        margin-bottom: 6px;
                      "
                    >
                      {{ it.name }}
                    </h4>
                    <p
                      style="
                        font-size: 11.5px;
                        color: var(--text2);
                        line-height: 1.5;
                        margin-bottom: 8px;
                      "
                    >
                      {{ it.desc }}
                    </p>
                    <div
                      v-if="it.formula"
                      style="
                        font-size: 10px;
                        font-family: var(--mono);
                        color: var(--text3);
                        background: rgba(0, 0, 0, 0.15);
                        padding: 4px 8px;
                        border-radius: 4px;
                        display: inline-block;
                      "
                    >
                      Công thức: {{ it.formula }}
                    </div>
                  </div>
                </div>
              </div>

              <div
                v-if="filteredGuide.length === 0"
                style="text-align: center; color: var(--text3); padding: 40px"
              >
                Không tìm thấy thuật ngữ nào khớp với từ khóa tìm kiếm.
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
  width: 120px;
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
  font-size: 11px;
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
  font-size: 11px;
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
  margin-bottom: 16px;
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
  font-size: 11px;
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
.table-wrap.scrollable-y {
  max-height: 480px;
  overflow: auto; /* enable both vertical and horizontal scroll */
  position: relative;
}
.table-wrap.scrollable-x-nv {
  overflow-x: auto;
  position: relative;
}
/* Freeze Column Nhân viên */
.table-wrap.scrollable-x-nv table.nv-table th:nth-child(1) {
  position: sticky;
  left: 0;
  z-index: 25;
  background: #131b2e !important;
  box-shadow: inset -1px -1px 0 rgba(255, 255, 255, 0.1);
}
.table-wrap.scrollable-x-nv table.nv-table td:nth-child(1) {
  position: sticky;
  left: 0;
  z-index: 12;
  background: #131b2e !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}
/* Striped Row Compatibility for locked column in Employee Table */
.table-wrap.scrollable-x-nv table.nv-table tr:nth-child(even) td:nth-child(1) {
  background: #172138 !important;
}
/* Row Hover highlight compatibility for locked column */
.table-wrap.scrollable-x-nv table.nv-table tr:hover td:nth-child(1) {
  background: rgba(255, 255, 255, 0.05) !important;
}
.table-wrap.scrollable-y table.nv-table th {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #131b2e !important; /* solid color matching panel background */
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.1);
}
/* Freeze Column # */
.table-wrap.scrollable-y table.nv-table th:nth-child(1) {
  position: sticky;
  left: 0;
  top: 0;
  z-index: 25;
  background: #131b2e !important;
}
.table-wrap.scrollable-y table.nv-table td:nth-child(1) {
  position: sticky;
  left: 0;
  z-index: 12;
  background: #131b2e !important;
}
/* Freeze Column Tên sản phẩm */
.table-wrap.scrollable-y table.nv-table th:nth-child(2) {
  position: sticky;
  left: 42px; /* width of first column */
  top: 0;
  z-index: 25;
  background: #131b2e !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}
.table-wrap.scrollable-y table.nv-table td:nth-child(2) {
  position: sticky;
  left: 42px; /* width of first column */
  z-index: 12;
  background: #131b2e !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}
/* Row hover fix for sticky cells */
.table-wrap.scrollable-y table.nv-table tr:hover td:nth-child(1),
.table-wrap.scrollable-y table.nv-table tr:hover td:nth-child(2) {
  background: rgba(255, 255, 255, 0.05) !important;
}
/* Zebra striping compatibility for locked frozen cells */
.table-wrap.scrollable-y table.nv-table tr:nth-child(even) td:nth-child(1),
.table-wrap.scrollable-y table.nv-table tr:nth-child(even) td:nth-child(2) {
  background: #172138 !important;
}
.employee-select {
  font-size: 11px;
  background: var(--bg3);
  color: var(--text);
  border: 1px solid var(--border2);
  border-radius: 6px;
  padding: 4px 10px;
  outline: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.employee-select:hover {
  border-color: rgba(168, 85, 247, 0.4);
}
.employee-select option {
  background-color: #141720 !important;
  color: #f8fafc !important;
}
table.nv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
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
table.nv-table tr {
  background: #131b2e !important;
}
table.nv-table tr:nth-child(even) {
  background: #172138 !important;
}
table.nv-table tr:nth-child(even) td {
  background: transparent;
}
table.nv-table tr:hover td {
  background: rgba(255, 255, 255, 0.05) !important;
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
  font-size: 11px;
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

@media (max-width: 768px) {
  .shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .sidebar {
    height: auto;
    position: relative;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .sidebar-logo {
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .logo-mark {
    margin-bottom: 0;
  }
  .nav-section {
    padding: 8px;
    display: flex;
    overflow-x: auto;
    gap: 8px;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  .nav-label {
    display: none;
  }
  .nav-item {
    margin-bottom: 0;
    padding: 6px 12px;
    font-size: 11px;
  }
  .group-switcher {
    padding: 8px 12px;
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    gap: 8px;
    white-space: nowrap;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    -webkit-overflow-scrolling: touch;
  }
  .group-switcher > div {
    display: none;
  }
  .group-btn {
    width: auto;
    display: inline-block;
    margin-bottom: 0;
    padding: 6px 10px;
  }
  .topbar {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
    padding: 12px 16px;
  }
  .content {
    padding: 12px 16px;
  }
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row,
  .charts-row.thirds {
    grid-template-columns: 1fr !important;
  }
}
@media (max-width: 480px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
