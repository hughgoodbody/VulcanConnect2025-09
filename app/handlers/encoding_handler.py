# app/handlers/encoding_handler.py

from typing import Any, Dict

from app.handlers.config_handler import ConfigHandler
from app.services.encoding_service import build_parameter_list


class EncodingHandler:
    """
    High-level façade for turning raw configuration values into an
    encoded Onshape configuration string.
    """

    @staticmethod
    def encode_from_values(doc_url: str, values: Dict[str, Any]) -> str:
        """
        :param doc_url: Full Onshape document URL.
        :param values: Dict of {parameterId: value}
        :return: Encoded configuration string (encodedId).
        """
        parameter_list = build_parameter_list(values)
        return ConfigHandler.encode_configuration(doc_url, parameter_list)
