// Drag-and-drop setup
["mf", "rk"].forEach(prefix => {
  const zone = document.getElementById(`${prefix}-zone`);
  const fileInput = document.getElementById(`${prefix}-file`);
  const label = document.getElementById(`${prefix}-filename`);

  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) label.textContent = fileInput.files[0].name;
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
    }
  });
});

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
  btn.textContent = "Uploading…";
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
      .map(([k, v]) => `${v} ${k} skipped (duplicates)`)
      .join(", ");

    resultBox.innerHTML = `
      <div class="alert alert-success">
        ✅ Imported ${lines}.
        ${skipLines ? `<br><small>${skipLines}</small>` : ""}
      </div>`;
  } catch (e) {
    resultBox.innerHTML = `<div class="alert alert-error">❌ ${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Upload & Import";
    setTimeout(() => { progressWrap.style.display = "none"; progressBar.style.width = "0%"; }, 1000);
  }
}
