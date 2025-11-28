from dataclasses import dataclass, field
from typing import Optional


#Variables which need to pass between multiple functions
class UIState:
    def __init__(self):
        self.config_area = None
        self.config_controls = {}
        self.frame_config_area = None
        self.frame_config_controls = {}
        self.error_output = None
        self.url_input = None
        self.tabs = None
        self.profile_tab = None
        self.uiOptions_tab = None
        self.results_tab = None        
        self.frames_output = []
        self.assembly_name = None
        self.frameStepOption = False
        self.download_button = None
        self.process_frame_button = None
        self.nc1_file = None
        self.views_file = None
        self.mat_file = None
        self.pdf = False
        self.dxf = False
        self.dwg = False  
        self.export_format_dict = {}
        self.export_progress = None
        self.generated_zip_buffer = None
        self.framesUiOptions = {}
        self.config_string = None
        self.encode_button = None
        self.process_button = None
        self.processing_done = False
        

class FrameUIState:
    def __init__(self):
        self.config_area = None
        self.config_controls = {}
        self.error_output = None
        self.url_input = None
        self.tabs = None
        self.frames_tab = None
        self.uiOptions_tab = None
        self.results_tab = None        
        self.frames_output = []
        self.assembly_name = None
        self.download_button = None
        self.process_frame_button = None
        self.results_tab = None
        self.config_string = None
        self.encode_button = None
        self.process_button = None
        self.nc1_file = None
        self.views_file = None
        self.mat_file = None
        self.step = False
        self.frames_zip = None
        self.frames_options = {}
        self.processing_done = False


class ProfilesUIState:
    def __init__(self, ui_options):
        self.config_area = None
        self.table_area = None
        self.config_controls = {}
        self.frame_config_area = None
        self.frame_config_controls = {}
        self.error_output = None
        self.url_input = None
        self.tabs = None        
        self.uiOptions_tab = None
        self.results_tab = None        
        self.assembly_name = None        
        self.download_button = None    
        self.export_progress = None
        self.generated_zip_buffer = None        
        self.config_string = None
        self.encode_button = None
        self.process_button = None
        self.processing_done = False 
        self.ui_options = ui_options