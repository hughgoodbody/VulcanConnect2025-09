# app/public_api/export_routes.py

from flask import Blueprint, request

from app.handlers.export_handler import ExportHandler
from app.utils.file_ops import bytes_to_download_response

export_bp = Blueprint("export", __name__, url_prefix="/api/export")


@export_bp.post("/step")
def export_step_route():
    data = request.get_json(force=True) or {}
    doc_url = data.get("url", "")
    configuration = data.get("configuration")  # optional encoded string

    step_bytes = ExportHandler.export_step_bytes(doc_url, configuration)
    return bytes_to_download_response(step_bytes, "model.step", "application/step")


@export_bp.post("/zip")
def export_zip_route():
    data = request.get_json(force=True) or {}
    doc_url = data.get("url", "")
    configuration = data.get("configuration")

    zip_bytes = ExportHandler.export_step_zip(doc_url, configuration)
    return bytes_to_download_response(zip_bytes, "model.zip", "application/zip")
