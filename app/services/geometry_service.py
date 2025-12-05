# app/services/geometry_service.py

import math
import numpy
from typing import Any, Dict, List, Optional, Sequence
from ezdxf.gfxattribs import GfxAttribs


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def load_js_function_as_string(path_to_js_file: str) -> str:
    with open(path_to_js_file, "r", encoding="utf-8") as file:
        return file.read()


def findInList(lst: List[Dict[str, Any]], key: str, value: Any) -> int:
    """Return index of dict where dict[key] == value, else -1."""
    for i, dic in enumerate(lst):
        if dic.get(key) == value:
            return i
    return -1


def search(lst: List[Dict[str, Any]], key: str, value: Any) -> Optional[int]:
    """Return index in list where dict[key] == value."""
    return next((i for i, d in enumerate(lst) if d.get(key) == value), None)


def dotProduct(v1: Sequence[float], v2: Sequence[float]) -> float:
    dp = abs(v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2])
    return dp


def pointDistance(p1: Sequence[float], p2: Sequence[float]) -> float:
    return math.sqrt(
        (p1[0] - p2[0]) ** 2 +
        (p1[1] - p2[1]) ** 2 +
        (p1[2] - p2[2]) ** 2
    )


def find_face_index(faces: List[Dict[str, Any]], face_id: Any) -> Optional[int]:
    return next((i for i, f in enumerate(faces) if f.get("id") == face_id), None)


# ---------------------------------------------------------------------------
# DXF Dimensioning
# ---------------------------------------------------------------------------

def detailTapping(hole, msp):
    """
    Add tapping detail label to DXF.
    """
    xtapinfo = "M6 x 1.75 - H6 THRU"
    hole_center = hole.dxf.center

    msp.add_radius_dim(
        center=(hole_center[0], hole_center[1]),
        radius=hole.dxf.radius,
        angle=45,
        text=" " + xtapinfo,
        dimstyle="EZ_RADIUS",
        override={"dimtad": 1, "dimtoh": 1},
        dxfattribs={"layer": "Hole_Tapping"},
    ).render()


def dimensionPrincipal(msp):
    """
    Dimension the longest line in the DXF modelspace.
    """
    longest = {"line": None, "len": 0}
    for line in msp.query("LINE"):
        length = pointDistance(line.dxf.start, line.dxf.end)
        if length > longest["len"]:
            longest = {"line": line, "len": length}

    if longest["line"]:
        msp.add_aligned_dim(
            p1=longest["line"].dxf.start,
            p2=longest["line"].dxf.end,
            distance=-1,
            override={"dimtad": 4},
            dxfattribs={"layer": "Dimensions"},
        ).render()


def dimensionBoundingBox(msp, bb, txt_h):
    s = 6
    attribs = GfxAttribs(layer="Dimensions")

    h_start = (bb.extmin[0], bb.extmin[1] - s)
    h_end   = (bb.extmax[0], bb.extmin[1] - s)
    v_start = (bb.extmin[0] - s, bb.extmin[1])
    v_end   = (bb.extmin[0] - s, bb.extmax[1])

    msp.add_line(h_start, h_end, dxfattribs=attribs)
    msp.add_line(v_start, v_end, dxfattribs=attribs)

    msp.add_line((bb.extmin[0] - 5, bb.extmin[1] - 5 - s),
                 (bb.extmin[0] + 5, bb.extmin[1] + 5 - s),
                 dxfattribs=attribs)

    msp.add_line((bb.extmax[0] - 5, bb.extmin[1] - 5 - s),
                 (bb.extmax[0] + 5, bb.extmin[1] + 5 - s),
                 dxfattribs=attribs)

    width  = math.ceil(abs(bb.extmax[0] - bb.extmin[0]))
    height = math.ceil(abs(bb.extmax[1] - bb.extmin[1]))

    h_pos = (bb.extmin[0] + width / 2, bb.extmin[1] - (txt_h + 2))
    v_pos = (bb.extmin[0] - (txt_h + s), bb.extmin[1] + (height / 2))

    t = msp.add_text(width).set_placement(h_pos)
    t.dxf.height = txt_h
    t.dxf.layer = "Dimensions"

    t = msp.add_text(height).set_placement(v_pos)
    t.dxf.height = txt_h
    t.dxf.rotation = 90
    t.dxf.layer = "Dimensions"
