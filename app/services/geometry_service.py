# app/services/geometry_service.py

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy  # type: ignore
from ezdxf.gfxattribs import GfxAttribs  # type: ignore


# ---------------------------------------------------------------------------
# General utilities
# ---------------------------------------------------------------------------

def load_js_function_as_string(path_to_js_file: str) -> str:
    """Load the contents of a JS file as a string."""
    with open(path_to_js_file, "r", encoding="utf-8") as file:
        return file.read()


def findInList(lst: List[Dict[str, Any]], key: str, value: Any) -> int:
    """Return index of dict in list where dict[key] == value, or -1 if not found."""
    for i, dic in enumerate(lst):
        if dic.get(key) == value:
            return i
    return -1


def search(lst: List[Dict[str, Any]], key: str, value: Any) -> Optional[int]:
    """Return index of dict in list where dict[key] == value, or None if not found."""
    return next((index for (index, d) in enumerate(lst) if d.get(key) == value), None)


def dotProduct(vector1: Sequence[float], vector2: Sequence[float]) -> float:
    """Absolute value of the dot product of two 3D vectors."""
    dot_val = (vector1[0] * vector2[0]) + (vector1[1] * vector2[1]) + (vector1[2] * vector2[2])
    return abs(dot_val)


def pointDistance(point1: Sequence[float], point2: Sequence[float]) -> float:
    """Euclidean distance between two 3D points."""
    return math.sqrt(
        (point1[0] - point2[0]) ** 2
        + (point1[1] - point2[1]) ** 2
        + (point1[2] - point2[2]) ** 2
    )


def find_face_index(faces: List[Dict[str, Any]], face_id: Any) -> Optional[int]:
    """Return index of face dict with given id, or None."""
    return next((i for i, f in enumerate(faces) if f.get("id") == face_id), None)


def calculate_thickness(face1: Dict[str, Any], face2: Dict[str, Any]) -> float:
    """Calculate thickness between two faces using their origins and face1 normal."""
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
    """Return True if faces are parallel within a tolerance based on their normals."""
    n1 = face1["surface"]["normal"]
    n2 = face2["surface"]["normal"]
    dot = n1["x"] * n2["x"] + n1["y"] * n2["y"] + n1["z"] * n2["z"]
    return abs(dot - 1) <= tol


# ---------------------------------------------------------------------------
# DXF / dimensioning utilities
# ---------------------------------------------------------------------------

def detailTapping(hole: Any, msp: Any) -> None:
    """
    Add tapping detail to a hole in a DXF modelspace.

    :param hole: DXF circle-like entity with .dxf.radius and .dxf.center
    :param msp: DXF modelspace
    """
    xtapinfo = "M6 x 1.75 - H6 THRU"
    hole_diameter = round((hole.dxf.radius * 2), 1)

    # centre of circle
    hole_centre = hole.dxf.center
    hole_x_coordinate = hole_centre[0]
    hole_y_coordinate = hole_centre[1]

    msp.add_radius_dim(
        center=(hole_x_coordinate, hole_y_coordinate),
        radius=hole.dxf.radius,
        angle=45,
        text=" " + xtapinfo,
        dimstyle="EZ_RADIUS",
        override={"dimtad": 1, "dimtoh": 1},
        dxfattribs={"layer": "Hole_Tapping"},
    ).render()


def dimensionPrincipal(msp: Any) -> None:
    """Dimension the longest line in modelspace as a principal dimension."""
    longest_line = {"Line Object": None, "Line Length": 0.0}
    lines_query = msp.query("LINE")

    for line in lines_query:
        line_length = math.sqrt(
            ((line.dxf.end[0] - line.dxf.start[0]) ** 2)
            + ((line.dxf.end[1] - line.dxf.start[1]) ** 2)
        )
        if line_length > longest_line["Line Length"]:
            longest_line["Line Object"] = line
            longest_line["Line Length"] = line_length

    if longest_line["Line Object"] is not None:
        msp.add_aligned_dim(
            p1=longest_line["Line Object"].dxf.start,
            p2=longest_line["Line Object"].dxf.end,
            distance=-1,
            override={"dimtad": 4},
            dxfattribs={"layer": "Dimensions"},
        ).render()


