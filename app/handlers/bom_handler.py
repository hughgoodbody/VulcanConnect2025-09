# app/handlers/bom_handler.py

from typing import Any, Dict, List
from app.onshape.parser import parse_url
from app.onshape.api_switch import api_or_mock
from app.config.settings import CREDS_PATH, API_VERSION, API_BASE, DEVELOPMENT_MODE
from app.services.bom_service import filter_bom_rows, dedupe_bom_by_source


class BomHandler:

    # --------------------------------------------------------------
    # FETCH BOM FOR A GIVEN CONFIGURATION
    # --------------------------------------------------------------
    @staticmethod
    def fetch_bom_for_configuration(doc_url: str, encoded_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve BOM for a specific encoded configuration.

        • DEV MODE -> load local mock JSON
        • LIVE MODE -> query Onshape BOM API with configuration={encoded_id}
        """
        did, wvm_type, wvm_id, eid = parse_url(doc_url)

        # BOM endpoint path
        path = (
            f"/api/{API_VERSION}/assemblies/d/"
            f"{did}/{wvm_type}/{wvm_id}/e/{eid}/bom"
        )

        # Query parameters (configuration-aware)
        query = {
            "indented": False,
            "multiLevel": False,
            "generateIfAbsent": True,
            "configuration": encoded_id       # ⬅ KEY LINE
        }

        mock_filename = "3_bom.json"

        # Fetch raw BOM list
        raw_bom = api_or_mock(
            mock_filename=mock_filename,
            method="GET",
            path=path,
            query=query
        )

        # Filter + dedupe (your existing functions)
        filtered = filter_bom_rows(raw_bom)
        deduped = dedupe_bom_by_source(filtered)

        return {
            "filtered": filtered,
            "dedupBySource": deduped
        }

