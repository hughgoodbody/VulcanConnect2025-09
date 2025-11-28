from nicegui import ui
print(">>> PASSENGER IMPORTED NICEGUI FROM:", nicegui.__file__)
print(">>> NICEGUI VERSION:", getattr(nicegui, '__version__', '(no version)'))
from nicegui.app import app as nicegui_app
from nicegui.ui_run_with import run_with

from frontend.ui import frontend_ui

# Register your UI pages
frontend_ui()

# Create the ASGI app NiceGUI exposes, initialized for embedding
app = run_with(nicegui_app)
