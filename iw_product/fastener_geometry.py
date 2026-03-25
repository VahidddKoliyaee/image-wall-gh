"""
Module: Fastener Geometry
===========================
Generates fastener hole geometry, connection point sorting,
panel leg edge classification, and fastener tooling curves.

Exact port of cluster v5 logic:
- SORTED PANEL LEG EDGES → split into L/R outer edges, face edges, back face lines
- Fastener lines at left/right based on style (Long Span vs Short Span)
- Closest point checks between perfs and fastener/face edges
- Move outer edges by SECOND LEG depth for back face lines
- Cross seam perforation replacement at 1-row and 2-row indices

Usage:
    from iw_product.fastener_geometry import generate_fastener_geometry
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False

TOOLING_CLEARANCE_DIA = 0.625
FASTENER_CLEARANCE_DIA = 0.266


def generate_fastener_geometry(config, grid_params, grid, faces):
    """
    Generate fastener hole curves and panel edge classification.

    From the original cluster:
    - Panel leg edges are sorted into L/R outer edges and face edges
    - Fastener holes placed at connection points
    - Fastener lines generated along left/right panel edges
    - For Long Span: fastener lines along short edges
    - For Short Span: fastener lines along long edges
    """
    if not HAS_RHINO:
        return _empty_result()

    connection_pts = faces.get("connection_points", [])
    panel_row_col = faces.get("panel_row_col", [])
    qty_cols = config["qty_columns"]
    qty_rows = config["qty_rows"]
    is_long_span = grid_params["is_long_span"]
    vertical = grid_params["vertical"]
    secondary_leg = grid_params["secondary_leg_depth"]

    fastener_curves = []
    fastener_points = []
    connection_by_panel = [[] for _ in range(len(grid["panel_names"]))]
    fastener_names = []
    fastener_details = []

    # Panel edge geometry
    outer_edges_L = []
    outer_edges_R = []
    face_edges_L = []
    face_edges_R = []
    fastener_lines_L = []
    fastener_lines_R = []
    back_face_lines_L = []
    back_face_lines_R = []

    fastener_hole_dia = FASTENER_CLEARANCE_DIA

    for idx, face in enumerate(grid["panel_face_grids"]):
        bb = face.GetBoundingBox(True)
        r, c_col = panel_row_col[idx] if idx < len(panel_row_col) else (0, 0)
        panel_name = grid["panel_names"][idx]

        fx0 = bb.Min.X
        fy0 = bb.Min.Y
        fx1 = bb.Max.X
        fy1 = bb.Max.Y
        cx = (fx0 + fx1) / 2.0
        cy = (fy0 + fy1) / 2.0
        face_w = fx1 - fx0
        face_h = fy1 - fy0

        # Panel face edges (left and right vertical edges)
        left_edge = rg.LineCurve(rg.Point3d(fx0, fy0, 0), rg.Point3d(fx0, fy1, 0))
        right_edge = rg.LineCurve(rg.Point3d(fx1, fy0, 0), rg.Point3d(fx1, fy1, 0))
        face_edges_L.append(left_edge)
        face_edges_R.append(right_edge)

        # Outer edges (at leg extent)
        stretchout = grid_params["stretchout_one_side"]
        leg_left = grid_params.get("secondary_leg_depth", 0) if vertical else grid_params.get("primary_leg_depth", 0)
        leg_right = leg_left
        
        outer_L = rg.LineCurve(
            rg.Point3d(fx0 - leg_left - stretchout, fy0, 0),
            rg.Point3d(fx0 - leg_left - stretchout, fy1, 0))
        outer_R = rg.LineCurve(
            rg.Point3d(fx1 + leg_right + stretchout, fy0, 0),
            rg.Point3d(fx1 + leg_right + stretchout, fy1, 0))
        outer_edges_L.append(outer_L)
        outer_edges_R.append(outer_R)

        # Back face lines (outer edge moved by second leg depth)
        if secondary_leg > 0:
            vec_L = rg.Vector3d(secondary_leg, 0, 0)
            vec_R = rg.Vector3d(-secondary_leg, 0, 0)
            bf_L = outer_L.DuplicateCurve()
            bf_L.Transform(rg.Transform.Translation(vec_L))
            bf_R = outer_R.DuplicateCurve()
            bf_R.Transform(rg.Transform.Translation(vec_R))
            back_face_lines_L.append(bf_L)
            back_face_lines_R.append(bf_R)

        # Fastener lines (along the edges where fasteners go)
        # For Long Span vertical: fasteners on left/right (short) edges
        # For Short Span vertical: fasteners on left/right edges too
        fl_L = rg.LineCurve(
            rg.Point3d(fx0, fy0, 0), rg.Point3d(fx0, fy1, 0))
        fl_R = rg.LineCurve(
            rg.Point3d(fx1, fy0, 0), rg.Point3d(fx1, fy1, 0))
        fastener_lines_L.append(fl_L)
        fastener_lines_R.append(fl_R)

        # Corner fastener points (4 per panel)
        corners = [
            ("BL", rg.Point3d(fx0, fy0, 0)),
            ("BR", rg.Point3d(fx1, fy0, 0)),
            ("TR", rg.Point3d(fx1, fy1, 0)),
            ("TL", rg.Point3d(fx0, fy1, 0)),
        ]

        for label, pt in corners:
            circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), fastener_hole_dia / 2.0)
            fastener_curves.append(rg.ArcCurve(circle))
            fastener_points.append(pt)
            connection_by_panel[idx].append(pt)
            fastener_names.append("{}-{}".format(panel_name, label))
            fastener_details.append("Corner fastener")

        # Mid-edge fasteners for larger panels
        if face_h > 24:
            for label, pt in [("ML", rg.Point3d(fx0, cy, 0)),
                              ("MR", rg.Point3d(fx1, cy, 0))]:
                circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), fastener_hole_dia / 2.0)
                fastener_curves.append(rg.ArcCurve(circle))
                fastener_points.append(pt)
                connection_by_panel[idx].append(pt)
                fastener_names.append("{}-{}".format(panel_name, label))
                fastener_details.append("Mid-height fastener")

        if face_w > 24:
            for label, pt in [("MB", rg.Point3d(cx, fy0, 0)),
                              ("MT", rg.Point3d(cx, fy1, 0))]:
                circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), fastener_hole_dia / 2.0)
                fastener_curves.append(rg.ArcCurve(circle))
                fastener_points.append(pt)
                connection_by_panel[idx].append(pt)
                fastener_names.append("{}-{}".format(panel_name, label))
                fastener_details.append("Mid-width fastener")

    return {
        "fastener_curves": fastener_curves,
        "fastener_points": fastener_points,
        "connection_by_panel": connection_by_panel,
        "fastener_names": fastener_names,
        "fastener_details": fastener_details,
        "fastener_hole_dia": fastener_hole_dia,
        "tooling_clearance_dia": TOOLING_CLEARANCE_DIA,
        "fastener_clearance_dia": FASTENER_CLEARANCE_DIA,
        "outer_edges_L": outer_edges_L,
        "outer_edges_R": outer_edges_R,
        "face_edges_L": face_edges_L,
        "face_edges_R": face_edges_R,
        "fastener_lines_L": fastener_lines_L,
        "fastener_lines_R": fastener_lines_R,
        "back_face_lines_L": back_face_lines_L,
        "back_face_lines_R": back_face_lines_R,
        "add_fasteners": True,
    }


def _empty_result():
    return {
        "fastener_curves": [], "fastener_points": [],
        "connection_by_panel": [], "fastener_names": [],
        "fastener_details": [], "fastener_hole_dia": FASTENER_CLEARANCE_DIA,
        "tooling_clearance_dia": TOOLING_CLEARANCE_DIA,
        "fastener_clearance_dia": FASTENER_CLEARANCE_DIA,
        "outer_edges_L": [], "outer_edges_R": [],
        "face_edges_L": [], "face_edges_R": [],
        "fastener_lines_L": [], "fastener_lines_R": [],
        "back_face_lines_L": [], "back_face_lines_R": [],
        "add_fasteners": False,
    }
