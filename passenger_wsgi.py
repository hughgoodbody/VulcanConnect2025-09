import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import ASGI app from NiceGUI 2.x
from nicegui import app as asgi_app

from asgiref.compatibility import guarantee_single_callable
application = guarantee_single_callable(asgi_app)
