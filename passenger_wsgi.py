import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import ASGI app from NiceGUI
from nicegui import app as asgi_app

# Real ASGI → WSGI adapter from Starlette
from starlette.middleware.wsgi import WSGIMiddleware

application = WSGIMiddleware(asgi_app)
