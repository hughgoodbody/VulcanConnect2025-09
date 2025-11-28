import os
import asyncio
from nicegui import ui

from frontend.ui import frontend_ui

# Register UI pages once
frontend_ui()

app = ui.app   # ASGI app that uvicorn will serve


@ui.on_startup
async def startup():
    """Manually perform NiceGUI initialization when uvicorn starts."""
    await ui.run_async(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8051")),
        reload=False,
    )


def main():
    """Local development server (not used on Passenger)."""
    ui.run(
        host="0.0.0.0",
        port=8051,
        reload=False,
    )


if __name__ == "__main__":
    main()
