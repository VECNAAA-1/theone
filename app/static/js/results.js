// results.js – renders analysis results from sessionStorage

document.addEventListener("DOMContentLoaded", () => {
  const data = loadResults();
  if (!data) {
    document.getElementById("no-results").classList.remove("hidden");
    return;
  }
  document.getElementById("no-results").classList.add("hidden");
  document.getElementById("results-container").classList.remove("hidden");
  render(data);
});

function render(data) {
  renderSummary(data.insights);
  renderAlerts(data.insights.alerts);
  renderStats(data.sentiments);
  renderCharts(data.charts);
  renderThemes(data.themes);
  renderRecommendations(data.insights.recommendations);
  renderTable(data.sentiments.items);
}

// ── Summary ──────────────────────────────────────────────────────────────────

function renderSummary(insights) {
  document.getElementById("summary-text").textContent = insights.summary || "";
}

// ── Alerts ───────────────────────────────────────────────────────────────────

function renderAlerts(alerts) {
  const container = document.getElementById("alerts-container");
  container.innerHTML = "";
  (alerts || []).forEach(alert => {
    const div = document.createElement("div");
    div.className = "alert " + (alert.includes("CRITICAL") ? "alert-crit" : "alert-warn");
    div.textContent = alert;
    container.appendChild(div);
  });
}

// ── Stats Badges ─────────────────────────────────────────────────────────────

function renderStats(sentiments) {
  const grid = document.getElementById("result-stats");
  const counts = sentiments.counts || {};
  const pct = sentiments.percentages || {};

  const items = [
    { label: "Positive", cls: "positive", icon: "😊", key: "Positive" },
    { label: "Negative", cls: "negative", icon: "😞", key: "Negative" },
    { label: "Neutral",  cls: "neutral",  icon: "😐", key: "Neutral" },
    { label: "Total",    cls: "total",    icon: "📋", key: null },
  ];

  grid.innerHTML = items.map(item => {
    const val = item.key
      ? `${counts[item.key] || 0} <small style="font-size:14px;font-weight:400;color:var(--text-muted)">(${pct[item.key] || 0}%)</small>`
      : sentiments.total || 0;
    return `
      <div class="stat-card ${item.cls}">
        <div class="stat-icon">${item.icon}</div>
        <div class="stat-info">
          <span class="stat-label">${item.label}</span>
          <span class="stat-value">${val}</span>
        </div>
      </div>`;
  }).join("");
}

// ── Charts ───────────────────────────────────────────────────────────────────

function renderCharts(charts) {
  const set = (id, b64) => {
    const el = document.getElementById(id);
    if (el && b64) el.src = "data:image/png;base64," + b64;
    else if (el) el.closest(".chart-card")?.classList.add("hidden");
  };
  set("pie-chart", charts.pie_chart);
  set("bar-chart", charts.bar_chart);
  set("keyword-bar", charts.keyword_bar);
  set("word-cloud", charts.word_cloud);
  set("polarity-histogram", charts.polarity_histogram);
}

// ── Themes ───────────────────────────────────────────────────────────────────

function renderThemes(themes) {
  const container = document.getElementById("themes-list");
  const phrases = themes.top_phrases || [];
  if (!phrases.length) { container.innerHTML = "<em style='color:var(--text-muted)'>No themes detected.</em>"; return; }
  container.innerHTML = phrases
    .map(p => `<span class="tag">${p.phrase} <small style="color:var(--text-muted)">${p.score}</small></span>`)
    .join("");
}

// ── Recommendations ──────────────────────────────────────────────────────────

function renderRecommendations(recs) {
  const ul = document.getElementById("recommendations-list");
  ul.innerHTML = (recs || []).map(r => `<li>${r}</li>`).join("");
}

// ── Per-item Table ───────────────────────────────────────────────────────────

function renderTable(items) {
  const tbody = document.getElementById("items-table-body");
  tbody.innerHTML = (items || []).map((item, i) => {
    const badgeCls = item.label === "Positive" ? "badge-pos" : item.label === "Negative" ? "badge-neg" : "badge-neu";
    return `
      <tr>
        <td>${i + 1}</td>
        <td>${escHtml(item.text)}</td>
        <td><span class="badge ${badgeCls}">${item.label}</span></td>
        <td>${item.polarity}</td>
        <td>${item.subjectivity}</td>
      </tr>`;
  }).join("");
}

function escHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
