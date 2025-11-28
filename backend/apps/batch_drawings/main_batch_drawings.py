from io import BytesIO
import asyncio
from zipfile import ZipFile
from urllib.parse import urlparse, parse_qsl
import time
import traceback
from backend.onshape.onshape import Onshape
from backend.utils.helpers import parse_url
from config.settings import CREDS_PATH, API_VERSION, API_BASE

onshape = Onshape(API_BASE, logging=False, creds=CREDS_PATH)

'''
export_formats={'PDF': True, 'DWG': True, 'DXF': False}'''

def export_drawings_to_memory_zip(
    url: str,
    export_formats: dict,
    update_notifier,
    update_progress: callable = None,  # Optional callback for progress updates
) -> BytesIO:

    # --- sanity log so we can see what the backend actually received
    #print('BACKEND export_drawings_to_memory_zip export_formats:', export_formats)

    # compute enabled formats once, normalize to UPPER
    enabled_fmts = [k.upper() for k, v in (export_formats or {}).items() if v]
    enabled_fmts = [f for f in enabled_fmts if f in ('PDF', 'DXF', 'DWG')]
    #print('Enabled formats:', enabled_fmts)

    if not enabled_fmts:
        print('No formats enabled; returning empty zip')
        buf = BytesIO()
        with ZipFile(buf, 'w'):
            pass
        buf.seek(0)
        return buf


    def get_drawings(documentId, wvmType, wvmId):
        print('GETTING DRAWINGS')
        resp = onshape.request('get', f'/api/{API_VERSION}/documents/d/{documentId}/{wvmType}/{wvmId}/elements')
        return [el for el in resp.json() if el['dataType'] == 'onshape-app/drawing']

    def create_translation(documentId, wvmType, wvmId, eid, fmt):
        url = f'/api/{API_VERSION}/drawings/d/{documentId}/{wvmType}/{wvmId}/e/{eid}/translations'
        
        #May need seperate bodies, for DXF/DWG and PDF - DXF/DWG needs to be version 2013

        if fmt.upper() == 'PDF':        
            body = {
                "formatName": fmt.upper(),
                "storeInDocument": False,
                "flatten": True,
                "splinesAsPolylines": True,
                "destinationName": f"{fmt}_Export",
                "textAsGeometry": False,
                "showOveriddenDimensions": True,
                "currentSheetOnly": False,      
                "flatten": True,
                "colorMethod": "color",
                "selectablePdfText": False,
      
            }

        else:
            body = {
            "formatName": fmt.upper(),
            "destinationName": f"{fmt}_Export",
            "textAsGeometry": False,
            "showOveriddenDimensions": True,
            "currentSheetOnly": False,
            "splinesAsPolylines": True,
            "flatten": True,
            "colorMethod": "color",
            "selectablePdfText": False,
            "storeInDocument": False,
            "versionString": "2013"
        }

        resp = onshape.request('post', url, body=body)
        return resp.json()['href']

    def href_to_data(href):
        query = parse_qsl(urlparse(href).query)
        path = urlparse(href).path
        return onshape.request('get', path, query=query).json()

    def poll_translation(href, retries=30, delay=5):
        for _ in range(retries):
            result = href_to_data(href)
            if result['requestState'] == 'DONE':
                return result
            elif result['requestState'] == 'FAILED':
                return None
            time.sleep(delay)
        return None

    def download_file(docid, file_id):
        #print('DOWNLOADING FILE')
        resp = onshape.request('get', f'/api/{API_VERSION}/documents/d/{docid}/externaldata/{file_id}')
        return resp.content if resp.ok else None

    # --- Begin Export ---
    try:
        zip_buffer = BytesIO()
        print('BEGIN EXPORT')        
        with ZipFile(zip_buffer, 'w') as zipf:
            docid, wvmType, wvmId, elementId = parse_url(url)
            drawings = get_drawings(docid, wvmType, wvmId)
            total_tasks = len(drawings) * sum(export_formats.values())
            completed_tasks = 0

            for drawing in drawings:
                eid = drawing['id']
                name = drawing['name']

                for fmt, enabled in export_formats.items():
                    if not enabled:
                        continue
                    try:
                        href = create_translation(docid, wvmType, wvmId, eid, fmt)
                        result = poll_translation(href)
                        if result:
                            file_id = result["resultExternalDataIds"][0]
                            content = download_file(docid, file_id)
                            if content:
                                filename = f"{name}.{fmt.lower()}"
                                zipf.writestr(filename, content)
                    except Exception as e:
                        print(f"⚠️ Export failed for {name}.{fmt}: {e}")
                    finally:
                        completed_tasks += 1
                        if update_progress:
                            update_progress(completed_tasks, total_tasks)

        zip_buffer.seek(0)
    except:
        traceback.print_exc()    
    return zip_buffer.read()