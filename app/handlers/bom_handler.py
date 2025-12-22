# app/handlers/bom_handler.py

from typing import Any, Dict
import json
import os

from app.onshape.parser import parse_url
from app.onshape.api_switch import api_or_mock
from app.config.settings import (
    CREDS_PATH,
    API_VERSION,
    API_BASE,
    DEVELOPMENT_MODE,
    LOCAL_DATA_PATH,
)
from app.services.bom_service import filter_bom_rows, dedupe_bom_by_source


class BomHandler:

    # --------------------------------------------------------------
    # FETCH BOM FOR A GIVEN CONFIGURATION
    # --------------------------------------------------------------
    @staticmethod
    def fetch_bom_for_configuration(doc_url: str, encoded_id: str, query_param: str) -> Dict[str, Any]:
        """
        Retrieve BOM for a specific encoded configuration.

        • DEV MODE -> load local mock JSON using local_manifest.json
        • LIVE MODE -> query Onshape BOM API with configuration={encoded_id}
        """
        did, wvm_type, wvm_id, eid = parse_url(doc_url)

        # BOM endpoint path
        path = (
            f"/api/{API_VERSION}/assemblies/d/"
            f"{did}/{wvm_type}/{wvm_id}/e/{eid}/bom"
        )

        # Query parameters (configuration-aware)
        config_value = query_param.split("configuration=", 1)[1]
        query = {
            "configuration": config_value,
            "indented": False,
            "multiLevel": False,
            "generateIfAbsent": True,
        }
        # queryParam already includes "configuration=..."
        logger.info("FINAL BOM QUERY: %s", query)
        mock_filename = None

        if DEVELOPMENT_MODE:
            # Use manifest to find the correct BOM file name
            manifest_path = os.path.join(LOCAL_DATA_PATH, "local_manifest.json")
            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                mock_filename = manifest.get("bom", "t1-bom.json")
            except Exception:
                # Fallback if manifest missing
                mock_filename = "t1-bom.json"

        # Fetch raw BOM dict (Onshape API or mock JSON)
        raw_bom = api_or_mock(
            mock_filename=mock_filename,
            method="GET",
            path=path,
            query=query,
        )

        # Filter + dedupe
        filtered_rows = filter_bom_rows(raw_bom)
        deduped_rows = dedupe_bom_by_source(filtered_rows)
        logger.info("BOM query dict: %s", query)

        return {
            "raw": raw_bom,
            "filtered": filtered_rows,
            "dedupBySource": deduped_rows,
        }
