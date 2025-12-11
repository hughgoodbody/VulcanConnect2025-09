import numpy as np
import math
import matplotlib.pyplot as plt
from io import BytesIO
import base64


# ============================================================================
# GEOMETRY UTILS
# ============================================================================

def v(vec):  # Convert Onshape vector dict → numpy array
    return np.array([vec["x"], vec["y"], vec["z"]], dtype=float)


def dot(a, b):
    return float(np.dot(a, b))


def normalised(a):
    n = np.linalg.norm(a)
    return a / n if n != 0 else a


def almost_equal(a, b, tol):
    return abs(a - b) <= tol


def is_parallel(n1, n2, tol):
    """
    Two unit normals are parallel if |dot| ≈ 1
    """
    return abs(abs(dot(n1, n2)) - 1.0) <= tol


def is_perpendicular(n1, n2, tol):
    """
    Perpendicular if |dot| ≈ 0
    """
    return abs(dot(n1, n2)) <= tol


def face_normal(face):
    return normalised(v(face["surface"]["normal"]))


def face_origin(face):
    return v(face["surface"]["origin"])


def cylinder_axis(face):
    return normalised(v(face["surface"]["axis"]))


def sweep_direction(face):
    return normalised(v(face["surface"]["direction"]))


# ============================================================================
# MAIN ALGORITHM
# ============================================================================

