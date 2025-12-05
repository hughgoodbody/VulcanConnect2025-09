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
# Face / edge relationships
# ---------------------------------------------------------------------------

def calculate_thickness(face1: Dict[str, Any], face2: Dict[str, Any]) -> float:
    o1 = face1["surface"]["origin"]
    o2 = face2["surface"]["origin"]
    vec = (o1["x"] - o2["x"], o1["y"] - o2["y"], o1["z"] - o2["z"])
    n = [
        face1["surface"]["normal"]["x"],
        face1["surface"]["normal"]["y"],
        face1["surface"]["normal"]["z"],
    ]
    return abs(dotProduct(vec, n))


def are_faces_parallel(face1: Dict[str, Any], face2: Dict[str, Any], tol: float) -> bool:
    n1 = face1["surface"]["normal"]
    n2 = face2["surface"]["normal"]
    dot = n1["x"] * n2["x"] + n1["y"] * n2["y"] + n1["z"] * n2["z"]
    return abs(dot - 1) <= tol


def get_face_edges(faces: List[Dict[str, Any]], face_index: int) -> List[Any]:
    edge_list: List[Any] = []
    for loop_data in faces[face_index].get("loops", []):
        for edge_data in loop_data.get("coedges", []):
            edge_list.append(edge_data["edgeId"])
    return edge_list


def are_faces_adjacent(
    qtyFaces: List[Dict[str, Any]],
    largestFace0_index: int,
    largestFace1_index: int,
) -> bool:
    largestFace0_edges = get_face_edges(qtyFaces, largestFace0_index)
    largestFace1_edges = get_face_edges(qtyFaces, largestFace1_index)

    for i in range(len(qtyFaces)):
        if i in (largestFace0_index, largestFace1_index):
            continue
        test_edges = get_face_edges(qtyFaces, i)
        is_adjacent = (
            any(e in largestFace0_edges for e in test_edges)
            and any(e in largestFace1_edges for e in test_edges)
        )
        if not is_adjacent:
            return False

    return True


def are_faces_perpendicular(
    qtyFaces: List[Dict[str, Any]],
    largestFace0_index: int,
    largestFace1_index: int,
    tolerance: float,
) -> bool:
    normal1 = qtyFaces[largestFace0_index]["surface"]["normal"]
    normal2 = qtyFaces[largestFace1_index]["surface"]["normal"]

    for i in range(len(qtyFaces)):
        if i in (largestFace0_index, largestFace1_index):
            continue

        surface = qtyFaces[i]["surface"]
        stype = surface.get("type")

        # Planar faces
        if stype == "PLANE":
            test_normal = surface["normal"]
            i_1 = abs(
                normal1["x"] * test_normal["x"]
                + normal1["y"] * test_normal["y"]
                + normal1["z"] * test_normal["z"]
            )
            i_2 = abs(
                normal2["x"] * test_normal["x"]
                + normal2["y"] * test_normal["y"]
                + normal2["z"] * test_normal["z"]
            )
            if abs(i_1 - 1) <= tolerance and abs(i_2 - 1) <= tolerance:
                return False

        # Cylindrical faces
        elif stype == "CYLINDER":
            axis = surface["axis"]
            test_normal = {"x": axis["x"], "y": axis["y"], "z": axis["z"]}
            i_1 = abs(
                normal1["x"] * test_normal["x"]
                + normal1["y"] * test_normal["y"]
                + normal1["z"] * test_normal["z"]
            )
            i_2 = abs(
                normal2["x"] * test_normal["x"]
                + normal2["y"] * test_normal["y"]
                + normal2["z"] * test_normal["z"]
            )
            if abs(i_1 - 1) >= tolerance and abs(i_2 - 1) >= tolerance:
                return False

        # Other surfaces (use direction)
        else:
            try:
                d = surface["direction"]
                test_normal = {"x": d["x"], "y": d["y"], "z": d["z"]}
                i_1 = abs(
                    normal1["x"] * test_normal["x"]
                    + normal1["y"] * test_normal["y"]
                    + normal1["z"] * test_normal["z"]
                )
                i_2 = abs(
                    normal2["x"] * test_normal["x"]
                    + normal2["y"] * test_normal["y"]
                    + normal2["z"] * test_normal["z"]
                )
                if abs(i_1 - 1) >= tolerance and abs(i_2 - 1) >= tolerance:
                    return False
            except Exception:
                return False

    return True


def find_longest_edge(
    qtyFaces: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    largestFace0_index: int,
) -> Any:
    longest_linear = 0.0
    longest_non_linear = 0.0
    linear_edge_flag = False
    longest_linear_edge_id = None
    longest_non_linear_edge_id = None

    largestFace0_edges = get_face_edges(qtyFaces, largestFace0_index)

    for edge_id in largestFace0_edges:
        edge_index = search(edges, "id", edge_id)
        if edge_index is None:
            continue

        edge_data = edges[edge_index]
        etype = edge_data.get("curve", {}).get("type")
        length = edge_data.get("geometry", {}).get("length", 0.0)

        if etype == "LINE":
            if length >= longest_linear:
                longest_linear = length
                linear_edge_flag = True
                longest_linear_edge_id = edge_id
        else:
            if length >= longest_non_linear:
                longest_non_linear = length
                longest_non_linear_edge_id = edge_id

    if linear_edge_flag and longest_linear_edge_id is not None:
        return longest_linear_edge_id
    return longest_non_linear_edge_id


def compute_view_matrix(
    edges: List[Dict[str, Any]],
    facesList: List[Dict[str, Any]],
    longestEdgeID: Any,
    largestFace0_index: int,
) -> List[float]:
    """
    Build a 4x4 view matrix based on the longest edge and the face normal.

    Layout:
      [ x0, x1, x2, 0,
        y0, y1, y2, 0,
        z0, z1, z2, 0,
        tx, ty, tz, 1 ]
    """
    viewMatrix = [0.0] * 16
    viewMatrix[15] = 1.0

    longestEdgeIndex = search(edges, "id", longestEdgeID)
    if longestEdgeIndex is None:
        raise ValueError("Longest edge ID not found in edges list")

    edge = edges[longestEdgeIndex]
    sv = edge["geometry"]["startVector"]

    # x axis
    viewMatrix[0] = sv["x"]
    viewMatrix[1] = sv["y"]
    viewMatrix[2] = sv["z"]

    # z axis (face normal)
    normal = facesList[largestFace0_index]["surface"]["normal"]
    viewMatrix[8] = normal["x"]
    viewMatrix[9] = normal["y"]
    viewMatrix[10] = normal["z"]

    # y axis = cross(x, z)
    yAxis = numpy.cross(
        [sv["x"], sv["y"], sv["z"]],
        [normal["x"], normal["y"], normal["z"]],
    )
    viewMatrix[4] = -yAxis[0]
    viewMatrix[5] = -yAxis[1]
    viewMatrix[6] = -yAxis[2]

    origin = facesList[largestFace0_index]["surface"]["origin"]
    viewMatrix[12] = origin["x"]
    viewMatrix[13] = origin["y"]
    viewMatrix[14] = origin["z"]

    return viewMatrix


def undersize_holes(edges: List[Dict[str, Any]]) -> Optional[float]:
    """
    Return smallest circular edge diameter from edges list, else None.
    """
    smallest: Optional[float] = None
    for edge in edges:
        if edge.get("curve", {}).get("type") == "CIRCLE":
            diameter = edge.get("radius", 0.0) * 2
            if smallest is None or diameter < smallest:
                smallest = diameter
    return smallest


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
    text.dxf.halign = 4
