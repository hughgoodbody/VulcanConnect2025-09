import traceback
import sys
from pprint import pprint
from backend.onshape.onshape import Onshape
from backend.utils.helpers import parse_url, update_metadata, get_step_url
from backend.bom.assembly_bom import get_bom, dedupe_bom_by_source, get_quantity_header_id
from config.settings import CREDS_PATH, API_BASE, API_VERSION
from backend.schema.cls_frame_schema import FrameBodyInfo
from backend.customFeatures_featurescripts.featureNamespaces import FRAME_NAMESPACE



def determine_profile(description):
    if "UC" in description or "UB" in description:
        return "I"
    if "EA" in description or "UEA" in description or "Angle" in description:
        return "L"
    if "SHS" in description or "RHS" in description:
        return "M"
    if "CHS" in description:
        return "RO"
    if "PFC" in description or "Channel" in description:
        return "U"
    return ""
    

def update_part_metadata(onshape, frame):
    #Property ID's found in Onshape company settings
    propertyDict = {"properties":[]}
    #Composite Part Number
    #propertyDict['properties'].append({"propertyId": "66c2ec9fbd44901870681756", "value": part['Composite Part Number']})
    #Primitive Part Number
    #propertyDict['properties'].append({"propertyId": "66c2ec3bf7a696613af37f7c", "value": part['Primitive Part Number']})
    #Frame Quantity
    propertyDict['properties'].append({"propertyId": "66c4bcdaf7a696613a47dfa5", "value": int(frame.table_info.qty) * int(frame.quantities.bom_qty)})
    #Description
    propertyDict['properties'].append({"propertyId": "57f3fb8efa3416c06701d60e", "value": frame.table_info.description})
    #Part Number
    #if not part['Primitive Part Number']:
    #propertyDict['properties'].append({"propertyId": "57f3fb8efa3416c06701d60f", "value": part['partNumber']})
    #Sets Frame Part Number
    propertyDict['properties'].append({"propertyId": "6888fa86dc4e0d2fa7e55bbe", "value": frame.table_info.part_number})

    #Update metadata
    #pprint(f'Property Dictionary: {propertyDict}')
    update_metadata(onshape, frame.document_info.documentId , frame.document_info.wvmType, frame.document_info.wvmId, frame.document_info.elementId, frame.table_info.original_body_id, frame.document_info.configuration, 'p', propertyDict)


