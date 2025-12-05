# app/services/step_export_service.py

from typing import Optional

from app.onshape.onshape_api import Onshape
from app.onshape.parser import parse_url
from app.config.settings import CREDS_PATH, API_VERSION, API_BASE


def export_step(doc_url: str, configuration: Optional[str] = None) -> bytes:
    did, wvm_type, wvm_id, eid = parse_url(doc_url)
    onshape = Onshape(API_BASE, logging=False, creds=CREDS_PATH)

    path = f"/api/{API_VERSION}/partstudios/d/{did}/{wvm_type}/{wvm_id}/e/{eid}/export"
    query = {"format": "STEP"}
    if configuration:
        query["configuration"] = configuration

    response = onshape.request("GET", path, query=query)
    return response.content
