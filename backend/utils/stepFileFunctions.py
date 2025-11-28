from urllib.parse import urlparse, parse_qsl
import time
from config.settings import API_BASE, API_VERSION, CREDS_PATH
from backend.onshape.onshape import Onshape
import traceback
import sys

onshape = Onshape(API_BASE, CREDS_PATH, logging=False)

def fetch_data_from_href(href):
    """Parse href and fetch JSON result from Onshape API."""
    parsed_url = urlparse(href)
    path = parsed_url.path
    query = parse_qsl(parsed_url.query)
    response = onshape.request('get', path, query=query)
    if response.ok:
        return response.json()
    raise RuntimeError(f"Failed to fetch data from href: {href}")

def download_step_file_to_memory(href, filename, docid):
    """Poll href until export is ready, then return STEP file bytes."""
    while True:
        data = fetch_data_from_href(href)
        state = data.get("requestState")
        if state == "DONE":
            break
        elif state == "FAILED":
            print(f"Export failed for {filename}")
            return None, None
        time.sleep(2)  # Polling delay

    file_id = data["resultExternalDataIds"][0]
    file_url = f"/api/{API_VERSION}/documents/d/{docid}/externaldata/{file_id}"
    response = onshape.request('get', file_url)
    if response.ok:
        return f"{filename}.step", response.content
    else:
        print(f"Error downloading STEP for {filename}: {response.status_code}")
        return None, None
    
def process_step_files(frames_output):
    step_files = []
    try:
        for frame in frames_output:
            if frame.href:
                href = frame.href
                docid = frame.document_info.documentId
                filename = frame.file_name
                if href and docid:
                    step_name, step_content = download_step_file_to_memory(href, filename, docid)
                    if step_content:
                        step_files.append((step_name, step_content))
                        #print(step_files)
    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        print("Exception:", e)
        print("Type:", exc_type)
        print("Line number:", exc_tb.tb_lineno)
        traceback.print_exc()
        return {
            "Error": str(e),
            "Information": 'ERROR IN STEP FILE PROCESSING',
            "Module": __name__,
            "Function": "process_step_files",
            "Line Number": e.__traceback__.tb_lineno
        }
    
    return step_files