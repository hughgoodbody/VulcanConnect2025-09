import os
from nicegui import ui, app as nicegui_app
from nicegui import ui_run_with

from frontend.ui import frontend_ui

# Register UI routes
frontend_ui()

# This creates the ASGI app with full NiceGUI initialization
app = ui_run_with(
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
