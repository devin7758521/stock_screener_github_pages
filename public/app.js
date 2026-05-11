let rawData = null;
let currentDataUrl = "./data/latest.json";

const defaults = {
  weeklyBodyMultiplier: 1.0,
  dailyBodyMultiplier: 1.0,
  enableVolumeFilter: false,
  volumeMultiplier: 1.2,
  enableDollarVolumeFilter: false,
  minAvgDollarVolume: 50000000,
  requireAboveMA25: false,
  requireAboveMA60: false,
  requireMA5GTMA25: false,
  requireMA25GTMA60: false,
  requireBeatSPY: false,
  requireBeatQQQ: false,
  enableKDJ: false,
  kdjJThreshold: 100,
  requireKDJJgtKWeekly: false,
  requireKDJJgtKDaily: false,
  showAI: true,
  showNews: false,
  enableWeeklyMA60DeviationFilter: false,
  minWeeklyMA60Deviation: 0.05,
  maxWeeklyMA60Deviation: 1.2,
  showWeeklyMA60DeviationRisk: true,
  topN: 200
};

const presets = {
  loose: { ...defaults, weeklyBodyMultiplier: 0.8, dailyBodyMultiplier: 0.8, enableVolumeFilter: false, minAvgDollarVolume: 10000000, maxWeeklyMA60Deviation: 1.5 },
  standard: { ...defaults },
  strict: { ...defaults, weeklyBodyMultiplier: 1.2, dailyBodyMultiplier: 1.2, volumeMultiplier: 1.5, minAvgDollarVolume: 100000000, requireAboveMA25: true, requireAboveMA60: true, requireBeatSPY: true, enableWeeklyMA60DeviationFilter: true, maxWeeklyMA60Deviation: 0.7 }
};

function $(id) { return document.getElementById(id); }
function money(v) { return "$" + Math.round((v || 0) / 1000000).toLocaleString() + "M"; }
function pct(v) { return v == null ? "--" : (v * 100).toFixed(1) + "%"; }

function setParams(params) {
  Object.entries(params).forEach(([k, v]) => {
    const el = $(k);
    if (!el) return;
    if (el.type === "checkbox") el.checked = !!v;
    else el.value = v;
  });
  syncOutputs();
}

function getParams() {
  const p = {};
  Object.keys(defaults).forEach(k => {
    const el = $(k);
    if (!el) return;
    if (el.type === "checkbox") p[k] = el.checked;
    else p[k] = Number(el.value);
  });
  return p;
}

function saveParams() { localStorage.setItem("stockScreenerParams", JSON.stringify(getParams())); }
function loadParams() { setParams(JSON.parse(localStorage.getItem("stockScreenerParams") || "null") || defaults); }
function syncOutputs() {
  ["weeklyBodyMultiplier", "dailyBodyMultiplier", "volumeMultiplier"].forEach(id => { $(id + "Out").textContent = Number($(id).value).toFixed(1); });
  const minDev = $("minWeeklyMA60Deviation");
  const maxDev = $("maxWeeklyMA60Deviation");
  if (minDev && maxDev) $("weeklyMA60DeviationOut").textContent = (Number(minDev.value) * 100).toFixed(0) + "% ~ " + (Number(maxDev.value) * 100).toFixed(0) + "%";
}

function passClientFilter(item, p) {
  const m = item.metrics || {};
  if (!m.weekly_bullish || m.weekly_body_ratio < p.weeklyBodyMultiplier) return false;
  if (!m.daily_bullish || m.daily_body_ratio < p.dailyBodyMultiplier) return false;
  if (p.enableVolumeFilter && m.volume_ratio < p.volumeMultiplier) return false;
  if (p.enableDollarVolumeFilter && m.avg_dollar_volume_20 < p.minAvgDollarVolume) return false;
  if (p.requireAboveMA25 && !m.above_ma25) return false;
  if (p.requireAboveMA60 && !m.above_ma60) return false;
  if (p.requireMA5GTMA25 && !m.ma5_gt_ma25) return false;
  if (p.requireMA25GTMA60 && !m.ma25_gt_ma60) return false;
  if (p.requireBeatSPY && !m.beat_spy_60d) return false;
  if (p.requireBeatQQQ && !m.beat_qqq_60d) return false;
  if (p.enableKDJ) {
    if (p.requireKDJJgtKWeekly && !(m.weekly_j > m.weekly_k)) return false;
    if (p.requireKDJJgtKDaily && !(m.daily_j > m.daily_k)) return false;
    if (m.weekly_j > p.kdjJThreshold || m.daily_j > p.kdjJThreshold) return false;
  }
  if (p.enableWeeklyMA60DeviationFilter) {
    const dev = m.weekly_ma60_deviation;
    if (dev == null) return false;
    if (dev < p.minWeeklyMA60Deviation || dev > p.maxWeeklyMA60Deviation) return false;
  }
  return true;
}

