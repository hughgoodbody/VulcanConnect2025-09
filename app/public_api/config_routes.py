# app/public_api/config_routes.py

from flask import Blueprint, request, jsonify

from app.handlers.config_handler import ConfigHandler
from app.handlers.encoding_handler import EncodingHandler
from app.services.configuration_service import build_ui_schema

config_bp = Blueprint("config", __name__, url_prefix="/api/config")


@config_bp.get("/configurations")
def get_configurations():
    doc_url = request.args.get("url", "")
    config_json = ConfigHandler.get_configurations(doc_url)
    ui_schema = build_ui_schema(config_json)
    return jsonify(ui_schema)


@config_bp.post("/encode")
def encode_configuration():
    data = request.get_json(force=True) or {}
    doc_url = data.get("url", "")
    values = data.get("values", {})

    encoded = EncodingHandler.encode_from_values(doc_url, values)
    return jsonify({"encodedId": encoded})
