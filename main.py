from nicegui import ui

@ui.page("/")
def index():
    ui.label("Hello from NiceGUI + Passenger!")

app = ui.run(return_app=True)
