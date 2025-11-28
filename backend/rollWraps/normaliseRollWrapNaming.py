import json
import requests
from urllib.parse import urlparse
from pprint import pprint
from onshape import Onshape

'''Import from other folders'''
import sys
sys.path.insert(0, 'A:\GITHUB\Onshape API')
from site import addsitedir
addsitedir('.\Onshape API')
import onshapeCommon as oc

urlFrame = 'https://cad.onshape.com/documents/98ef28bf767a1b8ef69a2584/w/ea915aa0fce4f6e2400c6df8/e/ae569dba7e59bd1776584c97'
folderNameFrame = 'C:\\Users\Hugh\\Desktop\\testFolder'

def initialize_onshape(credsLoc="A:\\GITHUB\\Onshape-Profile-Exporter\\creds.json"):
    return Onshape('https://cad.onshape.com', credsLoc, logging=False)

onshape = initialize_onshape()

def parse_url(url):
    parsed_url = list(filter(None, urlparse(url).path.split('/')))
    return parsed_url[1], parsed_url[2], parsed_url[3], parsed_url[5]

def parse_href(href):
    parsed_href = list(filter(None, urlparse(href).path.split('/')))
    return parsed_href[3], parsed_href[4], parsed_href[5], parsed_href[7], parsed_href[9]

# Function to update Onshape metadata
def update_metadata(did, wvm, wvmid, eid, pid, properties):
    url = f"/api/v8/metadata/d/{did}/{wvm}/{wvmid}/e/{eid}/p/{pid}"
    #query = {'configuration': "default"}
    body={"properties": properties}
    response = onshape.request('post', url, body=body).json()#
    return response


# Function to process metadata and perform the required operations
def process_metadata(metadata, did, wvm, wvmid, eid, i=1):
    for item in metadata['items']:
        name_a = item['properties'][1]['value']  # This is the "Name" field
        if name_a.startswith("Wrap_"):
            continue  # Skip Wrap_ items when identifying item A

        # Find corresponding item B with "Wrap_" prefix
        wrap_name = f"Wrap_{name_a}"
        item_b = None
        for other_item in metadata['items']:
            if other_item['properties'][1]['value'] == wrap_name:
                item_b = other_item
                break

        if item_b is None:
            continue  # No corresponding item B found

        # Process item A (check API Store 1)
        api_store_a = next((prop for prop in item['properties'] if prop['name'] == 'API Store 1'), None)
        api_store_a_id = api_store_a['propertyId']  # Use property ID for updating

        if api_store_a and api_store_a['value']:
            # API call to update Name metadata to API Store 1 value (use propertyId)
            name_property_id = next((prop for prop in item['properties'] if prop['name'] == 'Name'), None)['propertyId']
            update_metadata(did, wvm, wvmid, eid, item['partId'], [{"propertyId": name_property_id, "value": api_store_a['value']}])
        '''else:
            # API call to update Name and API Store 1 to Tube + i (use propertyId)
            new_name = f"Tube_A{i}"
            name_property_id = next((prop for prop in item['properties'] if prop['name'] == 'Name'), None)['propertyId']
            update_metadata(did, wvm, wvmid, eid, item['partId'], [
                {"propertyId": name_property_id, "value": new_name},
                {"propertyId": api_store_a_id, "value": new_name}
            ])'''

        # Process item B (check API Store 1)
        api_store_b = next((prop for prop in item_b['properties'] if prop['name'] == 'API Store 1'), None)
        api_store_b_id = api_store_b['propertyId']  # Use property ID for updating

        if api_store_b and api_store_b['value']:
            # API call to update Name metadata to API Store 1 value (use propertyId)
            name_property_id_b = next((prop for prop in item_b['properties'] if prop['name'] == 'Name'), None)['propertyId']
            update_metadata(did, wvm, wvmid, eid, item_b['partId'], [{"propertyId": name_property_id_b, "value": api_store_b['value']}])
        '''else:
            # API call to update Name and API Store 1 to Wrap_Tube + i (use propertyId)
            new_name = f"Wrap_Tube_A{i}"
            name_property_id_b = next((prop for prop in item_b['properties'] if prop['name'] == 'Name'), None)['propertyId']
            update_metadata(did, wvm, wvmid, eid, item_b['partId'], [
                {"propertyId": name_property_id_b, "value": new_name},
                {"propertyId": api_store_b_id, "value": new_name}
            ])'''

        # Copy Part number from item A to item B using property ID
        part_number_a = next((prop for prop in item['properties'] if prop['name'] == 'Part number'), None)
        part_number_b = next((prop for prop in item_b['properties'] if prop['name'] == 'Part number'), None)
        if part_number_a and part_number_b:
            # API call to update Part number of item B (use propertyId)
            update_metadata(did, wvm, wvmid, eid, item_b['partId'], [{"propertyId": part_number_b['propertyId'], "value": part_number_a['value']}])

        # Increment the index for the next pair
        i += 1






did, wvm, wvmid, eid = parse_url(urlFrame)

#Get partstudio metadata
url = f"/api/v8/metadata/d/{did}/{wvm}/{wvmid}/e/{eid}/p"
psmetadata = onshape.request('get', url).json()

# Call the function
process_metadata(psmetadata, did, wvm, wvmid, eid)
