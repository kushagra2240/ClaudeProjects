/**
 * Shared API fetch wrapper.
 * All functions return parsed JSON or throw on HTTP error.
 */

async function apiFetch(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Stats ─────────────────────────────────────────────────────────────────
const API = {
  summary: () => apiFetch("/api/stats/summary"),
  weekly: (weeks = 8) => apiFetch(`/api/stats/weekly?weeks=${weeks}`),
  monthly: (months = 6) => apiFetch(`/api/stats/monthly?months=${months}`),

  // Activities
  activities: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/activities${qs ? "?" + qs : ""}`);
  },
  activity: (id) => apiFetch(`/api/activities/${id}`),

  // Health
  steps: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/health/steps${qs ? "?" + qs : ""}`);
  },
  heartrate: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/health/heartrate${qs ? "?" + qs : ""}`);
  },
  sleep: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/api/health/sleep${qs ? "?" + qs : ""}`);
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────
function fmtDuration(seconds) {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function fmtDist(meters) {
  if (!meters) return "—";
  return (meters / 1000).toFixed(2) + " km";
}

function fmtSteps(n) {
  if (!n) return "—";
  return n.toLocaleString();
}

function activityIcon(type) {
  const icons = { run: "🏃", walk: "🚶", cycle: "🚴", hike: "🥾", swim: "🏊", elliptical: "⚙️", row: "🚣", yoga: "🧘", strength: "🏋️" };
  return icons[type] || "🏅";
}

function setActive(selector) {
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
  const el = document.querySelector(selector);
  if (el) el.classList.add("active");
}

function showError(containerId, msg) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="alert alert-error">${msg}</div>`;
}

function showEmpty(containerId, message = "No data yet. Upload your fitness files to get started.") {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="empty-state"><div class="icon">📊</div><p>${message}</p></div>`;
}
