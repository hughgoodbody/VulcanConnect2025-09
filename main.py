import os
from nicegui import ui

from frontend.ui import frontend_ui

# Register UI pages once
frontend_ui()

# ASGI app (for uvicorn)
app = ui.app


def main():
    # Local development runner
    ui.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8051")),
        reload=False,
    )


# Passenger/uvicorn imports this module as "main",
# so __name__ is NOT "__main__" and ui.run() should NOT run here.
# Local dev still works.
if __name__ == "__main__":
    main()
