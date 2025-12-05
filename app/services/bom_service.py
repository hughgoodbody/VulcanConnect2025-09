# app/services/bom_service.py

import copy
from typing import Any, Dict, List, Optional


def filter_bom_rows(bom: Dict[str, Any]) -> Dict[str, Any]:
    filtered_bom = copy.deepcopy(bom)

    prop_to_id = {h["propertyName"]: h["id"] for h in filtered_bom.get("headers", [])}
    exclude_bom_id = prop_to_id.get("excludeFromBom")
    exclude_laser_id = prop_to_id.get("excludefromlasersearch")

    rows = filtered_bom.get("rows", [])
    for idx in range(len(rows) - 1, -1, -1):
        row = rows[idx]
        src = row.get("itemSource", {})

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


def dedupe_bom_by_source(bom: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    for header in bom.get("headers", []):
        if header.get("propertyName") == "quantity":
            return header.get("id")
    return None
