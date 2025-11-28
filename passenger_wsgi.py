"""WSGI entrypoint for cPanel / Passenger deployments.

This file wraps the FastAPI ASGI app so Phusion Passenger can load it
as a standard WSGI `application` object.

Important: do **not** add ``imp.load_source`` calls here (the default
cPanel stub sometimes suggests that pattern). Loading this module from
itself triggers infinite recursion. Passenger will import this file
directly using the startup file you specify in the cPanel UI.
"""

import os
import site
import sys

# Ensure the repository directory is importable when Passenger spawns the app
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Ensure the app sees the virtualenv site-packages even if Passenger does not
VENV = os.environ.get("VIRTUAL_ENV")
if VENV:
    site_packages = os.path.join(
        VENV,
        "lib",
        f"python{sys.version_info.major}.{sys.version_info.minor}",
        "site-packages",
    )
    site.addsitedir(site_packages)

from asgiref.wsgi import ASGItoWSGI

from main import app as asgi_app

# Passenger expects a WSGI callable named `application`
application = ASGItoWSGI(asgi_app)
