import os
# app/config/settings.py

DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "").lower() == "true"
LOCAL_DATA_PATH = "local_json_responses"  # folder where cached responses live
#CREDS_PATH = "user_data/hugh/creds.json"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDS_PATH = os.getenv(
    "CREDS_PATH",
    os.path.join(BASE_DIR, "..", "user_data", "hugh", "creds.json")
)
API_VERSION = os.getenv("API_VERSION", "v12")
API_BASE = os.getenv("API_BASE", "https://cad.onshape.com").rstrip("/")
ONSHAPE_ACCESS_KEY = os.getenv("ONSHAPE_ACCESS_KEY")
ONSHAPE_SECRET_KEY = os.getenv("ONSHAPE_SECRET_KEY")



#BASE_DIR = os.path.dirname(os.path.dirname(__file__))
#CREDS_PATH = os.path.join(BASE_DIR, 'user_data', 'hugh', 'creds.json')
#SUPPLIER_PATH = os.path.join(BASE_DIR, 'user_data', 'hugh', 'SupplierDetails.json')
