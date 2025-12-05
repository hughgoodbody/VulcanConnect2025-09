# app/services/encoding_service.py

from typing import Any, Dict, List


def build_parameter_list(raw_values: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert {parameterId: value} into the list format expected by Onshape.
    """
    parameters: List[Dict[str, Any]] = []
    for pid, value in raw_values.items():
        if value is None:
            continue
        parameters.append(
            {
                "parameterId": pid,
                "parameterValue": value,
            }
        )
    return parameters
