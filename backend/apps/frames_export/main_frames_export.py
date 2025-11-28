#from backend.onshape.onshape import Onshape
from backend.findFrameMembers import frameExport
from backend.csvFiles import nc1_csv, material_quantity_csv, one_d_bin_packing
from backend.build_and_zip import build_frames_export_zip
from backend.utils.stepFileFunctions import process_step_files
from backend.build_and_zip import build_frames_export_zip
import sys
import traceback


def main_frames_exporter(urlFrame, ui_state, framesUiOptions, update_notifier):
    try:
        #Find the frame bodies to export
        update_notifier('Looking for frame members')
        print('BACKEND: Looking for frame members -- main_frames_exporter')
        framesOutput = frameExport(urlFrame, ui_state, framesUiOptions)

        #Create CSV Files
        update_notifier('Creating CSV files')
        print('BACKEND: Creating CSV files -- main_frames_exporter')
        nc1File = nc1_csv(framesOutput)
        matFile, viewFile = material_quantity_csv(framesOutput)
        update_notifier('CSV Completed')
        print('BACKEND: CSV Completed -- main_frames_exporter')
        #Create step files in memory
        if framesUiOptions['STEP Option']:
            update_notifier('Getting STEP files')
            print('BACKEND: Getting STEP files -- main_frames_exporter')
            step_files = process_step_files(framesOutput)
        else:
            step_files = []
            update_notifier('No STEP files selected for process')
            print('BACKEND: No STEP files selected for process -- main_frames_exporter')


        #Create Zip file of STEP and NC1
        update_notifier('Creating ZIP file')
        print('BACKEND: Creating ZIP file -- main_frames_exporter')
        framesZipFile = build_frames_export_zip(nc1File, matFile, viewFile, step_files)
        update_notifier('ZIP file created')
        print('BACKEND: ZIP file created -- main_frames_exporter')

        #Download occurs in server_routes, accessed by the download button and decorator



        #Bin Pack
        #binFile = one_d_bin_packing(framesOutput)


        #Assign all to ui_state
        #ui_state.frames_output = framesOutput
        #ui_state.nc1_file = nc1File
        #ui_state.views_file = viewFile
        #ui_state.mat_file = matFile
        ui_state.frames_zip = framesZipFile
    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        print("Exception:", e)
        print("Type:", exc_type)
        print("Line number:", exc_tb.tb_lineno)
        traceback.print_exc()


    return