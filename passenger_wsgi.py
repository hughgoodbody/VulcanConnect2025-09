import os
import sys
import subprocess

# --- FORCE VIRTUALENV ACTIVATION ---
VENV = "/home/cb08d76fjvq5/virtualenv/VulcanConnect2025-09/3.11/bin/activate_this.py"
with open(VENV) as f:
    exec(f.read(), {"__file__": VENV})

# --- ENSURE PROJECT IS IMPORTABLE ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- LAUNCH UVICORN ONCE ---
def application(environ, start_response):
    if not hasattr(application, 'started'):
        application.started = True
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1",
            "--port", "8051"
        ])

    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b"Starting ASGI server..."]
