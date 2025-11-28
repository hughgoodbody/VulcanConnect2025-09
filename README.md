# VulcanConnect Web Hosting

This repository contains a NiceGUI-based application. The previous local entry point has been refactored so it can run both locally and on a shared web host (e.g., cPanel).

## Local development
1. Create and activate a virtual environment.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the app (optionally overriding the host/port):
   ```bash
   HOST=0.0.0.0 PORT=8051 python main.py
   ```

## Deploying on cPanel (Phusion Passenger)
1. In **Setup Python App**, create (or select) a virtual environment.
2. Upload/clone this repo into the **Application root** shown in cPanel (the same folder where cPanel will look for the startup file).
3. Set the **Application startup file** to `passenger_wsgi.py`. Leave the **Application entry point** as `application` (Passenger looks for this name by default). If cPanel pre-populated the file with a default stub that calls ``imp.load_source`` on `passenger_wsgi.py`, delete that content and replace it with the `passenger_wsgi.py` from this repo—using ``imp`` to reload this same file causes infinite recursion.
4. Open the cPanel terminal for that app, activate the environment if needed, and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Click **Restart** in the cPanel UI. Passenger will import `passenger_wsgi.py`, which wraps the NiceGUI ASGI app from `main.py` and serves it on your domain.
6. Optional: for troubleshooting you can start the ASGI app yourself (e.g., over SSH) with:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8051 --proxy-headers --forwarded-allow-ips="*"
   ```

These steps allow the same codebase to work locally and on the web host without extra manual tweaks.
