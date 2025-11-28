from nicegui import ui
from frontend.configuration_encoding import encode_config

def encode_button(ui_state):
    ui.button('Encode Configurations', on_click=lambda: encode_config(ui_state))