import json
import requests
import copy
import sys
import traceback
from urllib.parse import urlparse
from config.settings import CREDS_PATH, API_VERSION, API_BASE




def filter_bom_rows(bom):
    """
    Return a deep‑copied BOM dict with unwanted rows removed in place.
    Unwanted rows are those where:
      • itemSource.isStandardContent is True, OR
      • the 'excludeFromBom' header flag is True, OR
      • the 'excludefromlasersearch' header flag is True.

    The original bom dict is left untouched.
    """
    # 1) Deep copy the entire BOM
    filtered_bom = copy.deepcopy(bom)

    # 2) Find the header IDs for the two exclude flags
    prop_to_id = {h['propertyName']: h['id'] for h in filtered_bom.get('headers', [])}
    exclude_bom_id   = prop_to_id.get('excludeFromBom')
    exclude_laser_id = prop_to_id.get('excludefromlasersearch')

    # 3) Walk backwards through the rows and delete any that match
    rows = filtered_bom.get('rows', [])
    for idx in range(len(rows) - 1, -1, -1):
        row = rows[idx]
        src = row.get('itemSource', {})

        # a) isStandardContent?
        if src.get('isStandardContent'):
            del rows[idx]
            continue

        # b & c) check header flags
        hv = row.get('headerIdToValue', {})
        if exclude_bom_id   and hv.get(exclude_bom_id):
            del rows[idx]
            continue
        if exclude_laser_id and hv.get(exclude_laser_id):
            del rows[idx]
            continue
    #print(filtered_bom)
    return filtered_bom

def get_bom(onshape, documentId, wvmType, wvmId, elementId):
    url = f'/api/{API_VERSION}/assemblies/d/{documentId}/{wvmType}/{wvmId}/e/{elementId}/bom'
    query = {'indented': False, 'multiLevel': False, 'generateIfAbsent': True}
    api_bom = onshape.request('get', url, query=query).json()
    #items = api_bom['bomTable']['items']
    filteredBom = filter_bom_rows(api_bom)    
    return filteredBom


def dedupe_bom_by_source(bom):
    """
    Creates a list of discrete part studios

    Given a BOM dict with a top‑level 'rows' list, return a new list of rows
    where no two rows share the same itemSource.documentId, elementId,
    wvmType, wvmId, and configuration.
    """
    seen = set()
    deduped = []

    for row in bom['rows']:
        src = row.get('itemSource', {})
        key = (
            src.get('documentId'),
            src.get('elementId'),
            src.get('wvmType'),
            src.get('wvmId'),
            src.get('configuration'),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(row)

    return deduped


def get_quantity_header_id(bom):
    """
    Given a BOM dict, return the header ID for the 'quantity' column.
    If no such header is found, returns None.
    """
    for header in bom.get('headers', []):
        if header.get('propertyName') == 'quantity':
            return header.get('id')
    return None