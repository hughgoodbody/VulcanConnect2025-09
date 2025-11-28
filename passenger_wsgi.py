import os
import sys

# Activate venv
VENV = "/home/cb08d76fjvq5/virtualenv/VulcanConnect2025-09/3.11/bin/activate_this.py"
with open(VENV) as f:
    exec(f.read(), {"__file__": VENV})

# Ensure project dir is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import the ASGI app *directly*
from main import app
