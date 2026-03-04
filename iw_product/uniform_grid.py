"""
Module 03: Uniform Grid
========================
Generates uniform panel grid geometry: panel rectangles, face grids,
panel boundaries, joints, and perforation point grids.

Replaces: "Panel Faces [Uniform]" group, Rectangle 2Pt chains,
Series → Vector → Move chains, Rectangular grid, Offset curves.

This module produces Rhino geometry objects and must run inside GH/Rhino.

Usage:
    from iw_product.uniform_grid import build_uniform_grid
    grid = build_uniform_grid(config, grid_params)
"""

import Rhino.Geometry as rg


def _make_rectangle(x0, y0, x1, y1):
    """Create a rectangle polyline from two corner points."""
    pts = [
        rg.Point3d(x0, y0, 0),
        rg.Point3d(x1, y0, 0),
        rg.Point3d(x1, y1, 0),
        rg.Point3d(x0, y1, 0),
        rg.Point3d(x0, y0, 0),
    ]
    return rg.Polyline(pts).ToPolylineCurve()


def _offset_curve_inward(curve, distance):
    """Offset a closed curve inward by distance. Returns offset curve or original."""
    if distance <= 0:
        return curve
    plane = rg.Plane.WorldXY
    offsets = curve.Offset(plane, -distance, 0.001, rg.CurveOffsetCornerStyle.Sharp)
    if offsets and len(offsets) > 0:
        return offsets[0]
    return curve


def build_uniform_grid(config, grid_params):
    """
    Build the full uniform panel grid.

    Args:
        config: dict from config_loader.load_config()
        grid_params: dict from grid_params.compute_grid_params()

    Returns:
        dict with all grid geometry:
            panel_boundaries  - list of panel outline curves (full size)
            panel_face_grids  - list of panel face curves (inset by stretchout)
            panel_face_grids_with_joint - list of face curves with joint offset
            panel_names       - list of panel name strings (e.g. "A1", "B2")
            panel_origins     - list of Point3d panel origin points
            panel_vectors     - list of Vector3d move vectors
            col_widths        - list of column width values
            row_heights       - list of row height values
            col_joints        - list of column joint values
            row_joints        - list of row joint values
            pt_grid_planes    - nested list of XY planes at grid points
            pt_grid_origins   - flat list of Point3d for perforation points
            overall_boundary  - single curve for the full scope boundary
    """
    col_w = config["panel_col_width"]
    row_h = config["panel_row_height"]
    qty_cols = config["qty_columns"]
    qty_rows = config["qty_rows"]
    stretchout = grid_params["stretchout_one_side"]
    panel_joint = grid_params["panel_joint"]
    true_col_sp = grid_params["true_grid_col_spacing"]
    true_row_sp = grid_params["true_grid_row_spacing"]
    qty_pt_cols = grid_params["qty_pt_grid_cols"]
    qty_pt_rows = grid_params["qty_pt_grid_rows"]

    # ── Panel rectangles and naming ───────────────────────────────
    # Series(0, COL_WIDTH, QTY_COLS) × Series(0, ROW_HEIGHT, QTY_ROWS)
    # → cross product → move rectangle to each position
    panel_boundaries = []
    panel_face_grids = []
    panel_face_grids_with_joint = []
    panel_names = []
    panel_origins = []
    panel_vectors = []

    # Base rectangle at origin: (0,0) to (col_w, row_h)
    base_rect = _make_rectangle(0, 0, col_w, row_h)

    for r in range(qty_rows):
        for c in range(qty_cols):
            # Move vector
            vx = c * col_w
            vy = r * row_h
            vec = rg.Vector3d(vx, vy, 0)

            # Panel boundary (full size)
            boundary = _make_rectangle(vx, vy, vx + col_w, vy + row_h)
            panel_boundaries.append(boundary)

            # Panel face grid (inset by stretchout)
            face = _make_rectangle(
                vx + stretchout, vy + stretchout,
                vx + col_w - stretchout, vy + row_h - stretchout
            )
            panel_face_grids.append(face)

            # Panel face with joint offset (half joint on each side)
            half_j = panel_joint / 2.0
            face_j = _make_rectangle(
                vx + half_j, vy + half_j,
                vx + col_w - half_j, vy + row_h - half_j
            )
            panel_face_grids_with_joint.append(face_j)

            # Panel name: column letter + row number (A1, B1, A2, ...)
            col_letter = chr(65 + c)  # A, B, C, ...
            row_num = str(r + 1)
            panel_names.append("{}{}".format(col_letter, row_num))

            panel_origins.append(rg.Point3d(vx, vy, 0))
            panel_vectors.append(vec)

    # ── Column/Row dimensions ─────────────────────────────────────
    col_widths = [col_w] * qty_cols
    row_heights = [row_h] * qty_rows

    # Joint values: half-joint at edges, full joint between panels
    col_joints = []
    for i in range(qty_cols + 1):
        if i == 0 or i == qty_cols:
            col_joints.append(panel_joint / 2.0)
        else:
            col_joints.append(panel_joint)

    row_joints = []
    for i in range(qty_rows + 1):
        if i == 0 or i == qty_rows:
            row_joints.append(panel_joint / 2.0)
        else:
            row_joints.append(panel_joint)

    # ── Perforation point grid (per panel) ────────────────────────
    # Rectangular grid: origin at panel face corner,
    # Size X = true_col_spacing, Size Y = true_row_spacing
    # Extent X = qty_pt_cols, Extent Y = qty_pt_rows
    pt_grid_planes = []  # nested: [panel][point] = Plane
    pt_grid_origins = []  # flat list of all points

    for panel_idx in range(len(panel_face_grids)):
        r = panel_idx // qty_cols
        c = panel_idx % qty_cols

        # Panel face origin (bottom-left of face)
        fx0 = c * col_w + stretchout
        fy0 = r * row_h + stretchout

        panel_pts = []
        for iy in range(qty_pt_rows + 1):
            for ix in range(qty_pt_cols + 1):
                px = fx0 + ix * true_col_sp
                py = fy0 + iy * true_row_sp
                pt = rg.Point3d(px, py, 0)
                plane = rg.Plane(pt, rg.Vector3d.ZAxis)
                panel_pts.append(plane)
                pt_grid_origins.append(pt)

        pt_grid_planes.append(panel_pts)

    # ── Overall boundary ──────────────────────────────────────────
    overall_w = qty_cols * col_w
    overall_h = qty_rows * row_h
    overall_boundary = _make_rectangle(0, 0, overall_w, overall_h)

    return {
        "panel_boundaries": panel_boundaries,
        "panel_face_grids": panel_face_grids,
        "panel_face_grids_with_joint": panel_face_grids_with_joint,
        "panel_names": panel_names,
        "panel_origins": panel_origins,
        "panel_vectors": panel_vectors,
        "col_widths": col_widths,
        "row_heights": row_heights,
        "col_joints": col_joints,
        "row_joints": row_joints,
        "pt_grid_planes": pt_grid_planes,
        "pt_grid_origins": pt_grid_origins,
        "overall_boundary": overall_boundary,
    }
