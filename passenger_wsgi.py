import os
import sys

# Make sure this directory is on the Python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import the ASGI app from main.py
from main import app as asgi_app

# Modern compatible ASGI → WSGI wrapper
from asgiref.compatibility import guarantee_single_callable

# Passenger requires a WSGI-level `application`
application = guarantee_single_callable(asgi_app)
