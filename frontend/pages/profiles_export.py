from nicegui import ui
from frontend.components.download_button import download_button
from backend.configuration_handling.configHandler import get_configurations
from frontend.configuration_display import configuration_display
from backend.schema.cls_ui_schema import ProfilesUIState
from backend.schema.cls_ui_options_schema import UserOptions
import json
from frontend.table_display import table_display
from backend.materialLibrary import get_material_library


ui_options = UserOptions()
ui_state = ProfilesUIState(ui_options)

@ui.page('/profiles-export')
def profiles_export_page():
    with ui.header():
        ui.label('Profiles Export')
    with ui.column().classes('w-full'):
        with ui.row().classes('w-full justify-center'):
            ui.image('static/images/Logo GSFX.png').classes('w-72')     
    ui.link('Back to Home', '/')
    ui.label('Paste Onshape Document URL:').classes('font-bold text-lg')
    url_input = ui.input(placeholder='https://cad.onshape.com/documents/...').classes('w-full')
    ui.label('Have you assigned all part numbers?').classes('font-bold text-lg')
    find_button = ui.button('Find Configurations')
    search_button = ui.button('Find Profiles')
    tab = ui.tab('Results')
    with ui.row().classes('w-full justify-center flex-nowrap'):
        options_page(ui_state)
    def find_and_display():
        #TEST URL
        #url_input.value = "https://cad.onshape.com/documents/b86b36176abab19222a08b65/w/eff05c25870425deb186d6fc/e/16d4fc235a86612d2290645b"        
        results = get_configurations(url_input.value)
        ui_state.url_input = url_input.value
        #Display the configuration options
        configuration_display(results, ui_state)
        
        
        
        #Encode the configuration options to a string for further processing
        #encode_button(ui_state)    
        

    find_button.on_click(find_and_display)
    search_button.on_click(process)
    download_button()
    

def process():
    print(f'Processing:')
    print(ui_state.ui_options)
    #Static data in json format to aid in coding rather than constant api calls
    with open("development/nicegui_table_app/data.json", "r") as f:
        profileData = json.load(f)
    #Get the materials library for the user
    materials = get_material_library()
    table_display(profileData, materials, ui_state.undersize_options)
    
    #print(materials)

def options_page(ui_state):
    # Load supplier names from JSON
    with open("user_data/hugh/SupplierDetails.json", "r") as f:
        suppliers = json.load(f)

    supplier_names = [s["Name"] for s in suppliers]
    with ui.column().classes('w-1/4 items-start'):
        ui.label('Hole Options:')
        ui_state.undersize_options = [
    'Ignore thickness / diameter ratio',
    'Etch undersize holes',
    'Drill undersize holes',
]
        ui.radio(ui_state.undersize_options, value='Ignore thickness / diameter ratio')
        
    with ui.column().classes('w-1/4 items-start'):
        ui.label('Marking Options:')
        ui.checkbox('Etch component part number').bind_value(ui_options, 'etch_component_part_number') 
        ui.checkbox('Etch bend line marks').bind_value(ui_options, 'etch_bend_line_marks') 
    with ui.column().classes('w-1/4 items-start'):
        ui.label('Other Options:')
        ui.checkbox('Create contact sheet', value=True).bind_value(ui_options, 'create_contact_sheet')        
        ui.checkbox('Create CSV file', value=True).bind_value(ui_options, 'create_csv_file') 
        ui.checkbox('Upload results to Onshape').bind_value(ui_options, 'upload_results_to_onshape') 
    with ui.column().classes('w-1/4 items-start'):
        ui.input('Multiplier', value=1).bind_value(ui_options, 'multiplier') 
        ui.number('Max Thickness', value=25).bind_value(ui_options, 'max_thickness') 
        ui.select(supplier_names, label='Default Supplier', value=supplier_names[0]).bind_value(ui_options, 'supplier') 
        
        
        #ui.button('Find Profiles', on_click=lambda: process_profile_exporter(ui_state)).classes('mt-2')
        