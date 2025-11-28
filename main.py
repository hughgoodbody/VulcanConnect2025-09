from nicegui import ui
from nicegui.app import app as nicegui_app
from nicegui.ui_run_with import run_with

from frontend.ui import frontend_ui

# Register your UI pages
frontend_ui()

# Create the ASGI app NiceGUI exposes, initialized for embedding
app = run_with(nicegui_app)
