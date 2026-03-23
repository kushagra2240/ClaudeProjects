document.getElementById("date-label").textContent = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

async function loadDashboard() {
  // Summary
  try {
    const s = await API.summary();
    // Week distance: fetch this week from weekly stats
    const weekly = await API.weekly(1);
    const thisWeek = weekly[0] || {};
    document.getElementById("s-dist").textContent = thisWeek.distance_km ?? "0";
    document.getElementById("s-steps").textContent = s.avg_daily_steps ? fmtSteps(s.avg_daily_steps) : "—";
    document.getElementById("s-hr").textContent = s.resting_hr ? s.resting_hr + " bpm" : "—";
    document.getElementById("s-sleep").textContent = s.avg_sleep_hours ? s.avg_sleep_hours + "h" : "—";
  } catch (e) {
    console.error(e);
  }

  // 30-day steps chart
  try {
    const steps = await API.steps();
    const labels = steps.map(d => {
      const dt = new Date(d.date);
      return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    });
    const values = steps.map(d => d.steps || 0);

    new Chart(document.getElementById("steps-chart"), {
      type: "bar",
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: values.map(v => v >= 10000 ? "#22c55e" : "#4f8ef7"),
          borderRadius: 4,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmtSteps(ctx.raw) + " steps" } } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 10 } } },
          y: { grid: { color: "#f1f5f9" }, ticks: { font: { size: 10 }, callback: v => v >= 1000 ? (v/1000)+"k" : v } }
        }
      }
    });
  } catch (e) {
    console.error("Steps chart:", e);
  }

  // Recent activities
  try {
    const data = await API.activities({ limit: 5 });
    const ul = document.getElementById("recent-activities");
    if (!data.items.length) {
      ul.innerHTML = `<div class="empty-state"><div class="icon">🏅</div><p>No activities yet. Upload your data to get started.</p></div>`;
      return;
    }
    ul.innerHTML = data.items.map(a => `
      <li class="activity-item" onclick="location.href='/activities'">
        <div class="activity-icon">${activityIcon(a.activity_type)}</div>
        <div class="activity-info">
          <div class="activity-name">${a.activity_type}</div>
          <div class="activity-meta">${a.date} &middot; <span class="badge badge-${a.source === 'runkeeper' ? 'runkeeper' : 'mifitness'}">${a.source}</span></div>
        </div>
        <div class="activity-stat">
          <div class="val">${a.distance_meters ? (a.distance_meters/1000).toFixed(1) : "—"}</div>
          <div class="unit">km</div>
        </div>
      </li>`).join("");
  } catch (e) {
    document.getElementById("recent-activities").innerHTML = `<div class="empty-state"><div class="icon">📭</div><p>Could not load activities.</p></div>`;
  }
}

loadDashboard();
