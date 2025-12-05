# app/public_api/config_routes.py

from flask import Blueprint, request, jsonify
from app.handlers.config_handler import ConfigHandler
from app.handlers.encoding_handler import EncodingHandler
from app.services.configuration_service import build_ui_schema

config_bp = Blueprint("config", __name__, url_prefix="/api/config")


# -----------------------------------------------------------
# GET CONFIGURATIONS
# -----------------------------------------------------------
@config_bp.get("/configurations")
def get_configurations():
    """
    Returns the configuration schema for the given Onshape URL.
    The response is transformed into a UI-friendly schema for Elementor.
    """
    doc_url = request.args.get("url", "")
    if not doc_url:
        return jsonify({"error": "Missing ?url= parameter"}), 400

    config_json = ConfigHandler.get_configurations(doc_url)
    ui_schema = build_ui_schema(config_json)
    return jsonify(ui_schema)


# -----------------------------------------------------------
# POST ENCODE CONFIGURATION
# -----------------------------------------------------------
@config_bp.post("/encode")
def encode_configuration():
    """
    Takes:
        { "url": "...", "values": { paramId: value } }
    Returns:
        { "encodedId": "..." }
    """
    data = request.get_json(force=True) or {}

    doc_url = data.get("url", "")
    values = data.get("values", {})

    if not doc_url:
        return jsonify({"error": "Missing URL"}), 400

    if not isinstance(values, dict):
        return jsonify({"error": "Invalid values payload"}), 400

    encoded = EncodingHandler.encode_from_values(doc_url, values)
    return jsonify({"encodedId": encoded})
