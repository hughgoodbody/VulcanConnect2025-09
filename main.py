from nicegui import ui

print(">>> NiceGUI imported from:", ui.__file__)
print(">>> NiceGUI version:", ui.__version__)

@ui.page("/")
def index():
    ui.label("Hello from Passenger + NiceGUI")

# THIS is the FastAPI ASGI app Passenger must serve:
app = ui.app
