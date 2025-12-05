# app/handlers/bom_handler.py

import logging
from typing import Any, Dict, List

from app.onshape.api_switch import api_or_mock
from app.onshape.parser import parse_url
from app.config.settings import API_VERSION, DEVELOPMENT_MODE
from app.services.bom_service import filter_bom_rows, dedupe_bom_by_source

logger = logging.getLogger(__name__)


class BomHandler:
    """
    High-level BOM operations with development-mode switching.
    """

    # ----------------------------------------------------------------------
    # FETCH RAW BOM (direct from Onshape or from mock file)
    # ----------------------------------------------------------------------
    @staticmethod
    def fetch_raw_bom(doc_url: str) -> Dict[str, Any]:
        """
        Retrieve the raw BOM for an assembly.

        • DEV mode → loads local_data/3_bom.json
        • LIVE mode → calls the Onshape BOM API
        """
        if not doc_url:
            raise ValueError("Document URL is empty.")

        did, wvm_type, wvm_id, eid = parse_url(doc_url)

        path = f"/api/{API_VERSION}/assemblies/d/{did}/{wvm_type}/{wvm_id}/e/{eid}/bom"
        mock_filename = "3_bom.json"

        query = {
            "indented": False,
            "multiLevel": False,
            "generateIfAbsent": True,
        }

        try:
            bom_data = api_or_mock(
                mock_filename=mock_filename,
                method="GET",
                path=path,
                query=query
            )

            logger.info("BOM served (%s mode)", 
                        "DEV" if DEVELOPMENT_MODE else "LIVE")

            return bom_data

        except Exception:
            logger.exception("Failed to retrieve raw BOM.")
            raise

    # ----------------------------------------------------------------------
    # FILTER BOM
    # ----------------------------------------------------------------------
    @staticmethod
    def fetch_filtered_bom(doc_url: str) -> Dict[str, Any]:
        """
        Apply filtering rules to clean the BOM:
        - Remove standard content
        - Remove rows flagged 'excludeFromBom'
        - Remove rows flagged 'excludefromlasersearch'
        """
        try:
            raw = BomHandler.fetch_raw_bom(doc_url)
            filtered = filter_bom_rows(raw)

            logger.info("Filtered BOM generated (%s mode)",
                        "DEV" if DEVELOPMENT_MODE else "LIVE")

            return filtered

        except Exception:
            logger.exception("Failed to filter BOM.")
            raise

    # ----------------------------------------------------------------------
    # DEDUPED BOM
    # ----------------------------------------------------------------------
    @staticmethod
    def fetch_deduped_bom(doc_url: str) -> List[Dict[str, Any]]:
        """
        Remove duplicate BOM rows that represent the same part source:
        (documentId, elementId, wvmType, wvmId, configuration).
        """
        try:
            filtered = BomHandler.fetch_filtered_bom(doc_url)
            deduped = dedupe_bom_by_source(filtered)

            logger.info("Deduped BOM generated (%s mode)",
                        "DEV" if DEVELOPMENT_MODE else "LIVE")

            return deduped

        except Exception:
            logger.exception("Failed to dedupe BOM.")
            raise
