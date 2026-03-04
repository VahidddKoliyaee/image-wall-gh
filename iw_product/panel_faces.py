"""
Module 05: Panel Faces
========================
Higher-level panel face logic: selects between uniform/nonuniform grids,
computes cross-seam data, corner conditions, and panel face properties.

Replaces: "Panel Faces [Uniform]" / "Panel Faces [Non Uniform]" routing,
cross-seam computations, corner index detection.

This module runs inside GH/Rhino.

Usage:
    from iw_product.panel_faces import build_panel_faces
    faces = build_panel_faces(config, grid_params, grid)
"""

import Rhino.Geometry as rg


def _bbox_dimensions(curve):
    """Get width and height of a curve's bounding box."""
    bb = curve.GetBoundingBox(True)
    w = bb.Max.X - bb.Min.X
    h = bb.Max.Y - bb.Min.Y
    return w, h


def build_panel_faces(config, grid_params, grid):
    """
    Compute panel face properties, cross-seam data, and corner conditions.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform_grid or nonuniform_grid

    Returns:
        dict with:
            panel_face_widths   - list of face widths per panel
            panel_face_heights  - list of face heights per panel
            panel_areas         - list of face areas (sq in)
            total_area_sqft     - total face area in sq ft
            cross_seam_indices  - list of row indices where cross seam occurs
            cross_seam_hits     - bool per panel: True if panel is at a cross seam
            corner_indices      - list of (row, col) tuples for corner panels
            left_is_corner      - bool per panel
            right_is_corner     - bool per panel
            panel_row_col       - list of (row, col) tuples per panel
            connection_points   - list of Point3d for connection/fastener locations
    """
    qty_cols = config["qty_columns"]
    qty_rows = config["qty_rows"]
    panel_faces = grid["panel_face_grids"]
    panel_names = grid["panel_names"]
    col_widths = grid["col_widths"]
    row_heights = grid["row_heights"]
    cross_seam_style = config["cross_seam"]
    vertical = grid_params["vertical"]

    # ── Face dimensions ───────────────────────────────────────────
    panel_face_widths = []
    panel_face_heights = []
    panel_areas = []

    for face in panel_faces:
        w, h = _bbox_dimensions(face)
        panel_face_widths.append(w)
        panel_face_heights.append(h)
        panel_areas.append(w * h)

    total_area_sqft = sum(panel_areas) / 144.0  # sq in → sq ft

    # ── Panel row/col mapping ─────────────────────────────────────
    panel_row_col = []
    for idx in range(len(panel_faces)):
        r = idx // qty_cols
        c = idx % qty_cols
        panel_row_col.append((r, c))

    # ── Cross seam ────────────────────────────────────────────────
    # Cross seams occur between rows (horizontal joints)
    # "Default" = all rows have cross seams
    # Cross seam indices = row boundaries: 1, 2, ..., qty_rows-1
    cross_seam_indices = list(range(1, qty_rows))

    cross_seam_hits = []
    for r, c in panel_row_col:
        # A panel is at a cross seam if it's at the top or bottom of a row boundary
        at_seam = (r > 0) or (r < qty_rows - 1 and qty_rows > 1)
        cross_seam_hits.append(at_seam)

    # ── Corner detection ──────────────────────────────────────────
    corner_indices = []
    left_is_corner = []
    right_is_corner = []

    for r, c in panel_row_col:
        is_left = (c == 0)
        is_right = (c == qty_cols - 1)
        left_is_corner.append(is_left)
        right_is_corner.append(is_right)
        if is_left or is_right:
            corner_indices.append((r, c))

    # ── Connection points ─────────────────────────────────────────
    # Connection points are at panel edges where fasteners attach
    # Typically at corners and along top/bottom edges
    connection_points = []
    stretchout = grid_params["stretchout_one_side"]

    for idx, (r, c) in enumerate(panel_row_col):
        ox = grid["panel_origins"][idx].X
        oy = grid["panel_origins"][idx].Y
        w = col_widths[c] if c < len(col_widths) else config["panel_col_width"]
        h = row_heights[r] if r < len(row_heights) else config["panel_row_height"]

        # 4 corners of panel (at stretchout inset)
        pts = [
            rg.Point3d(ox + stretchout, oy + stretchout, 0),
            rg.Point3d(ox + w - stretchout, oy + stretchout, 0),
            rg.Point3d(ox + w - stretchout, oy + h - stretchout, 0),
            rg.Point3d(ox + stretchout, oy + h - stretchout, 0),
        ]
        connection_points.extend(pts)

    return {
        "panel_face_widths": panel_face_widths,
        "panel_face_heights": panel_face_heights,
        "panel_areas": panel_areas,
        "total_area_sqft": total_area_sqft,
        "cross_seam_indices": cross_seam_indices,
        "cross_seam_hits": cross_seam_hits,
        "corner_indices": corner_indices,
        "left_is_corner": left_is_corner,
        "right_is_corner": right_is_corner,
        "panel_row_col": panel_row_col,
        "connection_points": connection_points,
    }
