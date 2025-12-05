# app/public_api/bom_routes.py

from flask import Blueprint, request, jsonify

from app.handlers.bom_handler import BomHandler

bom_bp = Blueprint("bom", __name__, url_prefix="/api/bom")


@bom_bp.get("/filtered")
def get_filtered_bom():
    doc_url = request.args.get("url", "")
    bom = BomHandler.fetch_filtered_bom(doc_url)
    return jsonify(bom)


@bom_bp.get("/deduped")
def get_deduped_bom():
    doc_url = request.args.get("url", "")
    rows = BomHandler.fetch_deduped_bom(doc_url)
    return jsonify({"rows": rows})
