from nicegui import ui
import asyncio
from frontend.components.download_button import download_button
from backend.configuration_handling.configHandler import get_configurations
from backend.schema.cls_ui_schema import FrameUIState
from frontend.configuration_display import configuration_display
from frontend.components.encode_button import encode_button
from backend.apps.frames_export.main_frames_export import main_frames_exporter
from frontend.configuration_encoding import encode_config
import sys
import traceback
from frontend import state
from backend import routes


framesUiOptions = {'STEP Option': False}
config_controls = {}

ui_state = FrameUIState()
@ui.page('/frames-export')
def frames_export_page():
    with ui.header():
        ui.label('Frames Export')
    with ui.column().classes('w-full'):
        with ui.row().classes('w-full justify-center'):
            ui.image('static/images/Logo GSFX.png').classes('w-72')         
    ui.link('Back to Home', '/')
    ui.label('Paste Onshape Document URL:').classes('font-bold text-lg')    
    url_input = ui.input(placeholder='https://cad.onshape.com/documents/...').classes('w-full')
    ui.label('Have you assigned all part numbers?').classes('font-bold text-lg')
    find_button = ui.button('Find Configurations')
    
    
    def find_and_display():
        #TEST URL
        #url_input.value = "https://cad.onshape.com/documents/b86b36176abab19222a08b65/w/eff05c25870425deb186d6fc/e/16d4fc235a86612d2290645b"        
        results = get_configurations(url_input.value)
        ui_state.url_input = url_input.value
        #Display the configuration options
        configuration_display(results, ui_state)
        
        stepCheck = ui.checkbox('Export .STEP file of frame members').bind_value(ui_state, 'step') # direct binding (no value=… param; binding sets initial + keeps in sync)     
        
        print(ui_state.step)
        #Encode the configuration options to a string for further processing
        #encode_button(ui_state)    
        process_button = ui.button('Process Frames', on_click=lambda: async_processing(ui_state.url_input, ui_state, stepCheck))
        download_button()
        

    async def async_processing(urlFrame, ui_state, stepCheck):
        #print(stepCheck.value)
        #Update the step value - could remove the dictionary here, or put the dict in ui_state for access later
        #need to do it here, because the checkbox is not inside a 'with' statement.
        ui_state.step = stepCheck.value
        framesUiOptions['STEP Option'] = ui_state.step 
        n = ui.notification(timeout=None)
        n.message = 'Processing Frames'
        n.spinner = True
        n.position = 'center'


        def update_notifier(notification):
            n.message = notification            
        await asyncio.sleep(0.1)
        try:
            await asyncio.to_thread(encode_and_process, urlFrame, ui_state, update_notifier)
            update_notifier('Done!')
            n.spinner = False
            #ui_state.process_button.visible = False
            #ui_state.download_button.visible = True
            # Enable the download button now
             # Reactive state update
            ui_state.processing_done = True  # <--- triggers button enable automatically
            await asyncio.sleep(1)
        except Exception as e:
            exc_type, exc_value, exc_tb = sys.exc_info()
            n.message = f'❌ Error: {e}'
            n.spinner = False
            exc_type, exc_value, exc_tb = sys.exc_info()
            print("Exception:", e)
            print("Type:", exc_type)
            print("Line number:", exc_tb.tb_lineno)
            traceback.print_exc()
            await ui.sleep(2)
        finally:
            n.dismiss()

    

        
    def encode_and_process(urlFrame, ui_state, update_notifier):
        print('FRONTEND: encode_and_process COMPLETED')
        #Encode configuration here
        encode_config(ui_state, update_notifier)
        print('FRONTEND: encode_config COMPLETED')
        #Run backend task here to process the frames
        #framesUiOptions['STEP Option'] = True
        print(framesUiOptions)
        main_frames_exporter(urlFrame, ui_state, framesUiOptions, update_notifier)
        print('FRONTEND: main_frames_exporter COMPLETED')
        #ui.notify("Processing frames")  
        update_notifier("Processing frames Completed")
        #Update state
        state.latest_frames_output = ui_state
        return
     
    find_button.on_click(find_and_display)
    
    
    
