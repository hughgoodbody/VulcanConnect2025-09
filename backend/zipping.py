from datetime import date
import io
import zipfile
import sys
import traceback
from backend.utils.stepFileFunctions import download_step_file_to_memory



def build_frames_export_zip(nc1File, matFile, viewFile, frames_output):
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            #print(frames_output)
            today = date.today()
            nc1csvName = "NC1_Files_" + today.strftime("%d") + today.strftime("%m")+ today.strftime("%Y") + ".csv"
            zipf.writestr(f'{nc1csvName}.csv', nc1File)            
            zipf.writestr('Total_Material.csv', matFile)
            zipf.writestr('Drawing_Views.csv', viewFile)
            # STEP files
            for frame in frames_output:
                if frame.href:
                    href = frame.href
                    docid = frame.document_info.documentId
                    filename = frame.file_name
                    if href and docid:
                        step_name, step_content = download_step_file_to_memory(href, filename, docid)
                        if step_content:
                            zipf.writestr(step_name, step_content)
        zip_buffer.seek(0)

    except Exception as e:
                exc_type, exc_value, exc_tb = sys.exc_info()
                print("Exception:", e)
                print("Type:", exc_type)
                print("Line number:", exc_tb.tb_lineno)
                traceback.print_exc()
                return {
                    "Error": str(e),
                    "Information": 'ERROR IN ZIP FILE CREATION',
                    "Module": __name__,
                    "Function": "build_frames_export_zip",
                    "Line Number": e.__traceback__.tb_lineno
                }    
    return zip_buffer.read()


def build_profiles_export_zip():
     return

def build_drawings_export_zip():
     return