def dimensionBoundingBox(msp: Any, xboundingBox: Any, xtextHeight: float) -> None:
    """
    Create horizontal and vertical bounding box dimensions using manual DXF entities.
    """
    second_horizontal_point = (xboundingBox.extmax[0], xboundingBox.extmin[1])
    second_vertical_point = (xboundingBox.extmin[0], xboundingBox.extmax[1])

    s = 6  # spacing between dimension line and model
    attribs = GfxAttribs(layer="Dimensions")

    h_start = (xboundingBox.extmin[0], (xboundingBox.extmin[1] - s))
    h_end = (xboundingBox.extmax[0], (xboundingBox.extmin[1] - s))
    v_start = (xboundingBox.extmin[0] - s, (xboundingBox.extmin[1]))
    v_end = (xboundingBox.extmin[0] - s, xboundingBox.extmax[1])

    # main dimension lines
    horiz_line = msp.add_line(h_start, h_end, dxfattribs=attribs)
    vert_line = msp.add_line(v_start, v_end, dxfattribs=attribs)

    # oblique ends for horizontal
    msp.add_line(
        (xboundingBox.extmin[0] - 5, xboundingBox.extmin[1] - 5 - s),
        (xboundingBox.extmin[0] + 5, xboundingBox.extmin[1] + 5 - s),
        dxfattribs=attribs,
    )
    msp.add_line(
        (xboundingBox.extmax[0] - 5, xboundingBox.extmin[1] - 5 - s),
        (xboundingBox.extmax[0] + 5, xboundingBox.extmin[1] + 5 - s),
        dxfattribs=attribs,
    )

    # oblique ends for vertical
    msp.add_line(
        (xboundingBox.extmin[0] - 5 - s, xboundingBox.extmin[1] - 5),
        (xboundingBox.extmin[0] + 5 - s, xboundingBox.extmin[1] + 5),
        dxfattribs=attribs,
    )
    msp.add_line(
        (xboundingBox.extmin[0] - 5 - s, xboundingBox.extmax[1] - 5),
        (xboundingBox.extmin[0] + 5 - s, xboundingBox.extmax[1] + 5),
        dxfattribs=attribs,
    )

    # numeric labels
    horiz_length = math.ceil(abs(xboundingBox.extmax[0] - xboundingBox.extmin[0]))
    vert_length = math.ceil(abs(xboundingBox.extmax[1] - xboundingBox.extmin[1]))

    h_dim_pos = (
        xboundingBox.extmin[0] + (horiz_length / 2),
        (xboundingBox.extmin[1] - (xtextHeight + 2)),
    )
    v_dim_pos = (
        xboundingBox.extmin[0] - ((xtextHeight / 2)) - (s + 2),
        (xboundingBox.extmin[1] + (vert_length / 2)),
    )

    text = msp.add_text(horiz_length).set_placement(h_dim_pos)
    text.dxf.height = xtextHeight
    text.dxf.layer = "Dimensions"
    text.dxf.halign = 4

    text = msp.add_text(vert_length).set_placement(v_dim_pos)
    text.dxf.height = xtextHeight
    text.dxf.rotation = 90
    text.dxf.layer = "Dimensions"
    text.dxf.halign = 4


# ---------------------------------------------------------------------------
# Face / edge / view-matrix helpers
# ---------------------------------------------------------------------------

def get_face_edges(faces: List[Dict[str, Any]], face_index: int) -> List[Any]:
    edge_list: List[Any] = []
    for loop_data in faces[face_index].get("loops", []):
        for coedge in loop_data.get("coedges", []):
            edge_id = coedge.get("edgeId")
            edge_list.append(edge_id)
    return edge_list


