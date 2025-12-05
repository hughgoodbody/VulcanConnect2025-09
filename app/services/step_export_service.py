# app/services/step_export_service.py

from typing import Optional

from app.onshape.client import OnshapeClient
from app.onshape.parser import parse_url
from app.config.settings import API_VERSION


def export_step(doc_url: str, configuration: Optional[str] = None) -> bytes:
    """
    Export a STEP file for the given Onshape element.

    :param doc_url: Full Onshape document URL.
    :param configuration: Optional encoded configuration string.
    :return: Raw STEP file bytes.
    """
    did, wvm_type, wid, eid = parse_url(doc_url)
    client = OnshapeClient()

    path = f"/api/{API_VERSION}/partstudios/d/{did}/{wvm_type}/{wid}/e/{eid}/export"
    query = {
        "format": "STEP",
    }
    if configuration:
        query["configuration"] = configuration

    response = client.get(path, params=query)
    response.raise_for_status()
    return response.content
