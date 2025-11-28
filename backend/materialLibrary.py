from config.settings import API_BASE, API_VERSION, CREDS_PATH
from backend.onshape.onshape import Onshape
from backend.utils.helpers import parse_url
import traceback
import sys
import json


def get_material_library():
    try:
        onshape = Onshape(API_BASE, logging=False, creds=CREDS_PATH)
        with open("user_data/hugh/user_settings.json", "r") as f:
            material_url = json.load(f)
            material_url = material_url['Material Library']

        documentId, wvmType, wvmId, elementId = parse_url(material_url)           
      

        if wvmType == 'v':
            raise Exception("Material library currently doesn't work with versions, please change URL to point to Workspace") 
        #Combine all material libraries into one list - get elements, if element = "onshape-app/materials"
        #Get materials    
        url = f'/api/{API_VERSION}/materials/libraries/d/%s/%s/%s/e/%s' % (documentId, wvmType, wvmId, elementId) 
        method = 'GET'  
        payload = {}  
        params = {}
        materials = onshape.request(method, url, query=params, body=payload)
        materials = json.loads(materials.content)
        materials = materials['materials']
        #Create a new list of material names
        matNames=['']
        for m in materials:
            matNames.append(m['displayName'])
        return matNames
    except:
        raise Exception("Invalid Material Library URL, Please amend...") 