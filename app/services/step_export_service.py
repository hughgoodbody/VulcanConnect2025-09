# app/services/step_export_service.py

import os
from typing import Optional

from app.onshape.onshape import Onshape
from app.onshape.parser import parse_url
from app.config.settings import (
    DEVELOPMENT_MODE,
    LOCAL_DATA_PATH,
    API_VERSION,
    API_BASE,
    CREDS_PATH
)


def export_step(doc_url: str, configuration: Optional[str] = None) -> bytes:
    """
    Return STEP file bytes.
    DEV mode  → loads from /local_data/4_step_export.step
    LIVE mode → requests Onshape export API
    """

    # ------------------------------------------------------------------
    # DEV MODE: Serve Mock File
    # ------------------------------------------------------------------
    if DEVELOPMENT_MODE:
        mock_file = os.path.join(LOCAL_DATA_PATH, "4_step_export.step")
        if not os.path.exists(mock_file):
            raise FileNotFoundError(
                f"DEV MODE is ON but mock STEP file is missing: {mock_file}"
            )
        with open(mock_file, "rb") as f:
            return f.read()

    # ------------------------------------------------------------------
    # LIVE MODE: Real API Call
    # ------------------------------------------------------------------
    did, wvm_type, wvm_id, eid = parse_url(doc_url)
    onshape = Onshape(API_BASE, creds=CREDS_PATH, logging=False)

    path = (
        f"/api/{API_VERSION}/partstudios/d/{did}/"
        f"{wvm_type}/{wvm_id}/e/{eid}/export"
    )

    query = {"format": "STEP"}
    if configuration:
        query["configuration"] = configuration

    response = onshape.request("GET", path, query=query)
    response.raise_for_status()

    return response.content
