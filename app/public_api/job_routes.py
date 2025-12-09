from flask import Blueprint, request, jsonify
from app.handlers.config_handler import ConfigHandler
from app.handlers.bom_handler import BomHandler
import traceback

job_bp = Blueprint("job", __name__)

# ----------------------------------------------------------
# Utility: convert frontend configValues → Onshape param list
# ----------------------------------------------------------
def build_parameter_list(config_values):
    param_list = []

    for param_id, value in config_values.items():

        # Quantity values → { "value": 10, "units": "mm" }
        if isinstance(value, dict) and "value" in value and "units" in value:
            param_list.append({
                "parameterId": param_id,
                "parameterValue": {
                    "type": "BTMParameterQuantity",
                    "value": value["value"],
                    "units": value["units"]
                }
            })

        # Boolean
        elif isinstance(value, bool):
            param_list.append({
                "parameterId": param_id,
                "parameterValue": value
            })

        # Numeric
        elif isinstance(value, (int, float)):
            param_list.append({
                "parameterId": param_id,
                "parameterValue": value
            })

        # Enum / String
        else:
            param_list.append({
                "parameterId": param_id,
                "parameterValue": str(value)
            })

    return param_list


# ----------------------------------------------------------
# POST /api/job/create
# ----------------------------------------------------------
@job_bp.post("/create")
def create_job():
    try:
        payload = request.get_json(force=True)

        if not payload:
            return jsonify({"error": "Missing JSON body"}), 400

        onshape_url = payload.get("onshapeUrl")
        config_values = payload.get("configValues", {})
        user_options = payload.get("userOptions", {})

        if not onshape_url:
            return jsonify({"error": "Missing onshapeUrl"}), 400

        # 1. Convert UI → Onshape parameter payload
        parameter_list = build_parameter_list(config_values)

        # 2. Encode configuration
        encoded_id = ConfigHandler.encode_configuration(onshape_url, parameter_list)

        # 3. Use encodedId to retrieve BOM
        bom = BomHandler.fetch_bom_for_configuration(onshape_url, encoded_id)
        filtered_bom = bom["filtered"]
        dedup_bom_by_source = bom["dedupBySource"]

        # 4. Return result
        return jsonify({
            "success": True,
            "encodedId": encoded_id,
            "filteredBom": filtered_bom,
            "dedupBomBySource": dedup_bom_by_source,
            "userOptions": user_options
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500
