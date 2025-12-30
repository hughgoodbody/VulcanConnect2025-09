# app/public_api/bom_routes.py

from flask import Blueprint, request, jsonify
from app.handlers.bom_handler import BomHandler

bom_bp = Blueprint("bom", __name__)


# -----------------------------------------------------------
# GET FILTERED BOM
# -----------------------------------------------------------
@bom_bp.get("/filtered")
def get_filtered_bom():
    """
    Returns cleaned BOM with:
    - no standard content
    - no excluded rows
    """
    doc_url = request.args.get("url", "")
    if not doc_url:
        return jsonify({"error": "Missing ?url= parameter"}), 400

    bom = BomHandler.fetch_filtered_bom(doc_url)
    return jsonify(bom)


# -----------------------------------------------------------
# GET DEDUPED BOM
# -----------------------------------------------------------
@bom_bp.get("/deduped")
def get_deduped_bom():
    """
    Returns deduped BOM with unique itemSource combinations.
    """
    doc_url = request.args.get("url", "")
    if not doc_url:
        return jsonify({"error": "Missing ?url= parameter"}), 400

    rows = BomHandler.fetch_deduped_bom(doc_url)
    return jsonify({"rows": rows})
