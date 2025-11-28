import os

from nicegui import ui

from frontend.ui import frontend_ui

# Register UI pages once during startup
frontend_ui()

# Expose the ASGI application for external servers (e.g., uvicorn or Passenger)
app = ui.app


def main() -> None:
    """Run the NiceGUI development server."""

    ui.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8051")),
        reload=False,
    )


if __name__ == "__main__":
    main()
