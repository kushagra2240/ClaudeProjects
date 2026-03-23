let currentPage = 1;
let currentType = "";
let currentSource = "";

// Filter chips
document.getElementById("type-filters").addEventListener("click", e => {
  const chip = e.target.closest(".filter-chip");
  if (!chip) return;
  document.querySelectorAll("#type-filters .filter-chip").forEach(c => c.classList.remove("active"));
  chip.classList.add("active");
  currentType = chip.dataset.type;
  currentPage = 1;
  loadActivities();
});

document.getElementById("source-filters").addEventListener("click", e => {
  const chip = e.target.closest(".filter-chip");
  if (!chip) return;
  document.querySelectorAll("#source-filters .filter-chip").forEach(c => c.classList.remove("active"));
  chip.classList.add("active");
  currentSource = chip.dataset.source;
  currentPage = 1;
  loadActivities();
});

async function loadActivities() {
  const list = document.getElementById("activity-list");
  list.innerHTML = `<div class="spinner"></div>`;

  const params = { page: currentPage, limit: 15 };
  if (currentType) params.type = currentType;
  if (currentSource) params.source = currentSource;

  try {
    const data = await API.activities(params);
    if (!data.items.length) {
      list.innerHTML = `<div class="empty-state"><div class="icon">🏅</div><p>No activities found. Try changing filters or upload data.</p></div>`;
      document.getElementById("pagination").innerHTML = "";
      return;
    }

    list.innerHTML = data.items.map(a => `
      <li class="activity-item" onclick="openDetail(${a.id})">
        <div class="activity-icon">${activityIcon(a.activity_type)}</div>
        <div class="activity-info">
          <div class="activity-name">${a.activity_type} <span class="badge badge-${a.source === 'runkeeper' ? 'runkeeper' : 'mifitness'}" style="font-size:10px">${a.source}</span></div>
          <div class="activity-meta">${a.date} &middot; ${fmtDuration(a.duration_seconds)}</div>
        </div>
        <div class="activity-stat">
          <div class="val">${a.distance_meters ? (a.distance_meters/1000).toFixed(2) : "—"}</div>
          <div class="unit">km</div>
        </div>
      </li>`).join("");

    // Pagination
    const totalPages = Math.ceil(data.total / data.limit);
    const pag = document.getElementById("pagination");
    if (totalPages <= 1) { pag.innerHTML = ""; return; }

    pag.innerHTML = `
      <button class="btn btn-secondary" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? "disabled" : ""}>‹ Prev</button>
      <span style="line-height:38px;font-size:13px;color:var(--text-muted)">${currentPage} / ${totalPages}</span>
      <button class="btn btn-secondary" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? "disabled" : ""}>Next ›</button>`;
  } catch (e) {
    list.innerHTML = `<div class="alert alert-error">Could not load activities.</div>`;
  }
}

function changePage(p) {
  currentPage = p;
  loadActivities();
  window.scrollTo(0, 0);
}

async function openDetail(id) {
  const overlay = document.getElementById("detail-overlay");
  const content = document.getElementById("detail-content");
  overlay.classList.add("open");
  content.innerHTML = `<div class="spinner"></div>`;

  try {
    const a = await API.activity(id);
    const pace = (a.distance_meters && a.duration_seconds)
      ? ((a.duration_seconds / 60) / (a.distance_meters / 1000)).toFixed(2) + " min/km"
      : "—";

    content.innerHTML = `
      <h2 style="font-size:20px;font-weight:700;margin-bottom:4px">${activityIcon(a.activity_type)} ${a.activity_type}</h2>
      <p style="font-size:13px;color:var(--text-muted);margin-bottom:12px">${a.date} &middot; <span class="badge badge-${a.source === 'runkeeper' ? 'runkeeper' : 'mifitness'}">${a.source}</span></p>
      <div class="stat-row">
        <div class="stat-pill"><div class="v">${a.distance_meters ? (a.distance_meters/1000).toFixed(2) : "—"}</div><div class="l">km</div></div>
        <div class="stat-pill"><div class="v">${fmtDuration(a.duration_seconds)}</div><div class="l">duration</div></div>
        <div class="stat-pill"><div class="v">${pace}</div><div class="l">pace</div></div>
        <div class="stat-pill"><div class="v">${a.avg_heart_rate ? a.avg_heart_rate + " bpm" : "—"}</div><div class="l">avg HR</div></div>
        <div class="stat-pill"><div class="v">${a.calories ? Math.round(a.calories) : "—"}</div><div class="l">kcal</div></div>
      </div>
      ${a.gpx_points && a.gpx_points.length ? `<canvas id="route-canvas"></canvas>` : `<p style="font-size:13px;color:var(--text-muted)">No GPS data for this activity.</p>`}`;

    if (a.gpx_points && a.gpx_points.length) {
      drawRoute(a.gpx_points);
    }
  } catch (e) {
    content.innerHTML = `<div class="alert alert-error">Could not load activity detail.</div>`;
  }
}

function closeDetail() {
  document.getElementById("detail-overlay").classList.remove("open");
}

function drawRoute(points) {
  const canvas = document.getElementById("route-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  canvas.width = canvas.offsetWidth || 340;
  canvas.height = 220;

  const lats = points.map(p => p.lat);
  const lons = points.map(p => p.lon);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLon = Math.min(...lons), maxLon = Math.max(...lons);
  const pad = 20;
  const w = canvas.width - pad * 2;
  const h = canvas.height - pad * 2;

  const toX = lon => pad + ((lon - minLon) / (maxLon - minLon || 1)) * w;
  const toY = lat => pad + (1 - (lat - minLat) / (maxLat - minLat || 1)) * h;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#4f8ef7";
  ctx.lineWidth = 2.5;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  points.forEach((p, i) => {
    const x = toX(p.lon), y = toY(p.lat);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Start (green) and end (red) dots
  const start = points[0], end = points[points.length - 1];
  [[start, "#22c55e"], [end, "#ef4444"]].forEach(([p, color]) => {
    ctx.beginPath();
    ctx.arc(toX(p.lon), toY(p.lat), 5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  });
}

loadActivities();
