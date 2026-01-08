# app/services/part_operations_service.py

from typing import Dict, Any


def compute_operations_flags(part: Dict[str, Any]) -> Dict[str, bool]:
    """
    Returns:
      {
        hasBend: bool,
        hasDrill: bool,
        hasTap: bool,
        hasEtch: bool
      }
    """

    flags = {
        "hasBend": False,
        "hasDrill": False,
        "hasTap": False,
        "hasEtch": False,
    }

    # ---- BEND (Sheet Metal) ----
    if part.get("sheetMetal") is True:
        flags["hasBend"] = True

    # ---- BODY DETAILS (preferred) ----
    body = part.get("bodyDetails") or {}

    # Example shapes – adapt to your exact bodyDetails schema
    for face in body.get("faces", []):
        ftype = face.get("type")

        if ftype == "CYLINDER":
            # Diameter + depth thresholds help differentiate holes vs shafts
            flags["hasDrill"] = True

        if face.get("threaded") is True:
            flags["hasTap"] = True

    for feature in body.get("features", []):
        ftype = feature.get("type", "").lower()

        if "tap" in ftype or "thread" in ftype:
            flags["hasTap"] = True

        if "hole" in ftype:
            flags["hasDrill"] = True

        if "etch" in ftype or "engrave" in ftype:
            flags["hasEtch"] = True

    return flags


def build_operations_code(flags: Dict[str, bool]) -> str:
    """
    B = Bend (sheet metal)
    T = Tap
    E = Etch
    D = Drill
    """
    code = ""

    if flags.get("hasBend"):
        code += "B"
    if flags.get("hasTap"):
        code += "T"
    if flags.get("hasEtch"):
        code += "E"
    if flags.get("hasDrill"):
        code += "D"

    return code
