from nicegui import ui

def home_page():
    page = ui.page(path="/")
    with ui.header():
        ui.label('NiceGUI Project')
    with ui.column().classes('w-full'):
        with ui.row().classes('w-full justify-center'):
            ui.image('static/images/Logo GSFX.png').classes('w-72')    
    ui.label('Welcome to the home page!')
    ui.link('Go to Frames Export', '/frames-export')
    ui.link('Go to Profiles Export', '/profiles-export')
    ui.link('Go to Batch Drawings Export', '/batch-drawings-export')
