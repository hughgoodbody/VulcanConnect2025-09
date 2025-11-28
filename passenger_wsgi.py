"""WSGI entrypoint for cPanel / Passenger deployments.

This file wraps the NiceGUI ASGI app so Phusion Passenger can load it
as a standard WSGI `application` object.

Important: do **not** add ``imp.load_source`` calls here (the default
cPanel stub sometimes suggests that pattern). Loading this module from
itself triggers infinite recursion. Passenger will import this file
directly using the startup file you specify in the cPanel UI.
"""

import os
import sys

from asgiref.wsgi import ASGItoWSGI

# Ensure the repository directory is importable when Passenger spawns the app
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app as asgi_app

# Passenger expects a WSGI callable named `application`
application = ASGItoWSGI(asgi_app)
