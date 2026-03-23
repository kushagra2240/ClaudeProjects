// Tab switching
const tabs = { steps: null, heartrate: null, sleep: null };
const loaded = { steps: false, heartrate: false, sleep: false };

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const tab = btn.dataset.tab;
    Object.keys(tabs).forEach(k => {
      document.getElementById(`tab-${k}`).style.display = k === tab ? "" : "none";
    });
    if (!loaded[tab]) {
      loaded[tab] = true;
      if (tab === "heartrate") loadHR();
      if (tab === "sleep") loadSleep();
    }
  });
});

// ── Steps ─────────────────────────────────────────────────────────────────
async function loadSteps() {
  try {
    const data = await API.steps();
    if (!data.length) return;

    const vals = data.map(d => d.steps || 0);
    const avg = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
    const best = Math.max(...vals);

    document.getElementById("avg-steps").textContent = fmtSteps(avg);
    document.getElementById("best-steps").textContent = fmtSteps(best);

    new Chart(document.getElementById("steps-chart"), {
      type: "bar",
      data: {
        labels: data.map(d => {
          const dt = new Date(d.date);
          return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        }),
        datasets: [{
          data: vals,
          backgroundColor: vals.map(v => v >= 10000 ? "#22c55e" : "#4f8ef7"),
          borderRadius: 4, borderSkipped: false,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => [fmtSteps(ctx.raw) + " steps", ctx.raw >= 10000 ? "✅ Goal reached!" : `${10000 - ctx.raw} to goal`]
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
          y: {
            grid: { color: "#f1f5f9" },
            ticks: { font: { size: 10 }, callback: v => v >= 1000 ? (v/1000)+"k" : v },
            suggestedMax: Math.max(...vals, 10000) * 1.1,
          }
        }
      }
    });
  } catch (e) {
    console.error("Steps:", e);
  }
}

// ── Heart Rate ─────────────────────────────────────────────────────────────
async function loadHR() {
  try {
    const data = await API.heartrate({ resolution: "daily" });
    if (!data.length) {
      document.getElementById("tab-heartrate").innerHTML = `<div class="empty-state"><div class="icon">❤️</div><p>No heart rate data yet.</p></div>`;
      return;
    }

    const avgs = data.map(d => d.avg_bpm);
    const resting = Math.round(avgs.reduce((a, b) => a + b, 0) / avgs.length);
    document.getElementById("resting-hr").textContent = resting;

    new Chart(document.getElementById("hr-chart"), {
      type: "line",
      data: {
        labels: data.map(d => {
          const dt = new Date(d.time);
          return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        }),
        datasets: [
          {
            label: "Avg BPM",
            data: avgs,
            borderColor: "#ef4444",
            backgroundColor: "rgba(239,68,68,.1)",
            fill: true,
            tension: 0.3,
            pointRadius: 2,
          },
          {
            label: "Min BPM",
            data: data.map(d => d.min_bpm),
            borderColor: "#94a3b8",
            borderDash: [4, 4],
            fill: false,
            tension: 0.3,
            pointRadius: 0,
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: true, labels: { font: { size: 11 } } } },
        scales: {
          x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
          y: { grid: { color: "#f1f5f9" }, ticks: { font: { size: 10 } }, min: 40 }
        }
      }
    });
  } catch (e) {
    console.error("HR:", e);
  }
}

// ── Sleep ──────────────────────────────────────────────────────────────────
async function loadSleep() {
  try {
    const data = await API.sleep();
    if (!data.length) {
      document.getElementById("tab-sleep").innerHTML = `<div class="empty-state"><div class="icon">😴</div><p>No sleep data yet.</p></div>`;
      return;
    }

    const totals = data.map(d => (d.total_minutes || 0) / 60);
    const avg = (totals.reduce((a, b) => a + b, 0) / totals.length).toFixed(1);
    document.getElementById("avg-sleep").textContent = avg + "h";

    const labels = data.map(d => {
      const dt = new Date(d.date);
      return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    });

    new Chart(document.getElementById("sleep-chart"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Deep", data: data.map(d => (d.deep_minutes || 0) / 60), backgroundColor: "#1d4ed8", borderRadius: 4 },
          { label: "REM",  data: data.map(d => (d.rem_minutes || 0) / 60),  backgroundColor: "#7c3aed", borderRadius: 4 },
          { label: "Light",data: data.map(d => (d.light_minutes || 0) / 60),backgroundColor: "#93c5fd", borderRadius: 4 },
          { label: "Awake",data: data.map(d => (d.awake_minutes || 0) / 60),backgroundColor: "#fca5a5", borderRadius: 4 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: true, labels: { font: { size: 11 }, boxWidth: 12 } } },
        scales: {
          x: { stacked: true, grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
          y: { stacked: true, grid: { color: "#f1f5f9" }, ticks: { font: { size: 10 }, callback: v => v + "h" } }
        }
      }
    });
  } catch (e) {
    console.error("Sleep:", e);
  }
}

// Load initial tab
loaded.steps = true;
loadSteps();