def frameExport(urlFrame, ui_state, framesUiOptions):
    try:
        framesOutput = []
        delete_feature = []
        onshape = Onshape(API_BASE, logging=False, creds=CREDS_PATH)
        documentId, wvmType, wvmId, elementId =  parse_url(urlFrame)        
        filtered_bom = get_bom(onshape, documentId, wvmType, wvmId, elementId)
        #pprint(filtered_bom)

        #Get discrete Part Studios to add API Frame Search feature to
        partStudios = dedupe_bom_by_source(filtered_bom)       
        print(f"PART STUDIOS TO SEARCH: {len(partStudios)}")

        #Create API Frame Search feature in each part studio
        for ps in partStudios:        
            url = f"/api/{API_VERSION}/partstudios/d/{ps['itemSource']['documentId']}/{ps['itemSource']['wvmType']}/{ps['itemSource']['wvmId']}/e/{ps['itemSource']['elementId']}/features"
            body = {    "btType": "BTFeatureDefinitionCall-1406",
                        "feature":{
                        "btType": "BTMFeature-134",
                        "returnAfterSubfeatures": False,
                        "subFeatures": [],
                        "namespace": FRAME_NAMESPACE,
                        "name": "API Frame Search 1",
                        "suppressed": False,
                        "parameters": [],
                        "featureId": "F1dw2h5I4K62kIi_3",
                        "nodeId": "MAI0J64gQKbjuztkw",
                        "featureType": "apiFrameSearch",
                        "suppressionState": None
                        }
        }
            resp = onshape.request('POST', url, body=body).json()
            feature_id = resp.get('feature', {}).get('featureId', None)
            if feature_id:            
                delete_feature.append({
                    'documentId': ps['itemSource']['documentId'],
                    'wvmType': ps['itemSource']['wvmType'],
                    'wvmId': ps['itemSource']['wvmId'],
                    'elementId': ps['itemSource']['elementId'],
                    'featureId': feature_id

                })
        
        #Get the quantity Header id value
        qtyId = get_quantity_header_id(filtered_bom)    

        #For each item in bom, find the part id in the table of the part studio directed to
        for part in filtered_bom['rows']:
            #Get the table data
            url = f"/api/{API_VERSION}/partstudios/d/{ps['itemSource']['documentId']}/{ps['itemSource']['wvmType']}/{ps['itemSource']['wvmId']}/e/{ps['itemSource']['elementId']}/fstable"
            params = {
                    "tableNamespace": FRAME_NAMESPACE,
                    "tableType": "APITable",
                    }
            tableData = onshape.request('GET', url, query=params).json()
            #pprint(tableData)  
            # No table found  
            if tableData.get('status') == 400:
                continue

            # Get the id to lookup  
            lookupId = part['itemSource']['partId']  
            print(f"LOOKUP ID: {lookupId}, {part['itemSource']['elementId']}")
            #pprint(
            # Extract the rows from the first table
            table = tableData['tables'][0]
            rows = table['rows']
            pprint(f"TABLE ROWS: {rows}")
            # Filter rows where CutListBodyId == lookupId
            cutlist_matches = [row['columnIdToValue'] for row in rows if row['columnIdToValue'].get('cutlistbodyid') == lookupId]
            pprint(f"CUTLIST MATCHES: {cutlist_matches}")
            if cutlist_matches:   
                # Add 'BOM Qty' to each matching row
                for row in cutlist_matches:
                    frameBody = FrameBodyInfo()                    
                    frameBody.assembly_string = f"{filtered_bom['bomSource']['document']['name']}_{filtered_bom['bomSource']['element']['name']}"
                    frameBody.quantities.bom_qty = int(part['headerIdToValue'][qtyId]) 
                    frameBody.document_info.documentId = part['itemSource']['documentId']  # using get to avoid key error: row.get('itemSource', {}).get('documentId')
                    frameBody.document_info.elementId = part['itemSource']['elementId']  
                    frameBody.document_info.wvmType = part['itemSource']['wvmType']  
                    frameBody.document_info.wvmId = part['itemSource']['wvmId']  
                    frameBody.document_info.configuration = part['itemSource']['configuration'] 
                    frameBody.table_info.part_name = row.get('partName')
                    frameBody.table_info.original_name = row.get('originalName')
                    frameBody.table_info.item = row.get('item')
                    frameBody.table_info.original_body_id = row.get('originalbodyid')
                    frameBody.table_info.description = row.get('description')
                    frameBody.table_info.qty = int(row.get('qty'))
                    frameBody.table_info.cutlist_body_id = row.get('cutlistbodyid')
                    frameBody.table_info.length = row.get('length')
                    frameBody.table_info.part_number = row.get('partNumber')
                    frameBody.table_info.part_type = row.get('type')                    
                    frameBody.quantities.cut_list_qty = row.get('qty')
                    frameBody.quantities.total_qty = int(row.get('qty')) * int(part['headerIdToValue'][qtyId] )

                    row['Assembly String'] = f"{filtered_bom['bomSource']['document']['name']}_{filtered_bom['bomSource']['element']['name']}"
                    row['BOM Qty'] = part['headerIdToValue'][qtyId]  
                    row['documentId'] = part['itemSource']['documentId']   
                    row['elementId'] = part['itemSource']['elementId']  
                    row['wvmType'] = part['itemSource']['wvmType']  
                    row['wvmId'] = part['itemSource']['wvmId']  
                    row['configuration'] = part['itemSource']['configuration'] 
                #framesOutput.extend(cutlist_matches)
                    framesOutput.append(frameBody)

         




            # Filter rows where OriginalBodyId == lookupId
            originalbody_matches = [row['columnIdToValue'] for row in rows if row['columnIdToValue'].get('originalbodyid') == lookupId]
            if originalbody_matches:   
                # Add 'BOM Qty' to each matching row
                for row in originalbody_matches:
                    frameBody = FrameBodyInfo()
                    frameBody.assembly_string = f"{filtered_bom['bomSource']['document']['name']}_{filtered_bom['bomSource']['element']['name']}"
                    frameBody.quantities.bom_qty = part['headerIdToValue'][qtyId] 
                    frameBody.document_info.documentId = part['itemSource']['documentId']  
                    frameBody.document_info.elementId = part['itemSource']['elementId']  
                    frameBody.document_info.wvmType = part['itemSource']['wvmType']  
                    frameBody.document_info.wvmId = part['itemSource']['wvmId']  
                    frameBody.document_info.configuration = part['itemSource']['configuration'] 
                    frameBody.table_info.part_name = row.get('partName')
                    frameBody.table_info.original_name = row.get('originalName')
                    frameBody.table_info.item = row.get('item')
                    frameBody.table_info.original_body_id = row.get('originalbodyid')
                    frameBody.table_info.description = row.get('description')
                    frameBody.table_info.qty = int(row.get('qty'))
                    frameBody.table_info.cutlist_body_id = row.get('cutlistbodyid')
                    frameBody.table_info.length = row.get('length')
                    frameBody.table_info.part_number = row.get('partNumber')
                    frameBody.table_info.part_type = row.get('type')                    
                    frameBody.quantities.cut_list_qty = row.get('qty')
                    frameBody.quantities.total_qty = int(row.get('qty')) * int(part['headerIdToValue'][qtyId] )
                    
                    row['BOM Qty'] = part['headerIdToValue'][qtyId]                  
                    row['documentId'] = part['itemSource']['documentId']   
                    row['elementId'] = part['itemSource']['elementId']                      
                    row['wvmType'] = part['itemSource']['wvmType']  
                    row['wvmId'] = part['itemSource']['wvmId']  
                    row['configuration'] = part['itemSource']['configuration']          
                #framesOutput.extend(originalbody_matches)
                    framesOutput.append(frameBody)

        # Convert each to a dictionary
        #frame_dicts = [asdict(frame) for frame in framesOutput]
        # Serialize to JSON
        #json_output = json.dumps(frame_dicts, indent=2)  # `indent` makes it pretty
        #print(json_output)    

        #pprint(framesOutput) 
        
        for frame in framesOutput:
            #pprint(frame)
            #print(frame.table_info.description)
            update_part_metadata(onshape, frame) 
            frame.profile = determine_profile(frame.table_info.description) 
            #frame['Profile'] = determine_profile(frame['description'])  
            #frame['href'] = get_step_url(onshape, frame['documentId'], frame['wvmType'], frame['wvmId'], frame['elementId'], frame['configuration'], frame['originalbodyid'])
            
            #Only get href if option was selected in UI
            if framesUiOptions['STEP Option']:            
                frame.href = get_step_url(onshape, frame.document_info.documentId , frame.document_info.wvmType, frame.document_info.wvmId, frame.document_info.elementId, frame.document_info.configuration, frame.table_info.original_body_id)
        
        #Delete created feature - as has been used now
        #pprint(delete_feature)
        for i in delete_feature:
            delete_url = f"/api/{API_VERSION}/partstudios/d/{i['documentId']}/{i['wvmType']}/{i['wvmId']}/e/{i['elementId']}/features/featureid/{i['featureId']}"
            onshape.request('DELETE', delete_url).json()
        
        # Convert each to a dictionary
        #frame_dicts = [asdict(frame) for frame in framesOutput]
        # Serialize to JSON
        #json_output = json.dumps(frame_dicts, indent=2)  # `indent` makes it pretty
        #print(json_output)
        ui_state.frames_output = framesOutput
        print(f"FRAMES OUTPUT: {framesOutput}")
        return framesOutput
        
            
    except Exception as e:
                exc_type, exc_value, exc_tb = sys.exc_info()
                print("Exception:", e)
                print("Type:", exc_type)
                print("Line number:", exc_tb.tb_lineno)
                traceback.print_exc()
                return {
                    "Error": str(e),
                    "Information": 'ERROR IN COMPOSITE CUTLIST DETERMINATION',
                    "Module": __name__,
                    "Function": "get_body_details",
                    "Line Number": e.__traceback__.tb_lineno
                }

    return