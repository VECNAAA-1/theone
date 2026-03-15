// upload.js

let selectedFile = null;

async function analyzeText() {
  const raw = document.getElementById("feedback-text").value.trim();
  if (!raw) { showError("Please enter at least one feedback item."); return; }
  const lines = raw.split("\n").map(l => l.trim()).filter(Boolean);
  if (!lines.length) { showError("No valid feedback lines found."); return; }

  showLoading();
  try {
    const res  = await fetch("/api/analyze/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback: lines }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Analysis failed.");
    saveResults(data);
    window.location.href = "/results";
  } catch(err) {
    hideLoading();
    showError(err.message);
  }
}

function clearText() { document.getElementById("feedback-text").value = ""; }

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) setFile(file);
}

function setFile(file) {
  selectedFile = file;
  const info = document.getElementById("file-info");
  info.textContent = `📄 ${file.name}  (${(file.size/1024).toFixed(1)} KB)`;
  info.classList.remove("hidden");
  document.getElementById("upload-btn-row").style.display = "flex";
}

function resetFile() {
  selectedFile = null;
  document.getElementById("file-input").value = "";
  document.getElementById("file-info").classList.add("hidden");
  document.getElementById("upload-btn-row").style.display = "none";
}

async function analyzeFile() {
  if (!selectedFile) { showError("Please select a file first."); return; }
  const formData = new FormData();
  formData.append("file", selectedFile);
  showLoading();
  try {
    const res  = await fetch("/api/analyze/file", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Analysis failed.");
    saveResults(data);
    window.location.href = "/results";
  } catch(err) {
    hideLoading();
    showError(err.message);
  }
}

const dz = document.getElementById("dropzone");
if (dz) {
  dz.addEventListener("dragover",  e => { e.preventDefault(); dz.classList.add("dragover"); });
  dz.addEventListener("dragleave", ()=> dz.classList.remove("dragover"));
  dz.addEventListener("drop", e => {
    e.preventDefault(); dz.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) { document.getElementById("file-input").files = e.dataTransfer.files; setFile(file); }
  });
}
