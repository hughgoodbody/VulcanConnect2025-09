# app/services/bom_service.py

import copy
from typing import Any, Dict, List, Optional

from app.onshape.client import OnshapeClient
from app.config.settings import API_VERSION


def filter_bom_rows(bom: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a deep-copied BOM dict with unwanted rows removed:
      • Standard content rows
      • rows with 'excludeFromBom' header flag True
      • rows with 'excludefromlasersearch' header flag True
    """
    filtered_bom = copy.deepcopy(bom)

    prop_to_id = {h["propertyName"]: h["id"] for h in filtered_bom.get("headers", [])}
    exclude_bom_id = prop_to_id.get("excludeFromBom")
    exclude_laser_id = prop_to_id.get("excludefromlasersearch")

    rows = filtered_bom.get("rows", [])
    for idx in range(len(rows) - 1, -1, -1):
        row = rows[idx]
        src = row.get("itemSource", {})

        # standard content
        if src.get("isStandardContent"):
            del rows[idx]
            continue

        hv = row.get("headerIdToValue", {})

        if exclude_bom_id and hv.get(exclude_bom_id):
            del rows[idx]
            continue
        if exclude_laser_id and hv.get(exclude_laser_id):
            del rows[idx]
            continue

    return filtered_bom


def get_raw_bom(
    document_id: str,
    wvm_type: str,
    wvm_id: str,
    element_id: str,
) -> Dict[str, Any]:
    """
    Call the Onshape BOM API and return the raw BOM dict.
    """
    client = OnshapeClient()
    url = f"/api/{API_VERSION}/assemblies/d/{document_id}/{wvm_type}/{wvm_id}/e/{element_id}/bom"
    query = {"indented": False, "multiLevel": False, "generateIfAbsent": True}
    api_bom = client.get(url, params=query).json()
    return api_bom


def get_bom(
    document_id: str,
    wvm_type: str,
    wvm_id: str,
    element_id: str,
) -> Dict[str, Any]:
    """
    Convenience wrapper that fetches and filters the BOM.
    """
    raw_bom = get_raw_bom(document_id, wvm_type, wvm_id, element_id)
    return filter_bom_rows(raw_bom)


def dedupe_bom_by_source(bom: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Given a BOM dict, return a list of rows where no two rows share the same:
      documentId, elementId, wvmType, wvmId, configuration.
    """
    seen = set()
    deduped: List[Dict[str, Any]] = []

    for row in bom.get("rows", []):
        src = row.get("itemSource", {})
        key = (
            src.get("documentId"),
            src.get("elementId"),
            src.get("wvmType"),
            src.get("wvmId"),
            src.get("configuration"),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(row)

    return deduped


def get_quantity_header_id(bom: Dict[str, Any]) -> Optional[str]:
    """
    Return header ID for the 'quantity' column in a BOM, or None if not found.
    """
    for header in bom.get("headers", []):
        if header.get("propertyName") == "quantity":
            return header.get("id")
    return None
