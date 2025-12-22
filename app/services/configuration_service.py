# app/services/configuration_service.py

from typing import Any, Dict, List


def build_ui_schema(config_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Onshape's configurationStructure into a clean UI schema used by Elementor.
    """
    parameters = config_json.get("configurationParameters", [])
    ui_parameters: List[Dict[str, Any]] = []

    for param in parameters:
        type_name = param.get("btType")
        name = param.get("parameterName", "Unnamed")
        param_id = param.get("parameterId", "unknown")

        entry: Dict[str, Any] = {
            "id": param_id,
            "name": name,
            "rawType": type_name,
        }

        # ENUM PARAMETERS
        if type_name.startswith("BTMConfigurationParameterEnum"):
            entry["type"] = "enum"
        
            # IMPORTANT:
            # - label = optionName (UI)
            # - value = option (what Onshape expects)
            entry["options"] = [
                {
                    "label": opt.get("optionName", "Unnamed"),
                    "value": opt.get("option"),
                }
                for opt in param.get("options", [])
                if "option" in opt
            ]
            # IMPORTANT: this is the OPTION TOKEN
            entry["default"] = param.get("defaultValue")

        # BOOLEAN PARAMETERS
        elif type_name.startswith("BTMConfigurationParameterBoolean"):
            entry["type"] = "boolean"
            entry["default"] = param.get("defaultValue", False)

        # QUANTITY PARAMETERS
        elif type_name.startswith("BTMConfigurationParameterQuantity"):
            range_msg = param.get("rangeAndDefault", {})
            entry["type"] = "quantity"
            entry["min"] = range_msg.get("minValue", 0)
            entry["max"] = range_msg.get("maxValue", 1000)
            entry["default"] = range_msg.get("defaultValue", entry["min"])
            entry["units"] = range_msg.get("units", "mm")

        else:
            entry["type"] = "unsupported"

        ui_parameters.append(entry)

    return {"parameters": ui_parameters}
