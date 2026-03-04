"""
Module 04: Nonuniform Grid
============================
Generates a panel grid with variable column widths and row heights,
read from the IW-NonUniformGrid Excel sheet.

Replaces: "Panel Faces [Non Uniform]" + "Nonuniform Panel Grid" groups.

This module produces Rhino geometry objects and must run inside GH/Rhino.

Usage:
    from iw_product.nonuniform_grid import build_nonuniform_grid
    grid = build_nonuniform_grid(config, grid_params)
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


def parse_nonuniform_data(raw_grid):
    """
    Parse the IW-NonUniformGrid sheet data into column widths and row heights.

    The sheet format varies, but typically:
    - Row 0: header
    - Subsequent rows: column widths per scope/row

    Args:
        raw_grid: list of lists from Excel sheet

    Returns:
        (col_widths_per_row, row_heights) or None if no data
    """
    if not raw_grid:
        return None

    # Try to extract numeric values
    col_widths = []
    row_heights = []

    for row in raw_grid:
        row_vals = []
        for cell in row:
            if cell is not None:
                try:
                    row_vals.append(float(cell))
                except (ValueError, TypeError):
                    pass
        if row_vals:
            col_widths.append(row_vals)

    if not col_widths:
        return None

    return col_widths


def build_nonuniform_grid(config, grid_params):
    """
    Build a nonuniform panel grid with variable widths/heights.

    If nonuniform data is not available, falls back to uniform grid logic
    with the standard config dimensions.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params

    Returns:
        dict with same keys as uniform_grid.build_uniform_grid()
    """
    nonuniform_data = config.get("nonuniform_grid")
    stretchout = grid_params["stretchout_one_side"]
    panel_joint = grid_params["panel_joint"]

    if nonuniform_data:
        parsed = parse_nonuniform_data(nonuniform_data)
    else:
        parsed = None

    # If no nonuniform data, build from config col/row lists
    if parsed:
        # Nonuniform: each row in parsed is a list of column widths
        # Row heights derived from the data or from config
        all_col_widths = parsed  # list of lists
        qty_rows = len(all_col_widths)
        row_heights = [config["panel_row_height"]] * qty_rows
    else:
        # Uniform fallback
        qty_cols = config["qty_columns"]
        qty_rows = config["qty_rows"]
        col_w = config["panel_col_width"]
        row_h = config["panel_row_height"]
        all_col_widths = [[col_w] * qty_cols for _ in range(qty_rows)]
        row_heights = [row_h] * qty_rows

    # ── Build geometry ────────────────────────────────────────────
    panel_boundaries = []
    panel_face_grids = []
    panel_face_grids_with_joint = []
    panel_names = []
    panel_origins = []
    panel_vectors = []
    col_widths_flat = []
    col_joints = []
    row_joints = []
    pt_grid_planes = []
    pt_grid_origins = []

    y_cursor = 0.0
    panel_idx = 0

    for r, (row_cols, row_h) in enumerate(zip(all_col_widths, row_heights)):
        x_cursor = 0.0

        for c, col_w in enumerate(row_cols):
            vx = x_cursor
            vy = y_cursor
            vec = rg.Vector3d(vx, vy, 0)

            # Panel boundary
            boundary = _make_rectangle(vx, vy, vx + col_w, vy + row_h)
            panel_boundaries.append(boundary)

            # Panel face (inset)
            face = _make_rectangle(
                vx + stretchout, vy + stretchout,
                vx + col_w - stretchout, vy + row_h - stretchout
            )
            panel_face_grids.append(face)

            # Face with joint
            half_j = panel_joint / 2.0
            face_j = _make_rectangle(
                vx + half_j, vy + half_j,
                vx + col_w - half_j, vy + row_h - half_j
            )
            panel_face_grids_with_joint.append(face_j)

            # Name
            col_letter = chr(65 + c) if c < 26 else "{}{}".format(
                chr(64 + c // 26), chr(65 + c % 26))
            panel_names.append("{}{}".format(col_letter, r + 1))

            panel_origins.append(rg.Point3d(vx, vy, 0))
            panel_vectors.append(vec)

            # Point grid for this panel
            face_w = col_w - 2 * stretchout
            face_h = row_h - 2 * stretchout
            spacing = config["perf_spacing"]

            if spacing > 0 and face_w > 0 and face_h > 0:
                nx = max(1, round(face_w / spacing))
                ny = max(1, round(face_h / spacing))
                sx = face_w / nx
                sy = face_h / ny
            else:
                nx, ny, sx, sy = 1, 1, face_w, face_h

            panel_pts = []
            for iy in range(ny + 1):
                for ix in range(nx + 1):
                    px = vx + stretchout + ix * sx
                    py = vy + stretchout + iy * sy
                    pt = rg.Point3d(px, py, 0)
                    plane = rg.Plane(pt, rg.Vector3d.ZAxis)
                    panel_pts.append(plane)
                    pt_grid_origins.append(pt)
            pt_grid_planes.append(panel_pts)

            if r == 0:
                col_widths_flat.append(col_w)

            x_cursor += col_w
            panel_idx += 1

        y_cursor += row_h

    # Overall boundary
    total_w = max(sum(row) for row in all_col_widths)
    total_h = sum(row_heights)
    overall_boundary = _make_rectangle(0, 0, total_w, total_h)

    # Joints
    qty_cols_max = max(len(row) for row in all_col_widths)
    for i in range(qty_cols_max + 1):
        col_joints.append(panel_joint / 2.0 if (i == 0 or i == qty_cols_max) else panel_joint)
    for i in range(len(row_heights) + 1):
        row_joints.append(panel_joint / 2.0 if (i == 0 or i == len(row_heights)) else panel_joint)

    return {
        "panel_boundaries": panel_boundaries,
        "panel_face_grids": panel_face_grids,
        "panel_face_grids_with_joint": panel_face_grids_with_joint,
        "panel_names": panel_names,
        "panel_origins": panel_origins,
        "panel_vectors": panel_vectors,
        "col_widths": col_widths_flat,
        "row_heights": row_heights,
        "col_joints": col_joints,
        "row_joints": row_joints,
        "pt_grid_planes": pt_grid_planes,
        "pt_grid_origins": pt_grid_origins,
        "overall_boundary": overall_boundary,
    }
