# app/services/encoding_service.py

from typing import Any, Dict, List


def build_parameter_list(raw_values: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert { parameterId: value } into a list Onshape expects:
    [{ "parameterId": "...", "parameterValue": "..." }]

    IMPORTANT:
    - parameterValue MUST be a string
    - booleans -> "true"/"false"
    - numbers -> string
    """
    parameters: List[Dict[str, Any]] = []

    for pid, value in raw_values.items():
        if value is None:
            continue

        if isinstance(value, bool):
            param_value = "true" if value else "false"
        else:
            param_value = str(value)

        parameters.append(
            {
                "parameterId": pid,
                "parameterValue": param_value,
            }
        )

    return parameters
