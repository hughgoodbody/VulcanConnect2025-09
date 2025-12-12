# app/public_api/debug_routes.py

from flask import Blueprint, request, jsonify

from app.handlers.config_handler import ConfigHandler
from app.handlers.bom_handler import BomHandler
from app.services.part_list_service import PartListService
import app.state.memory as memory



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

        

        # 3. Build master part list
        master_list = PartListService.build_master_part_list(
            onshape_url,
            encoded_id,
            bom["raw"],                # full BOM dict
            bom["filtered"],           # filtered rows
            bom["dedupBySource"]       # deduped rows
        )

        # 🚨 TEMPORARY: Return BOMs so you can inspect their structure
        return jsonify({
            "success": True,
            "encodedId": encoded_id,
            "filteredBom_preview": bom["filtered"][:5],
            "dedupBom_preview": bom["dedupBySource"][:5],
            "filteredBom_full": bom["filtered"],
            "dedupBom_full": bom["dedupBySource"],
            "masterPartList": master_list
        }), 200

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500

@debug_bp.get("/updated-parts")
def debug_updated_parts():
    """
    Returns the last payload received by POST /api/job/updateParts.
    Useful for debugging Elementor table output.
    """
    if memory.last_updated_parts is None:
        return jsonify({"success": False, "message": "No updates have been posted yet"}), 200

    return jsonify({
        "success": True,
        "lastUpdatedParts": memory.last_updated_parts
    }), 200
