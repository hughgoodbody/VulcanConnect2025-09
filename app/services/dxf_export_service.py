# app/services/dxf_export_service.py

import os
import io
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qsl

from app.onshape.onshape import Onshape
from app.config.settings import (
    DEVELOPMENT_MODE,
    LOCAL_DATA_PATH,
    API_VERSION,
    API_BASE,
    CREDS_PATH,
)
from app.onshape.parser import parse_url
from app.utils.filename import sanitize_token


PROCESS_MAP = {
    "Laser": "LAS",
    "Waterjet": "WJ",
    "Plasma": "PLA",
    "Oxy Fuel": "OXY",
    "Saw": "SAW",
    "Manual": "MAN",
}


def _process_code(process: Optional[str]) -> str:
    return PROCESS_MAP.get(process or "", sanitize_token(process or "") or "UNK")


def _format_thickness_mm(part: Dict[str, Any]) -> str:
    """
    Prefer laserProfile.data.Thickness_mm (exists in your sample JSON).
    """
    lp = (part.get("laserProfile") or {}).get("data") or {}
    t = lp.get("Thickness_mm")

    if t is None:
        # fallback if later you add part["thickness_mm"] or similar
        t = part.get("thickness_mm")

    try:
        t_float = float(t)
    except Exception:
        return "0mm"

    # Keep it stable & parseable
    if abs(t_float - round(t_float)) < 1e-9:
        return f"{int(round(t_float))}mm"
    return f"{t_float:.2f}mm"


def _derive_operations_code(part: Dict[str, Any]) -> str:
    """
    Preferred: part["operationsCode"] set upstream.
    Fallback: 'B' if sheetMetal else ''.
    """
    existing = part.get("operationsCode") or part.get("operations")  # allow either
    if isinstance(existing, str) and existing.strip():
        return sanitize_token(existing.strip())

    ops = ""
    if part.get("sheetMetal"):
        ops += "B"

    # If later you add booleans, these will “just work”:
    if part.get("hasTaps") or part.get("tapCount", 0):
        ops += "T"
    if part.get("hasEtch") or part.get("etchCount", 0):
        ops += "E"
    if part.get("hasDrill") or part.get("drillCount", 0):
        ops += "D"

    return ops


def build_dxf_filename(part: Dict[str, Any]) -> str:
    """
    PartNumber_thickness_material_quantity_operations_process.dxf
    """
    part_number = part.get("partNumber") or part.get("name") or part.get("partId") or "PART"
    part_number = sanitize_token(part_number) or "PART"

    thickness = _format_thickness_mm(part)

    material = part.get("material") or "UNKNOWN"
    material = sanitize_token(material) or "UNKNOWN"

    qty = part.get("exportQuantity") or part.get("quantity") or 1
    try:
        qty = int(qty)
    except Exception:
        qty = 1

    operations = _derive_operations_code(part)
    process = _process_code(part.get("process"))

    tokens = [part_number, thickness, material, str(qty)]
    if operations:
        tokens.append(operations)
    tokens.append(process)

    return "_".join(tokens) + ".dxf"


def export_dxf_bytes_for_part(
    onshape: Onshape,
    did: str,
    wvm_type: str,
    wvm_id: str,
    eid: str,
    configuration: str,
    face_id: str,
    view_matrix: List[float],
) -> bytes:
    """
    Calls Onshape export to generate a flat DXF using face + view matrix.
    Two-step:
      1) POST export -> returns href
      2) GET href -> returns file bytes
    """
    path = f"/api/{API_VERSION}/documents/d/{did}/{wvm_type}/{wvm_id}/e/{eid}/export"

    view_string = ",".join(str(x) for x in view_matrix)

    payload = {
        "format": "DXF",
        "view": view_string,
        "destinationName": "Export Flatpattern via API",
        "version": "2007",
        "flatten": True,
        "includeBendCenterlines": True,
        "includeSketches": False,
        "sheetMetalFlat": True,
        "triggerAutoDownload": True,
        "storeInDocument": False,
        "configuration": configuration,
        "cloudStorageAccountId": "",
        "cloudObjectId": "",
        "partIds": face_id,  # NOTE: this is a FACE id (as in your snippet)
    }

    resp = onshape.request("POST", path, query={}, body=payload)
    resp.raise_for_status()
    href = resp.json()["href"]

    u = urlparse(href)
    dl_query = dict(parse_qsl(u.query))
    dl_path = u.path

    dl = onshape.request("GET", dl_path, query=dl_query, body={})
    dl.raise_for_status()
    return dl.content


def export_supplier_grouped_dxf_zip(
    doc_url: str,
    payload_json: Dict[str, Any],
) -> Dict[str, bytes]:
    """
    Returns a dict suitable for create_zip():
      { "SupplierA/<filename>.dxf": bytes, "SupplierB/<filename>.dxf": bytes, ... }

    - Uses updatedParts[] where each item has:
        { updates: {...}, originalPart: {...} }
    - Skips remove==True
    """
    updated_parts = payload_json.get("updatedParts") or []
    user_options = payload_json.get("userOptions") or {}

    default_supplier = user_options.get("defaultSupplier") or "Unassigned"

    # Use doc_url to get wvm context (your current.json sample omits wvmType/wvmId) :contentReference[oaicite:2]{index=2}
    did_from_url, wvm_type, wvm_id, _eid_from_url = parse_url(doc_url)

    onshape = Onshape(API_BASE, creds=CREDS_PATH, logging=False)

    out: Dict[str, bytes] = {}

    for row in updated_parts:
        updates = row.get("updates") or {}
        orig = row.get("originalPart") or {}

        if updates.get("remove") is True:
            continue

        part: Dict[str, Any] = {}
        part.update(orig)
        part.update({
            # “updates” fields override originals
            "process": updates.get("process") or orig.get("process"),
            "material": updates.get("material") or orig.get("material"),
            "supplier": updates.get("supplier") or default_supplier,
            "exportQuantity": updates.get("exportQuantity") or orig.get("quantity") or 1,
            "partNumber": updates.get("partNumber") or orig.get("partNumber") or orig.get("name"),
        })

        supplier = sanitize_token(part.get("supplier") or default_supplier) or "Unassigned"

        dxf_name = build_dxf_filename(part)

        # DXF export needs laser profile data
        lp = (part.get("laserProfile") or {}).get("data") or {}
        face_id = lp.get("Face")
        view_matrix = lp.get("ViewMatrix")

        if not face_id or not view_matrix:
            # No laser profile => cannot export DXF flat from face/view
            # (You can later decide to skip or raise; skipping is safer for batch export.)
            continue

        # This part’s elementId can differ across the BOM
        eid = part.get("elementId")
        if not eid:
            continue

        configuration = part.get("configuration") or "default"
        did = part.get("documentId") or did_from_url

        dxf_bytes = export_dxf_bytes_for_part(
            onshape=onshape,
            did=did,
            wvm_type=wvm_type,
            wvm_id=wvm_id,
            eid=eid,
            configuration=configuration,
            face_id=face_id,
            view_matrix=view_matrix,
        )

        zip_path = f"{supplier}/{dxf_name}"
        out[zip_path] = dxf_bytes

        # Optional local write (useful during local dev)
        if DEVELOPMENT_MODE:
            export_dir = os.path.join(LOCAL_DATA_PATH, "exports", supplier)
            os.makedirs(export_dir, exist_ok=True)
            with open(os.path.join(export_dir, dxf_name), "wb") as f:
                f.write(dxf_bytes)

    return out
