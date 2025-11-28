from nicegui import ui, app

@ui.page("/")
def index():
    ui.label("Hello from NiceGUI on Passenger!")

# IMPORTANT:
# DO NOT call ui.run() when deploying under uvicorn.
# Passenger starts uvicorn and uvicorn loads app directly.
