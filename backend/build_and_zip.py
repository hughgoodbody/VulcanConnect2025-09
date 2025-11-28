from datetime import date
import sys
import traceback
import zipfile
import io


def build_frames_export_zip(nc1File, matFile, viewFile, step_files):
    try:       
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # NC1, Material, and Drawing Views files
            today = date.today()
            nc1csvName = "NC1_Files_" + today.strftime("%d") + today.strftime("%m") + today.strftime("%Y")
            zipf.writestr(f'{nc1csvName}.csv', nc1File)
            zipf.writestr('Total_Material.csv', matFile)
            zipf.writestr('Drawing_Views.csv', viewFile)

            # STEP files
            for step_name, step_content in step_files:
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