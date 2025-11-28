from nicegui import ui
from frontend.pages.home import home_page
from frontend.pages.frames_export import frames_export_page
from frontend.pages.profiles_export import profiles_export_page
from frontend.pages.batch_drawings_export import batch_drawings_export_page

# Frontend routing setup
def frontend_ui():
    home_page()
    #frames_export_page()
    #profiles_export_page()
    #batch_drawings_export_page()

frontend_ui()
