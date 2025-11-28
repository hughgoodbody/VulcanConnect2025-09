from nicegui import ui

def download_button():
    btn = ui.button('Download All as ZIP', on_click=lambda: ui.run_javascript('window.open("/download-frames-zip", "_blank")')).props('enabled')    
    return btn

def download_drawings_button():
    btn = ui.button('Download All as ZIP', on_click=lambda: ui.run_javascript('window.open("/download-drawings-zip", "_blank")')).props('enabled')    
    return btn