function renderCards(items, p) {
  const box = $("cards");
  box.innerHTML = "";
  if (!items.length) { box.innerHTML = `<div class="empty">当前参数下没有符合条件的股票。</div>`; return; }
  items.forEach(item => {
    const m = item.metrics || {};
    const news = (item.news || []).map(n => `<li>${n.title}</li>`).join("");
    const card = document.createElement("article");
    card.className = "stock-card";
    card.innerHTML = `
      <div class="card-head">
        <div><h3>${item.symbol}</h3><p>${item.name || ""}</p></div>
        <div class="score">${item.score}</div>
      </div>
      <div class="tags">${(item.tags || []).map(t => `<span>${t}</span>`).join("")}</div>
      <div class="info-grid">
        <div><span>周K实体比</span><strong>${(m.weekly_body_ratio || 0).toFixed(2)}x</strong></div>
        <div><span>日K实体比</span><strong>${(m.daily_body_ratio || 0).toFixed(2)}x</strong></div>
        <div><span>成交量比</span><strong>${(m.volume_ratio || 0).toFixed(2)}x</strong></div>
        <div><span>20日均成交额</span><strong>${money(m.avg_dollar_volume_20)}</strong></div>
        <div><span>60日收益</span><strong>${pct(m.stock_return_60d)}</strong></div>
        <div><span>SPY 60日</span><strong>${pct(m.spy_return_60d)}</strong></div>
        <div><span>QQQ 60日</span><strong>${pct(m.qqq_return_60d)}</strong></div>
        <div><span>收盘价</span><strong>${m.close || "--"}</strong></div>
        <div><span>周J</span><strong>${m.weekly_j ?? "--"}</strong></div>
        <div><span>日J</span><strong>${m.daily_j ?? "--"}</strong></div>
        <div><span>60周线偏离</span><strong>${pct(m.weekly_ma60_deviation)}</strong></div>
        <div><span>60周线风险</span><strong>${m.weekly_ma60_deviation_risk || "--"}</strong></div>
      </div>
      ${p.showAI ? `<div class="analysis">${item.ai_summary || "暂无AI摘要"}</div>` : ""}
      ${p.showNews && news ? `<ul class="news">${news}</ul>` : ""}
    `;
    box.appendChild(card);
  });
}

function applyFilter() {
  if (!rawData) return;
  const p = getParams();
  saveParams();
  const items = (rawData.items || []).filter(i => passClientFilter(i, p)).sort((a, b) => b.score - a.score).slice(0, p.topN);
  $("candidateCount").textContent = items.length;
  renderCards(items, p);
}

async function loadData(url = currentDataUrl) {
  try {
    const res = await fetch(url + "?_=" + Date.now());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    rawData = await res.json();
    $("lastUpdated").textContent = rawData.generated_at || "--";
    $("marketStatus").textContent = rawData.market_status || "--";
    $("universeCount").textContent = rawData.universe_count || "--";
    applyFilter();
  } catch (e) {
    $("cards").innerHTML = `<div class="empty">数据加载失败：${e.message}。请稍后刷新重试。</div>`;
    $("lastUpdated").textContent = "加载失败";
  }
}

async function loadHistory() {
  try {
    const res = await fetch("./data/history.json?_=" + Date.now());
    const history = await res.json();
    const box = $("historyList");
    box.innerHTML = `<button class="active" data-url="./data/latest.json">最新</button>` + history.map(h => `<button data-url="./data/runs/${h.date}.json">${h.date}<small>${h.count ?? ""}</small></button>`).join("");
    box.querySelectorAll("button").forEach(btn => btn.addEventListener("click", async () => {
      box.querySelectorAll("button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentDataUrl = btn.dataset.url;
      await loadData(currentDataUrl);
    }));
  } catch (e) { console.warn("history load failed", e); }
}

function bindEvents() {
  document.querySelectorAll("input, select").forEach(el => el.addEventListener("input", () => { syncOutputs(); applyFilter(); }));
  document.querySelectorAll("[data-preset]").forEach(btn => btn.addEventListener("click", () => { setParams(presets[btn.dataset.preset]); applyFilter(); }));
  $("resetBtn").addEventListener("click", () => { localStorage.removeItem("stockScreenerParams"); setParams(defaults); applyFilter(); });
}

async function main() {
  loadParams();
  bindEvents();
  await loadData();
  await loadHistory();
}
main();
