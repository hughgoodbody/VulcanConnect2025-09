# VulcanConnect Web Hosting

This repository now exposes the existing CAD processing logic as a headless FastAPI service. The front end can be built entirely in WordPress (e.g., with Elementor) and talk to this API over HTTPS.

## Architecture overview
- **FastAPI backend (`main.py`)**: Provides `/api/frames/export` (frames + STEP option), `/api/drawings/export` (PDF/DWG/DXF per drawing), a placeholder `/api/profiles/export` (wire now, fill in when backend logic exists), and `/health` for uptime checks.
- **WSGI adapter (`passenger_wsgi.py`)**: Lets cPanel/Passenger load the ASGI app without touching the Python code.
- **Existing processing logic**: The `backend/` folder is unchanged and is invoked by the API endpoint.

## Local development
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API locally:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8051
   ```
4. Test the health check:
   ```bash
   curl http://localhost:8051/health
   ```
5. Trigger a frame export (replace the URL with a real Onshape document URL):
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -o Frames_Export.zip \
     -d '{"document_url": "https://cad.onshape.com/documents/...", "export_step": true}' \
     http://localhost:8051/api/frames/export
   ```
6. Trigger a batch drawings export (PDF + DWG by default):
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -o Drawings_Export.zip \
     -d '{"document_url": "https://cad.onshape.com/documents/...", "export_pdf": true, "export_dwg": true, "export_dxf": false}' \
     http://localhost:8051/api/drawings/export
   ```

## Deploying on cPanel (Phusion Passenger)
1. In **Setup Python App**, create (or select) a virtual environment and note the **Application root**.
2. Upload/clone this repo into that application root.
3. Set **Application startup file** to `passenger_wsgi.py`. Keep **Application entry point** as `application`.
4. Ensure the app sees your virtualenv:
   - cPanel typically sets `VIRTUAL_ENV` automatically; `passenger_wsgi.py` uses it to add `site-packages` to `sys.path`.
   - If you see `ModuleNotFoundError`, confirm `VIRTUAL_ENV` points to your venv or recreate the app via **Setup Python App**.
5. Open the cPanel terminal for the app, activate the venv if needed, and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Click **Restart** in the cPanel UI. Passenger will import `passenger_wsgi.py`, wrap the FastAPI app, and serve it on your domain.
7. Verify deployment:
   ```bash
   curl -s https://yourdomain.com/health
   ```

## Connecting Elementor (WordPress) to the API
You can keep the visual UI in WordPress while this backend handles the heavy processing. Two common patterns:

### 1) Elementor Form webhook (no custom plugin required)
1. In Elementor, add a **Form** widget with fields for the Onshape URL and a checkbox for exporting STEP files.
2. Under **Actions After Submit**, add **Webhook**.
3. Set **Webhook URL** to your API endpoint, e.g., `https://yourdomain.com/api/frames/export` (frames) or `https://yourdomain.com/api/drawings/export` (drawings). Wire `/api/profiles/export` now; it returns HTTP 501 until backend logic is added.
4. Set **Request Method** to `POST` and **Content Type** to `application/json`.
5. Map fields to JSON body:
   ```json
   {
     "document_url": "[field id=onshape_url]",
     "export_step": "[field id=export_step]"
   }
   ```
6. Elementor will POST to the API; the response is a ZIP stream. Configure Elementor to **Redirect After Submit** to the webhook response URL or handle the download via a small JavaScript snippet (see pattern 2).

### 2) JavaScript fetch + download button
Embed a Code widget (or a small custom plugin) in Elementor and use `fetch` to POST to the API and download the ZIP:
```html
<button id="export-btn">Generate ZIP</button>
<input id="doc-url" placeholder="https://cad.onshape.com/documents/..." />
<label><input type="checkbox" id="export-step" /> Include STEP</label>
<script>
  const download = async () => {
    const response = await fetch('/api/frames/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_url: document.querySelector('#doc-url').value,
        export_step: document.querySelector('#export-step').checked
      })
    });
    if (!response.ok) { alert('Export failed'); return; }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'Frames_Export.zip';
    a.click();
    window.URL.revokeObjectURL(url);
  };
  document.querySelector('#export-btn').addEventListener('click', download);
</script>
```

To target drawings instead, POST to `/api/drawings/export` with body fields `document_url`, `export_pdf`, `export_dwg`, and `export_dxf`.

### Troubleshooting tips
- **CORS**: The API allows all origins by default (`CORSMiddleware`), so WordPress pages on the same domain work without changes. If hosting the API on a different domain, set `allow_origins` in `main.py` to that domain.
- **Time limits**: If exports take time, ensure your hosting plan allows long-running requests. Consider adding background task handling if needed.
- **Logging**: Passenger logs usually appear in `~/logs/` or the app root; FastAPI progress messages are appended to the `X-Export-Progress` response header.

## Files to know
- `main.py`: FastAPI app with `/api/frames/export`, `/api/drawings/export`, placeholder `/api/profiles/export`, and `/health`.
- `passenger_wsgi.py`: Adapter so cPanel/Passenger can load the ASGI app.
- `backend/`: Existing processing code (CSV generation, STEP handling, ZIP creation). No front-end dependencies remain.
