from nicegui import ui
from frontend.pages.home import home_page
from frontend.pages.frames_export import frames_export_page
from frontend.pages.profiles_export import profiles_export_page
from frontend.pages.batch_drawings_export import batch_drawings_export_page


def frontend_ui() -> None:
    """Register all NiceGUI pages for the application."""

    home_page()
    # frames_export_page()
    # profiles_export_page()
    # batch_drawings_export_page()
