async function loadStats() {
  // Summary
  try {
    const s = await API.summary();
    document.getElementById("t-dist").textContent = s.total_distance_km;
    document.getElementById("t-acts").textContent = s.total_activities;
    document.getElementById("t-steps").textContent = s.avg_daily_steps ? fmtSteps(s.avg_daily_steps) : "—";
    document.getElementById("t-sleep").textContent = s.avg_sleep_hours ? s.avg_sleep_hours + "h" : "—";

    document.getElementById("pr-run").textContent = s.records.longest_run_km + " km";
    document.getElementById("pr-steps").textContent = fmtSteps(s.records.best_step_day);
    document.getElementById("pr-sleep").textContent = s.records.best_sleep_hours + "h";
  } catch (e) {
    console.error("Summary:", e);
  }

  // Weekly chart
  try {
    const weekly = await API.weekly(8);
    new Chart(document.getElementById("weekly-chart"), {
      type: "bar",
      data: {
        labels: weekly.map(w => w.week),
        datasets: [{
          label: "km",
          data: weekly.map(w => w.distance_km),
          backgroundColor: "#4f8ef7",
          borderRadius: 6,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.raw + " km" } } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 } } },
          y: { grid: { color: "#f1f5f9" }, ticks: { font: { size: 10 }, callback: v => v + " km" } }
        }
      }
    });
  } catch (e) {
    console.error("Weekly:", e);
  }

  // Monthly chart (multi-dataset: distance + steps scaled)
  try {
    const monthly = await API.monthly(6);
    new Chart(document.getElementById("monthly-chart"), {
      type: "bar",
      data: {
        labels: monthly.map(m => m.month),
        datasets: [
          {
            label: "Distance (km)",
            data: monthly.map(m => m.distance_km),
            backgroundColor: "#4f8ef7",
            borderRadius: 4,
            yAxisID: "y",
          },
          {
            label: "Activities",
            data: monthly.map(m => m.activities),
            backgroundColor: "#22c55e",
            borderRadius: 4,
            yAxisID: "y2",
          }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: true, labels: { font: { size: 11 }, boxWidth: 12 } } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 } } },
          y:  { position: "left",  grid: { color: "#f1f5f9" }, ticks: { font: { size: 10 }, callback: v => v + " km" } },
          y2: { position: "right", grid: { display: false }, ticks: { font: { size: 10 } } }
        }
      }
    });
  } catch (e) {
    console.error("Monthly:", e);
  }
}

loadStats();
