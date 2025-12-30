# app/handlers/config_handler.py

import logging
from typing import Any, Dict, List

from app.onshape.api_switch import api_or_mock
from app.onshape.onshape import Onshape  # your original class
from app.onshape.parser import parse_url
from app.config.settings import CREDS_PATH, API_VERSION, API_BASE, DEVELOPMENT_MODE

logger = logging.getLogger(__name__)


class ConfigHandler:
    """High-level operations for fetching and encoding Onshape configurations."""

    # ----------------------------------------------------------------------
    # GET CONFIGURATIONS
    # ----------------------------------------------------------------------
    @staticmethod
    def get_configurations(doc_url: str) -> Dict[str, Any]:
        """
        Fetch the full configuration structure for an Onshape element.

        • In DEV MODE → loads local_data/1_configurations.json
        • In PROD MODE → calls real Onshape API
        """
        if not doc_url:
            raise ValueError("Document URL is empty.")

        did, wvm_type, wid, eid = parse_url(doc_url)
        path = f"/api/{API_VERSION}/elements/d/{did}/{wvm_type}/{wid}/e/{eid}/configuration"

        mock_filename = "1_configurations.json"

        try:
            data = api_or_mock(
                mock_filename=mock_filename,
                method="GET",
                path=path
            )
            logger.info("Configuration data served (%s mode)", 
                        "DEV" if DEVELOPMENT_MODE else "LIVE")
            return data

        except Exception:
            logger.exception("Failed to retrieve configuration data.")
            raise

    # ----------------------------------------------------------------------
    # ENCODE CONFIGURATION
    # ----------------------------------------------------------------------
    @staticmethod
    def encode_configuration(
        doc_url: str,
        config_payload: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Encode a set of configuration parameter values into an
        Onshape configuration encoding.
    
        Returns:
            {
              "encodedId": "...",
              "queryParam": "configuration=..."
            }
    
        • In DEV MODE → loads local_data/2_encoded_configuration.json
        • In PROD MODE → calls real Onshape API
        """
        if not doc_url:
            raise ValueError("Document URL is empty.")
    
        if not config_payload:
            raise ValueError("Configuration payload is empty.")
    
        did, _wvm_type, _wid, eid = parse_url(doc_url)
        path = f"/api/{API_VERSION}/elements/d/{did}/e/{eid}/configurationencodings"
    
        mock_filename = "2_encoded_configuration.json"
        body = {"parameters": config_payload}
    
        try:
            data = api_or_mock(
                mock_filename=mock_filename,
                method="POST",
                path=path,
                body=body
            )
    
            encoded_id = data.get("encodedId")
            query_param = data.get("queryParam")
    
            if not encoded_id or not query_param:
                raise RuntimeError(
                    f"Encoding response missing encodedId or queryParam: {data}"
                )
    
            logger.info(
                "Configuration encoded (%s mode): %s",
                "DEV" if DEVELOPMENT_MODE else "LIVE",
                encoded_id
            )
    
            return {
                "encodedId": encoded_id,
                "queryParam": query_param,
            }
    
        except Exception:
            logger.exception("Failed to encode configuration.")
            raise

