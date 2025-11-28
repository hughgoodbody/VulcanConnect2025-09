import os
import json
from onshape import Onshape


'''Due to multiple options of List, Variable and Boolean configurations, configurations need to be encoded so the correct
configuration is addressed'''

def encodeConfiguration(document_info: dict) -> str:
    did = documentInfo['Document Id']
    eid = documentInfo['Element Id']
    url = '/api/v5/elements/d/%s/e/%s/configurationencodings' % (did, eid)