import os
from nicegui import ui
from nicegui.app import app as nicegui_app
from nicegui.ui_run_with import run_with

from frontend.ui import frontend_ui

# Register UI routes
frontend_ui()

# Create fully initialized ASGI app for uvicorn
app = run_with(
    nicegui_app,
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8051")),
    reload=False,
)

def main():
    ui.run(
        host="0.0.0.0",
        port=8051,
        reload=False,
    )

if __name__ == "__main__":
    main()
