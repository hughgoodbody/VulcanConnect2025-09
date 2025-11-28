from nicegui import ui
import nicegui  # <-- needed for __version__

print(">>> NiceGUI imported from:", ui.__file__)
print(">>> NiceGUI version:", nicegui.__version__)

@ui.page("/")
def index():
    ui.label("Hello from NiceGUI on Passenger!")

app = ui.app
