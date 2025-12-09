from flask import Blueprint, request, jsonify
from app.handlers.configHandler import encode_configuration
from app.handlers.bomHandler import fetch_deduped_bom   # adjust import if needed
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
            return jsonify({"error": "Missing Onshape URL"}), 400

        # 1. Convert UI config values → Onshape parameter list
        parameter_list = build_parameter_list(config_values)

        # 2. Encode configuration (Onshape encodedId)
        encoded_id = encode_configuration(onshape_url, parameter_list)

        if not encoded_id:
            return jsonify({"error": "Failed to encode configuration"}), 500

        # 3. Get BOM for this encodedId
        bom = fetch_deduped_bom(onshape_url, encoded_id)

        # 4. Final response
        return jsonify({
            "success": True,
            "encodedId": encoded_id,
            "bom": bom,
            "userOptions": user_options
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500
