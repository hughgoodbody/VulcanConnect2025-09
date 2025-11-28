import os
from nicegui import app
from frontend.ui import frontend_ui

# Register UI routes on startup
frontend_ui()

def main() -> None:
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8051")),
        reload=False,
    )

if __name__ == "__main__":
    main()
