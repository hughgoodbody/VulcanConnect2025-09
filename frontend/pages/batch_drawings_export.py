from nicegui import ui
import asyncio
import sys
import traceback
from frontend.components.download_button import download_drawings_button
from backend.apps.batch_drawings.main_batch_drawings import export_drawings_to_memory_zip
from backend.schema.cls_ui_schema import UIState
from frontend import state


ui_state = UIState()
@ui.page('/batch-drawings-export')
def batch_drawings_export_page():
    with ui.header():
        ui.label('Batch Drawings Export')
    with ui.column().classes('w-full'):
        with ui.row().classes('w-full justify-center'):
            ui.image('static/images/Logo GSFX.png').classes('w-72')         
    ui.link('Back to Home', '/')
    ui.label('Paste Onshape Document URL:').classes('font-bold text-lg')
    
    ui.input(placeholder='https://cad.onshape.com/documents/...').classes('w-full').bind_value(ui_state, 'url_input')  
    
     
    ui.label('Select Drawing Formats')

    ui_state.export_format_dict = {
        'PDF': True,
        'DXF': True,
        'DWG': True,
    }

    # direct binding (no value=… param; binding sets initial + keeps in sync)
    ui.checkbox('PDF').bind_value(ui_state, 'pdf')
    ui.checkbox('DXF').bind_value(ui_state, 'dxf')
    ui.checkbox('DWG').bind_value(ui_state, 'dwg')
    ui.button('EXPORT DRAWINGS', on_click=start_export_task).classes('mt-4')

    ui_state.export_progress = ui.linear_progress(value=0).props('show-value precision=0').classes('w-full')   # show "42%" with no decimals
    ui_state.progress_label = ui.label('0%')

    #download_drawings_button()

async def start_export_task():        
    # build formats dict from the bound booleans
    export_formats = {'PDF': ui_state.pdf, 'DXF': ui_state.dxf, 'DWG': ui_state.dwg}
    n = ui.notification(timeout=None)
    n.message = 'Getting Drawings'
    n.spinner = True
    n.position = 'center'


    def update_notifier(notification):
        n.message = notification  

    def update_progress(completed, total):
        frac = completed / max(total, 1)
        ui_state.export_progress.set_value(frac)
        ui_state.progress_label.text = f'{int(frac*100)}%'
        n.message = f"Exporting Drawing {completed} of {total}"


    await asyncio.sleep(0.1)
    try:
        await asyncio.to_thread(process_drawings, ui_state.url_input, ui_state, export_formats, update_notifier, update_progress)
        update_notifier('Done!')
        n.spinner = False
        #ui_state.process_button.visible = False
        #ui_state.download_button.visible = True
        # Enable the download button now
            # Reactive state update
        ui_state.processing_done = True  # <--- triggers button enable automatically
        await asyncio.sleep(1)

        ui.run_javascript('window.open("/download-drawings-zip", "_blank")')   

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

def process_drawings(url_input, ui_state, export_formats, update_notifier, update_progress):
    print(f'URL:{url_input}')
    print(f'Exporting drawings, {export_formats}')
    drawingData = export_drawings_to_memory_zip(url_input, export_formats, update_notifier, update_progress)  # Optional callback for progress updates
    #Generated zip buffer saved to ui state to be accesses through routes by the download button
    ui_state.generated_zip_buffer = drawingData
    state.latest_drawings_output = ui_state 
    
    
    return