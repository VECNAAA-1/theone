// app.js – shared utilities

/**
 * Persist analysis results to sessionStorage so the Results page
 * can read them after redirect.
 */
function saveResults(data) {
  sessionStorage.setItem("feedbackiq_results", JSON.stringify(data));
}

function loadResults() {
  const raw = sessionStorage.getItem("feedbackiq_results");
  return raw ? JSON.parse(raw) : null;
}

function showLoading() {
  document.getElementById("loading")?.classList.remove("hidden");
}

function hideLoading() {
  document.getElementById("loading")?.classList.add("hidden");
}

function showError(msg) {
  const el = document.getElementById("error-banner");
  if (!el) return;
  el.textContent = "⚠️  " + msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 8000);
}
