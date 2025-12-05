# app/services/bom_service.py

import copy
from typing import Any, Dict, List, Optional


def filter_bom_rows(bom: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a deep-copied BOM dict with unwanted rows removed in place.
    Unwanted rows are those where:
      • itemSource.isStandardContent is True, OR
      • the 'excludeFromBom' header flag is True, OR
      • the 'excludefromlasersearch' header flag is True.
    """
    filtered_bom = copy.deepcopy(bom)

    prop_to_id = {h["propertyName"]: h["id"] for h in filtered_bom.get("headers", [])}
    exclude_bom_id = prop_to_id.get("excludeFromBom")
    exclude_laser_id = prop_to_id.get("excludefromlasersearch")

    rows = filtered_bom.get("rows", [])
    for idx in range(len(rows) - 1, -1, -1):
        row = rows[idx]
        src = row.get("itemSource", {})

        # Standard content
        if src.get("isStandardContent"):
            del rows[idx]
            continue

        hv = row.get("headerIdToValue", {})

        # Exclude from BOM
        if exclude_bom_id and hv.get(exclude_bom_id):
            del rows[idx]
            continue

        # Exclude from laser search
        if exclude_laser_id and hv.get(exclude_laser_id):
            del rows[idx]
            continue

    return filtered_bom


def dedupe_bom_by_source(bom: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Given a BOM dict with top-level 'rows',
    return rows where each (documentId, elementId, wvmType, wvmId, configuration)
    combination appears only once.
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
    Return the header ID that corresponds to the 'quantity' column, or None.
    """
    for header in bom.get("headers", []):
        if header.get("propertyName") == "quantity":
            return header.get("id")
    return None
