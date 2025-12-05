import os
# app/config/settings.py

DEVELOPMENT_MODE = True  # ❗ Set to False to use real Onshape API
LOCAL_DATA_PATH = "local_json_responses"  # folder where cached responses live
CREDS_PATH = "creds.json"
API_VERSION = 'v12'
API_BASE = 'https://cad.onshape.com'

#BASE_DIR = os.path.dirname(os.path.dirname(__file__))
#CREDS_PATH = os.path.join(BASE_DIR, 'user_data', 'hugh', 'creds.json')
#SUPPLIER_PATH = os.path.join(BASE_DIR, 'user_data', 'hugh', 'SupplierDetails.json')
