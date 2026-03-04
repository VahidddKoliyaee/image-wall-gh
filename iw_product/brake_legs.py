"""
Module 12: Brake Legs
======================
Adds brake/bend leg geometry to unfolded panels, notches corners
for folding clearance, and handles cross-seam flat conditions.

Replaces: "Cross Seam Flat" + "Notch Legs" groups.

This module runs inside GH/Rhino.

Usage:
    from iw_product.brake_legs import add_brake_legs
    legs = add_brake_legs(config, grid_params, grid, faces, unfold)
"""

import Rhino.Geometry as rg


def _make_rectangle(x0, y0, x1, y1):
    pts = [
        rg.Point3d(x0, y0, 0), rg.Point3d(x1, y0, 0),
        rg.Point3d(x1, y1, 0), rg.Point3d(x0, y1, 0),
        rg.Point3d(x0, y0, 0),
    ]
    return rg.Polyline(pts).ToPolylineCurve()


def add_brake_legs(config, grid_params, grid, faces, unfold):
    """
    Generate brake leg geometry and corner notches.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform/nonuniform grid
        faces: dict from panel_faces
        unfold: dict from panel_unfold

    Returns:
        dict with:
            leg_left      - list of Curve: left brake leg per panel
            leg_right     - list of Curve: right brake leg per panel
            leg_top       - list of Curve: top brake leg per panel
            leg_bottom    - list of Curve: bottom brake leg per panel
            notch_corners - list of list of Curve: corner notch rectangles
            cross_seam_flat_edges - list of Curve: edges with no brake (cross seam)
    """
    brake_depth = unfold["brake_leg_depth"]
    stretchout = unfold["stretchout"]
    panel_faces = grid["panel_face_grids"]
    panel_row_col = faces["panel_row_col"]
    left_is_corner = faces["left_is_corner"]
    right_is_corner = faces["right_is_corner"]
    cross_seam_flat = grid_params["cross_seam_flat"]
    qty_rows = config["qty_rows"]
    is_flat = grid_params["is_flat"]

    leg_left = []
    leg_right = []
    leg_top = []
    leg_bottom = []
    notch_corners = []
    cross_seam_flat_edges = []

    if is_flat or brake_depth <= 0:
        # No brake legs for flat panels
        empty = [None] * len(panel_faces)
        return {
            "leg_left": empty, "leg_right": empty,
            "leg_top": empty, "leg_bottom": empty,
            "notch_corners": [[] for _ in panel_faces],
            "cross_seam_flat_edges": [],
        }

    for idx, face in enumerate(panel_faces):
        bb = face.GetBoundingBox(True)
        fx0 = bb.Min.X
        fy0 = bb.Min.Y
        fx1 = bb.Max.X
        fy1 = bb.Max.Y
        r, c = panel_row_col[idx]

        # Left leg
        left = _make_rectangle(fx0 - brake_depth - stretchout, fy0,
                                fx0, fy1)
        leg_left.append(left)

        # Right leg
        right = _make_rectangle(fx1, fy0,
                                 fx1 + brake_depth + stretchout, fy1)
        leg_right.append(right)

        # Bottom leg
        bot = _make_rectangle(fx0, fy0 - brake_depth - stretchout,
                               fx1, fy0)
        leg_bottom.append(bot)

        # Top leg
        top = _make_rectangle(fx0, fy1,
                               fx1, fy1 + brake_depth + stretchout)
        leg_top.append(top)

        # Corner notches (material removed at 4 corners for folding)
        notch_w = brake_depth + stretchout
        notches = [
            # Bottom-left
            _make_rectangle(fx0 - notch_w, fy0 - notch_w, fx0, fy0),
            # Bottom-right
            _make_rectangle(fx1, fy0 - notch_w, fx1 + notch_w, fy0),
            # Top-right
            _make_rectangle(fx1, fy1, fx1 + notch_w, fy1 + notch_w),
            # Top-left
            _make_rectangle(fx0 - notch_w, fy1, fx0, fy1 + notch_w),
        ]
        notch_corners.append(notches)

        # Cross seam flat: if panel is at a row boundary and cross_seam_flat,
        # the top/bottom legs may be omitted
        if cross_seam_flat:
            if r > 0:
                # Bottom edge is a cross seam
                cross_seam_flat_edges.append(
                    rg.LineCurve(rg.Point3d(fx0, fy0, 0), rg.Point3d(fx1, fy0, 0)))
            if r < qty_rows - 1:
                # Top edge is a cross seam
                cross_seam_flat_edges.append(
                    rg.LineCurve(rg.Point3d(fx0, fy1, 0), rg.Point3d(fx1, fy1, 0)))

    return {
        "leg_left": leg_left,
        "leg_right": leg_right,
        "leg_top": leg_top,
        "leg_bottom": leg_bottom,
        "notch_corners": notch_corners,
        "cross_seam_flat_edges": cross_seam_flat_edges,
    }
