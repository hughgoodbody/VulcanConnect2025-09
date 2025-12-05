# passenger_wsgi.py
# Entry point for cPanel / Phusion Passenger

import sys
import os

# Ensure project root is on PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app as application  # Flask WSGI app
