// Drag-and-drop setup
["mf", "rk"].forEach(prefix => {
  const zone = document.getElementById(`${prefix}-zone`);
  const fileInput = document.getElementById(`${prefix}-file`);
  const label = document.getElementById(`${prefix}-filename`);

  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) {
      label.textContent = fileInput.files[0].name;
      // Clear previous preview when a new file is selected
      const previewBox = document.getElementById(`${prefix}-preview-box`);
      if (previewBox) previewBox.innerHTML = "";
    }
  });

  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      fileInput.files = dt.files;
      label.textContent = file.name;
      const previewBox = document.getElementById(`${prefix}-preview-box`);
      if (previewBox) previewBox.innerHTML = "";
    }
  });
});

// ── Preview ───────────────────────────────────────────────────────────────────

async function previewFile() {
  const fileInput = document.getElementById("mf-file");
  const previewBox = document.getElementById("mf-preview-box");
  const btn = document.getElementById("mf-preview-btn");
  const progressWrap = document.getElementById("mf-progress-wrap");
  const progressBar = document.getElementById("mf-progress");

  if (!fileInput.files[0]) {
    previewBox.innerHTML = `<div class="alert alert-error">Select a ZIP file first.</div>`;
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  btn.disabled = true;
  btn.textContent = "Scanning…";
  progressWrap.style.display = "block";
  progressBar.style.width = "40%";

  try {
    const res = await fetch("/api/upload/mi-fitness/preview", { method: "POST", body: formData });
    progressBar.style.width = "100%";

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Preview failed");
    }

    const d = await res.json();
    previewBox.innerHTML = renderPreview(d);
  } catch (e) {
    previewBox.innerHTML = `<div class="alert alert-error">❌ ${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Preview";
    setTimeout(() => { progressWrap.style.display = "none"; progressBar.style.width = "0%"; }, 800);
  }
}

function renderPreview(d) {
  const fmt = n => n.toLocaleString();
  const range = key => {
    const r = d.date_ranges[key];
    return r ? `<div class="range">${r.from} → ${r.to}</div>` : "";
  };

  const stats = [
    { key: "activities", label: "Activities", icon: "🏃" },
    { key: "steps",      label: "Step days",  icon: "👟" },
    { key: "heartrate",  label: "HR readings", icon: "❤️" },
    { key: "sleep",      label: "Sleep nights", icon: "😴" },
  ];

  const grid = stats.map(s => `
    <div class="preview-stat">
      <div class="num">${fmt(d.counts[s.key] || 0)}</div>
      <div class="lbl">${s.icon} ${s.label}</div>
      ${range(s.key)}
    </div>`).join("");

  const actBreakdown = d.activity_types && d.activity_types.length ? `
    <div class="activity-breakdown">
      <p style="font-size:12px;font-weight:600;margin:0 0 6px;color:var(--text-secondary)">Activity breakdown:</p>
      ${d.activity_types.map(a => `
        <div class="activity-row">
          <span style="text-transform:capitalize">${a.type}</span>
          <span style="font-weight:600">${a.count}</span>
        </div>`).join("")}
    </div>` : "";

  const errors = d.errors && d.errors.length ? `
    <div style="margin-top:8px">
      ${d.errors.map(e => `<div class="error-row">⚠️ ${e.file}: ${e.error}</div>`).join("")}
    </div>` : "";

  const unrecognised = d.unrecognised_files && d.unrecognised_files.length ? `
    <details>
      <summary>${d.unrecognised_files.length} unrecognised file(s) — tap to see</summary>
      <pre>${d.unrecognised_files.join("\n")}</pre>
    </details>` : "";

  const colDetails = d.columns && Object.keys(d.columns).length ? `
    <details>
      <summary>Raw column names — tap to see (useful for debugging)</summary>
      <pre>${Object.entries(d.columns).map(([f, cols]) => `${f}\n  ${cols.join(", ")}`).join("\n\n")}</pre>
    </details>` : "";

  const total = Object.values(d.counts).reduce((a, b) => a + b, 0);
  if (total === 0) {
    return `<div class="alert alert-error">⚠️ No recognisable data found in this ZIP. Check that it's a Mi Fitness export — tap "Raw column names" below if you see files listed.<br>${colDetails}</div>`;
  }

  return `
    <div class="preview-box">
      <h4>What will be imported</h4>
      <div class="preview-grid">${grid}</div>
      ${actBreakdown}
      ${errors}
      ${unrecognised}
      ${colDetails}
    </div>
    <p style="font-size:12px;color:var(--text-muted);margin:8px 0 0">
      Duplicates are skipped automatically — safe to re-import the same file.
    </p>`;
}

// ── Import ────────────────────────────────────────────────────────────────────

async function uploadFile(source) {
  const prefix = source === "mi-fitness" ? "mf" : "rk";
  const fileInput = document.getElementById(`${prefix}-file`);
  const btn = document.getElementById(`${prefix}-btn`);
  const progressWrap = document.getElementById(`${prefix}-progress-wrap`);
  const progressBar = document.getElementById(`${prefix}-progress`);
  const resultBox = document.getElementById("result-box");

  if (!fileInput.files[0]) {
    resultBox.innerHTML = `<div class="alert alert-error">Please select a ZIP file first.</div>`;
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  btn.disabled = true;
  btn.textContent = "Importing…";
  progressWrap.style.display = "block";
  progressBar.style.width = "30%";
  resultBox.innerHTML = "";

  try {
    progressBar.style.width = "60%";
    const res = await fetch(`/api/upload/${source}`, { method: "POST", body: formData });
    progressBar.style.width = "100%";

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Upload failed");
    }

    const data = await res.json();
    const imp = data.imported;
    const skip = data.skipped;

    const lines = Object.entries(imp)
      .filter(([, v]) => v > 0)
      .map(([k, v]) => `<b>${v}</b> ${k}`)
      .join(", ") || "nothing new";

    const skipLines = Object.entries(skip || {})
      .filter(([, v]) => v > 0)
      .map(([k, v]) => `${v} ${k} already existed`)
      .join(", ");

    resultBox.innerHTML = `
      <div class="alert alert-success">
        ✅ Imported ${lines}.
        ${skipLines ? `<br><small style="color:var(--text-muted)">${skipLines}</small>` : ""}
      </div>`;

    // Scroll to result
    resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    resultBox.innerHTML = `<div class="alert alert-error">❌ ${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Import";
    setTimeout(() => { progressWrap.style.display = "none"; progressBar.style.width = "0%"; }, 1000);
  }
}
