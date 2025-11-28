import os
from nicegui import ui

from frontend.ui import frontend_ui

# Register your UI routes once on startup
frontend_ui()

# NiceGUI 2.x ASGI app
app = ui.app

def main() -> None:
    ui.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8051")),
        reload=False,
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()
