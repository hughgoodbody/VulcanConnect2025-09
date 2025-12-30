# app/services/bom_service.py

import copy
from typing import Any, Dict, List, Optional


def filter_bom_rows(bom: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns a LIST of filtered BOM rows.
    Does NOT modify structure; each row is unchanged except removal.
    """

    # Extract required mappings
    prop_to_id = {h["propertyName"]: h["id"] for h in bom.get("headers", [])}
    exclude_bom_id = prop_to_id.get("excludeFromBom")
    exclude_laser_id = prop_to_id.get("excludefromlasersearch")

    filtered_rows = []

    for row in bom.get("rows", []):
        src = row.get("itemSource", {})

        # Exclude standard content
        if src.get("isStandardContent"):
            continue

        hv = row.get("headerIdToValue", {})

        # Exclude based on BOM flags
        if exclude_bom_id and hv.get(exclude_bom_id):
            continue

        if exclude_laser_id and hv.get(exclude_laser_id):
            continue

        filtered_rows.append(row)

    return filtered_rows



def dedupe_bom_by_source(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate by (documentId, elementId, wvmType, wvmId, configuration),
    preserving entire BOM rows.
    """

    seen = set()
    deduped = []

    for row in rows:
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