def are_faces_adjacent(qtyFaces: List[Dict[str, Any]], largestFace0_index: int, largestFace1_index: int) -> bool:
    largestFace0_edges = get_face_edges(qtyFaces, largestFace0_index)
    largestFace1_edges = get_face_edges(qtyFaces, largestFace1_index)

    for i in range(len(qtyFaces)):
        if i in (largestFace0_index, largestFace1_index):
            continue

        test_edges = get_face_edges(qtyFaces, i)
        bool_val = (any(e in largestFace0_edges for e in test_edges)) and (
            any(e in largestFace1_edges for e in test_edges)
        )
        if bool_val is False:
            return False

    return True


def are_faces_perpendicular(
    qtyFaces: List[Dict[str, Any]],
    largestFace0_index: int,
    largestFace1_index: int,
    tolerance: float,
) -> bool:
    largestFace0_edges = get_face_edges(qtyFaces, largestFace0_index)
    largestFace1_edges = get_face_edges(qtyFaces, largestFace1_index)

    normal1 = qtyFaces[largestFace0_index]["surface"]["normal"]
    normal2 = qtyFaces[largestFace1_index]["surface"]["normal"]

    for i in range(len(qtyFaces)):
        if i in (largestFace0_index, largestFace1_index):
            continue

        surface = qtyFaces[i]["surface"]
        if surface["type"] == "PLANE":
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

        elif surface["type"] == "CYLINDER":
            test_normal = {
                "x": surface["axis"]["x"],
                "y": surface["axis"]["y"],
                "z": surface["axis"]["z"],
            }
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

        else:
            try:
                test_normal = {
                    "x": surface["direction"]["x"],
                    "y": surface["direction"]["y"],
                    "z": surface["direction"]["z"],
                }
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
        edge_type = edge_data.get("curve", {}).get("type")
        length = edge_data.get("geometry", {}).get("length", 0.0)

        if edge_type == "LINE":
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
    faces_list: List[Dict[str, Any]],
    longestEdgeID: Any,
    largestFace0_index: int,
) -> List[float]:
    """
    Build a 4x4 view matrix (flattened) based on the longest edge and the
    normal of the largest face.
    """
    view_matrix = [0.0] * 16
    view_matrix[15] = 1.0

    longest_edge_index = search(edges, "id", longestEdgeID)
    if longest_edge_index is None:
        raise ValueError("Longest edge ID not found in edges list")

    edge = edges[longest_edge_index]
    start_vec = edge["geometry"]["startVector"]

    # x axis
    view_matrix[0] = start_vec["x"]
    view_matrix[1] = start_vec["y"]
    view_matrix[2] = start_vec["z"]

    # z axis (face normal)
    normal = faces_list[largestFace0_index]["surface"]["normal"]
    view_matrix[8] = normal["x"]
    view_matrix[9] = normal["y"]
    view_matrix[10] = normal["z"]

    # y axis = cross(x, z)
    y_axis = numpy.cross(
        [start_vec["x"], start_vec["y"], start_vec["z"]],
        [normal["x"], normal["y"], normal["z"]],
    )

    view_matrix[4] = -y_axis[0]
    view_matrix[5] = -y_axis[1]
    view_matrix[6] = -y_axis[2]

    origin = faces_list[largestFace0_index]["surface"]["origin"]
    view_matrix[12] = origin["x"]
    view_matrix[13] = origin["y"]
    view_matrix[14] = origin["z"]

    return view_matrix


def undersize_holes(edges: List[Dict[str, Any]]) -> Optional[float]:
    """
    Return the smallest circular edge diameter found in a list of edges,
    or None if no circular edges exist.
    """
    smallest: Optional[float] = None
    for edge in edges:
        if edge.get("curve", {}).get("type") == "CIRCLE":
            diameter = edge.get("radius", 0) * 2
            if smallest is None or diameter < smallest:
                smallest = diameter
    return smallest
