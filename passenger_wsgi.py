import os
import sys
import subprocess

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Start uvicorn server inside Passenger
def application(environ, start_response):
    # Start uvicorn only once
    if not hasattr(application, 'started'):
        application.started = True
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1",
            "--port", "8051"
        ])

    # Respond to Passenger health checks
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b"Starting ASGI server..."]
