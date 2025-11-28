import json
import traceback
import sys
from backend.onshape.onshape import Onshape
from backend.error_handling.error_handler import log_exception
from config.settings import CREDS_PATH, API_VERSION, API_BASE
from backend.utils.helpers import parse_url


@log_exception(API_BASE, '/api/{API_VERSION}/elements/d/{did}/{wvm_type}/{wid}/e/{eid}/configuration', 'configHandler.py', 'get_configurations')
def get_configurations(doc_url):
    if not doc_url:
        raise ValueError("Document URL is empty.")

    try:

        did, wvm_type, wid, eid =  parse_url(doc_url)
                        
        onshape = Onshape('https://cad.onshape.com', logging=False, creds=CREDS_PATH)
        url = f'/api/{API_VERSION}/elements/d/{did}/{wvm_type}/{wid}/e/{eid}/configuration'
        config_data = onshape.request('GET', url).json()  # This returns a dict directly
        print('BACKEND: get_configurations COMPLETED') 
        return config_data  # ✅ Return the full configuration structure

    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        print("Exception:", e)
        print("Type:", exc_type)
        print("Line number:", exc_tb.tb_lineno)
        traceback.print_exc()
        return {
            "Error": str(e),
            "API Call": url if 'url' in locals() else 'N/A',
            "Module": __name__,
            "Function": "get_configurations",
            "Line Number": e.__traceback__.tb_lineno
        }

'''Due to multiple options of List, Variable and Boolean configurations, configurations need to be encoded so the correct
configuration is addressed'''

@log_exception(API_BASE, '/api/{API_VERSION}/elements/d/{did}/{wvm_type}/{wid}/e/{eid}/configurationencodings', 'configHandler.py', 'encode_configuration_string')
def encode_configuration_string(doc_url, config_payload):
    try:
        did, wvm_type, wid, eid =  parse_url(doc_url)

        onshape = Onshape('https://cad.onshape.com', logging=False, creds=CREDS_PATH)
        url = f'/api/{API_VERSION}/elements/d/{did}/e/{eid}/configurationencodings'

        # ✅ Ensure body is JSON-encoded and headers are set
        body = json.dumps({ "parameters": config_payload })
        headers = {'Content-Type': 'application/json'}
        response = onshape.request('POST', url, headers=headers, body=body)
        print('BACKEND: Configuration String Encode COMPLETED')        
        return json.loads(response.content).get("encodedId", "")

    except Exception as e:
        raise RuntimeError(f"Failed to encode configuration string: {str(e)}")