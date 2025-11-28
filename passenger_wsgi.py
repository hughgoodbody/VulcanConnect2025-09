import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

VENV = "/home/cb08d76fjvq5/virtualenv/VulcanConnect2025-09/3.11/bin/activate_this.py"
with open(VENV) as f:
    exec(f.read(), {"__file__": VENV})

# Start uvicorn once
if not hasattr(sys, "_uvicorn_started"):
    sys._uvicorn_started = True
    subprocess.Popen([
        sys.executable,
        "-m", "uvicorn",
        "main:app",
        "--host", "127.0.0.1",
        "--port", "8051",
    ])

def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"ASGI server running"]