class LaserProfileAnalyzer:

    AREA_TOL = 1e-4
    PARALLEL_TOL = 1e-8
    PERP_TOL = 1e-6

    def __init__(self, body, max_thickness_mm):
        self.body = body
        self.faces = body["faces"]
        self.edges = body["edges"]
        self.max_thickness_m = max_thickness_mm / 1000.0

        # Pre-index edges by id for speed
        self.edge_index = {e["id"]: e for e in self.edges}

    # ----------------------------------------------------------------------
    # STEP 1: Largest planar faces
    # ----------------------------------------------------------------------
    def find_largest_planar_faces(self):
        planar = [f for f in self.faces if f["surface"]["type"] == "PLANE"]
        if len(planar) < 2:
            return None

        planar_sorted = sorted(planar, key=lambda f: f["area"], reverse=True)
        f1, f2 = planar_sorted[:2]

        if not almost_equal(f1["area"], f2["area"], self.AREA_TOL):
            return None

        return f1, f2

    # ----------------------------------------------------------------------
    # STEP 2: Parallelism check
    # ----------------------------------------------------------------------
    def check_parallel(self, f1, f2):
        n1 = face_normal(f1)
        n2 = face_normal(f2)
        return is_parallel(n1, n2, self.PARALLEL_TOL)

    # ----------------------------------------------------------------------
    # STEP 3: Thickness calculation
    # ----------------------------------------------------------------------
    def compute_thickness(self, f1, f2):
        n = face_normal(f1)
        delta = face_origin(f1) - face_origin(f2)
        # Uses |dot(Δorigin, normal)| (correct)
        thickness = abs(dot(delta, n))
        return float(round(thickness, 4))

    # ----------------------------------------------------------------------
    # STEP 4: Thickness limit check
    # ----------------------------------------------------------------------
    def check_thickness_limit(self, t):
        return t <= self.max_thickness_m

    # ----------------------------------------------------------------------
    # STEP 5a: Adjacency check (face must touch both main faces)
    # ----------------------------------------------------------------------
    def shared_edge_ids(self, face):
        out = []
        for loop in face["loops"]:
            for c in loop["coedges"]:
                out.append(c["edgeId"])
        return out

    def check_adjacency(self, f1, f2):
        edges1 = set(self.shared_edge_ids(f1))
        edges2 = set(self.shared_edge_ids(f2))

        for face in self.faces:
            if face is f1 or face is f2:
                continue
            edges = set(self.shared_edge_ids(face))

            if not (edges & edges1 and edges & edges2):
                return False

        return True

    # ----------------------------------------------------------------------
    # STEP 5b: Perpendicularity check for all other faces
    # ----------------------------------------------------------------------
    def check_perpendicular_faces(self, f1, f2):
        n1 = face_normal(f1)
        n2 = face_normal(f2)

        for face in self.faces:
            if face is f1 or face is f2:
                continue

            stype = face["surface"]["type"]

            # ---------------- PLANE ----------------
            if stype == "PLANE":
                n = face_normal(face)
                # must be perpendicular to both large face normals
                if (not is_perpendicular(n, n1, self.PERP_TOL) or
                    not is_perpendicular(n, n2, self.PERP_TOL)):
                    return False

            # ---------------- CYLINDER ----------------
            elif stype == "CYLINDER":
                axis = cylinder_axis(face)
                # cylinders: axis must be parallel to main normals
                if not (is_parallel(axis, n1, self.PARALLEL_TOL) or
                        is_parallel(axis, n2, self.PARALLEL_TOL)):
                    return False

            # ---------------- SWEEP / OTHER ----------------
            else:
                try:
                    d = sweep_direction(face)
                    # sweep axis must be parallel to main normals
                    if not (is_parallel(d, n1, self.PARALLEL_TOL) or
                            is_parallel(d, n2, self.PARALLEL_TOL)):
                        return False
                except KeyError:
                    return False

        return True

    # ----------------------------------------------------------------------
    # STEP 6: Find longest usable edge
    # ----------------------------------------------------------------------
    def find_longest_edge(self, face):
        edge_ids = self.shared_edge_ids(face)

        linear_longest = None
        nonlinear_longest = None
        L_lin = 0
        L_non = 0

        for eid in edge_ids:
            e = self.edge_index[eid]
            length = e["geometry"]["length"]
            is_line = (e["curve"]["type"] == "LINE")

            if is_line and length > L_lin:
                L_lin = length
                linear_longest = e

            if not is_line and length > L_non:
                L_non = length
                nonlinear_longest = e

        return linear_longest if linear_longest else nonlinear_longest

    # ----------------------------------------------------------------------
    # STEP 7: View matrix construction
    # ----------------------------------------------------------------------
    def create_view_matrix(self, edge, f1):
        X = normalised(v(edge["geometry"]["startVector"]))
        Z = face_normal(f1)
        Y = normalised(np.cross(X, Z))

        O = face_origin(f1)

        # Column-major OpenGL-style 4×4 matrix flattened
        M = [
            X[0], X[1], X[2], 0,
            Y[0], Y[1], Y[2], 0,
            Z[0], Z[1], Z[2], 0,
            O[0], O[1], O[2], 1
        ]
        return M
    # ======================================================================
    # STEP 8: THUMBNAIL GENERATION
    # ======================================================================
    
    def generate_face_thumbnail(self, face, X_axis, Y_axis, origin):
        """
        Draws a wireframe thumbnail of the face using its edges.
        Returns: Base64 PNG string.
        """
    
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.set_aspect('equal')
        ax.axis('off')
    
        # --- extract edge IDs ---
        edge_ids = self.shared_edge_ids(face)
    
        # --- for each edge, draw its 2D projection ---
        for eid in edge_ids:
            edge = self.edge_index[eid]
            geom = edge["geometry"]
        
            pts3 = []
        
            # 1) If evalPoints exist, use them (best quality)
            if "evalPoints" in geom and geom["evalPoints"]:
                pts3 = [v(p) for p in geom["evalPoints"]]
        
            # 2) else if both startPoint and endPoint exist → treat as straight line
            elif "startPoint" in geom and "endPoint" in geom:
                P1 = v(geom["startPoint"])
                P2 = v(geom["endPoint"])
                pts3 = [P1, P2]
        
            # 3) else fallback
            else:
                # Try best effort
                if "startPoint" in geom:
                    pts3.append(v(geom["startPoint"]))
                if "endPoint" in geom:
                    pts3.append(v(geom["endPoint"]))
                if len(pts3) < 2:
                    continue  # cannot render this edge
        
            # Project 3D → 2D
            pts2 = [(dot(p - origin, X_axis), dot(p - origin, Y_axis)) for p in pts3]
        
            ax.plot([p[0] for p in pts2], [p[1] for p in pts2], color='black', linewidth=1)


    
        # --- Export to Base64 PNG ---
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches='tight', pad_inches=0.05)
        plt.close(fig)
    
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return encoded
    # ============================================================================
    # MAIN DRIVER
    # ============================================================================

    def process(self):
        # Step 1
        f1f2 = self.find_largest_planar_faces()
        if not f1f2:
            return False
        f1, f2 = f1f2

        # Step 2
        if not self.check_parallel(f1, f2):
            return False

        # Step 3 / 4
        thickness = self.compute_thickness(f1, f2)
        if not self.check_thickness_limit(thickness):
            return False

        # Step 5
        if not self.check_adjacency(f1, f2):
            return False
        if not self.check_perpendicular_faces(f1, f2):
            return False

        # Step 6
        longest_edge = self.find_longest_edge(f1)
        if not longest_edge:
            return False

        # Step 7
        view_matrix = self.create_view_matrix(longest_edge, f1)

        # Step 8
        X_axis = normalised(v(longest_edge["geometry"]["startVector"]))
        Z_axis = face_normal(f1)
        Y_axis = normalised(np.cross(X_axis, Z_axis))
        origin = face_origin(f1)
        thumbnail_base64 = self.generate_face_thumbnail(f1, X_axis, Y_axis, origin)

        # Final output record
        return {
            "Face": f1["id"],
            "Thickness_mm": thickness * 1000,
            "Area": f1["area"],
            "Origin": f1["surface"]["origin"],
            "Normal": f1["surface"]["normal"],
            "LongestEdge": longest_edge["id"],
            "ViewMatrix": view_matrix,
            "Description": f"{thickness*1000:.3f} mm Laser Plate",
            "BoxMinCorner": f1["box"]["minCorner"],
            "BoxMaxCorner": f1["box"]["maxCorner"],
            "faceThumbnail": thumbnail_base64,
        }
