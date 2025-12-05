# app/handlers/encoding_handler.py

from typing import Any, Dict
from app.handlers.config_handler import ConfigHandler
from app.services.encoding_service import build_parameter_list
from app.onshape.api_switch import api_or_mock
from app.onshape.parser import parse_url
from app.config.settings import API_VERSION, DEVELOPMENT_MODE


class EncodingHandler:
    """
    Encodes configuration values using either:
    • Mock JSON file (DEV mode)
    • Actual Onshape API (LIVE mode)
    """

    @staticmethod
    def encode_from_values(doc_url: str, values: Dict[str, Any]) -> str:
        """
        Convert { paramId: value } into an encoded configurationId.
        """

        did, wvm_type, wid, eid = parse_url(doc_url)
        path = f"/api/{API_VERSION}/elements/d/{did}/e/{eid}/configurationencodings"

        parameter_list = build_parameter_list(values)
        body = {"parameters": parameter_list}

        mock_file = "2_encoded_configuration.json"

        # DEV MODE → Load mocked encodedId
        response = api_or_mock(
            mock_filename=mock_file,
            method="POST",
            path=path,
            body=body
        )

        encoded = response.get("encodedId")
        if not encoded:
            raise RuntimeError("Missing encodedId in response (mock or API).")

        return encoded
