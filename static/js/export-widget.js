// static/js/export-widget.js

async function downloadStep(url, configuration) {
  const res = await fetch("/api/export/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, configuration }),
  });

  if (!res.ok) {
    alert("Failed to export STEP");
    return;
  }

  const blob = await res.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "model.step";
  document.body.appendChild(link);
  link.click();
  link.remove();
}

async function downloadZip(url, configuration) {
  const res = await fetch("/api/export/zip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, configuration }),
  });

  if (!res.ok) {
    alert("Failed to export ZIP");
    return;
  }

  const blob = await res.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "model.zip";
  document.body.appendChild(link);
  link.click();
  link.remove();
}
