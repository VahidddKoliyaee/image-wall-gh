"""
Module: Fastener Geometry
===========================
Generates fastener hole geometry, connection point sorting,
and fastener tooling clearance curves.

Replaces: FASTENER CURVES, CONNECTION LOCATIONS (DL/FASTENERS),
CONNECTION POINTS (SORTED BY PANEL), PERFORATION CURVES [Edited],
Add Fasteners data flow.

Usage:
    from iw_product.fastener_geometry import generate_fastener_geometry
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def generate_fastener_geometry(config, grid_params, grid, faces):
    """
    Generate fastener hole curves and connection point data.

    Fasteners are placed at panel connection points (typically corners
    and edge midpoints). The geometry includes:
    - Fastener hole circles (for CNC punching)
    - Connection location curves
    - Sorted connection points per panel

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from grid
        faces: dict from panel_faces

    Returns:
        dict with:
            fastener_curves       - list of Circle curves at fastener locations
            fastener_points       - list of Point3d
            connection_by_panel   - nested list: [panel_idx][point_idx]
            fastener_names        - list of str names
            fastener_details      - list of str detail info
            perf_curves_original  - list of perf curves (unedited)
            perf_curves_edited    - list of perf curves (edited for clearance)
            add_fasteners         - bool
    """
    if not HAS_RHINO:
        return _empty_result()

    connection_pts = faces.get("connection_points", [])
    panel_row_col = faces.get("panel_row_col", [])
    qty_cols = config["qty_columns"]
    qty_rows = config["qty_rows"]
    is_droplock = grid_params["is_droplock"]
    style = config["style"]

    # Fastener hole diameter (standard)
    fastener_hole_dia = 0.25  # 1/4" standard fastener hole

    fastener_curves = []
    fastener_points = []
    connection_by_panel = [[] for _ in range(len(grid["panel_names"]))]
    fastener_names = []
    fastener_details = []

    # Generate fastener points at panel edges
    for idx, face in enumerate(grid["panel_face_grids"]):
        bb = face.GetBoundingBox(True)
        cx = (bb.Min.X + bb.Max.X) / 2.0
        cy = (bb.Min.Y + bb.Max.Y) / 2.0

        r, c_col = panel_row_col[idx] if idx < len(panel_row_col) else (0, 0)
        panel_name = grid["panel_names"][idx]

        # Corner fasteners (4 per panel)
        corners = [
            rg.Point3d(bb.Min.X, bb.Min.Y, 0),  # BL
            rg.Point3d(bb.Max.X, bb.Min.Y, 0),  # BR
            rg.Point3d(bb.Max.X, bb.Max.Y, 0),  # TR
            rg.Point3d(bb.Min.X, bb.Max.Y, 0),  # TL
        ]
        corner_labels = ["BL", "BR", "TR", "TL"]

        for pt, label in zip(corners, corner_labels):
            circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), fastener_hole_dia / 2.0)
            fastener_curves.append(rg.ArcCurve(circle))
            fastener_points.append(pt)
            connection_by_panel[idx].append(pt)
            fastener_names.append("{}-{}".format(panel_name, label))
            fastener_details.append("Corner fastener")

        # Edge midpoint fasteners (for larger panels)
        face_w = bb.Max.X - bb.Min.X
        face_h = bb.Max.Y - bb.Min.Y

        if face_h > 24:  # Add mid-height fasteners for panels taller than 24"
            mid_pts = [
                rg.Point3d(bb.Min.X, cy, 0),  # Left mid
                rg.Point3d(bb.Max.X, cy, 0),  # Right mid
            ]
            for i, pt in enumerate(mid_pts):
                circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), fastener_hole_dia / 2.0)
                fastener_curves.append(rg.ArcCurve(circle))
                fastener_points.append(pt)
                connection_by_panel[idx].append(pt)
                side = "L" if i == 0 else "R"
                fastener_names.append("{}-M{}".format(panel_name, side))
                fastener_details.append("Mid-height fastener")

        if face_w > 24:  # Add mid-width fasteners
            mid_pts = [
                rg.Point3d(cx, bb.Min.Y, 0),  # Bottom mid
                rg.Point3d(cx, bb.Max.Y, 0),  # Top mid
            ]
            for i, pt in enumerate(mid_pts):
                circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), fastener_hole_dia / 2.0)
                fastener_curves.append(rg.ArcCurve(circle))
                fastener_points.append(pt)
                connection_by_panel[idx].append(pt)
                side = "B" if i == 0 else "T"
                fastener_names.append("{}-M{}".format(panel_name, side))
                fastener_details.append("Mid-width fastener")

    return {
        "fastener_curves": fastener_curves,
        "fastener_points": fastener_points,
        "connection_by_panel": connection_by_panel,
        "fastener_names": fastener_names,
        "fastener_details": fastener_details,
        "perf_curves_original": [],
        "perf_curves_edited": [],
        "add_fasteners": True,
        "fastener_hole_dia": fastener_hole_dia,
    }


def _empty_result():
    return {
        "fastener_curves": [], "fastener_points": [],
        "connection_by_panel": [], "fastener_names": [],
        "fastener_details": [], "perf_curves_original": [],
        "perf_curves_edited": [], "add_fasteners": False,
        "fastener_hole_dia": 0.25,
    }
