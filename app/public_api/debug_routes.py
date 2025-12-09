# app/public_api/debug_routes.py

from flask import Blueprint, request, jsonify

from app.handlers.config_handler import ConfigHandler
from app.handlers.bom_handler import BomHandler
from app.services.part_list_service import PartListService


debug_bp = Blueprint("debug", __name__)


@debug_bp.get("/master-part-list")
def debug_master_part_list():
    """
    Development-only endpoint:
    Builds master part list using DEVELOPMENT_MODE mock files.
    """

    # Allow a URL override for flexibility
    onshape_url = request.args.get(
        "url",
        "https://cad.onshape.com/documents/FAKE_DOCUMENT/w/wid/e/eid"
    )

    try:
        # 1. Mock configuration encoding
        encoded_id = ConfigHandler.encode_configuration(onshape_url, [{"parameterId": "MOCK", "parameterValue": 1}])

        # 2. Mock BOM
        bom = BomHandler.fetch_bom_for_configuration(onshape_url, encoded_id)
        filtered_bom = bom["filtered"]
        dedup_bom_by_source = bom["dedupBySource"]

        # 🚨 TEMPORARY: Return BOMs so you can inspect their structure
        return jsonify({
            "success": True,
            "encodedId": encoded_id,
            "filteredBom_preview": filtered[:5],   # first 5 rows
            "dedupBom_preview": dedup[:5],         # first 5 rows
            "filteredBom_full": filtered,
            "dedupBom_full": dedup
        }), 200

        # 3. Build master part list
        master_list = PartListService.build_master_part_list(
            onshape_url,
            encoded_id,
            filtered_bom,
            dedup_bom_by_source
        )

        return jsonify({
            "success": True,
            "encodedId": encoded_id,
            "filteredBom": filtered_bom,
            "dedupBomBySource": dedup_bom_by_source,
            "masterPartList": master_list
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500
