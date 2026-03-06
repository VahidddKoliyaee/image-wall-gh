"""
Module 12: Brake Legs
======================
Adds brake/bend leg geometry with accurate per-side depths.
Handles cross-seam flat conditions and corner notching.

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

    Leg depths vary by side based on vertical/horizontal orientation:
    - Vertical: primary (top/bot), secondary (left/right)
    - Horizontal: primary (left/right), secondary (top/bot)

    Cross-seam flat: when a panel shares a horizontal seam with another panel,
    the leg at that edge is omitted (flat edge for seaming).
    """
    stretchout = unfold["stretchout"]
    leg_t = unfold["leg_top"]
    leg_b = unfold["leg_bottom"]
    leg_l = unfold["leg_left"]
    leg_r = unfold["leg_right"]

    panel_faces = grid["panel_face_grids"]
    panel_row_col = faces["panel_row_col"]
    cross_seam_flat = grid_params["cross_seam_flat"]
    qty_rows = config["qty_rows"]
    qty_cols = config["qty_columns"]
    is_flat = grid_params["is_flat"]

    result_leg_left = []
    result_leg_right = []
    result_leg_top = []
    result_leg_bottom = []
    notch_corners = []
    cross_seam_flat_edges = []

    if is_flat or (leg_t <= 0 and leg_b <= 0 and leg_l <= 0 and leg_r <= 0):
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

        # ── Determine actual leg depths per edge ──────────────────
        # Cross seam flat: omit leg at shared row boundaries
        actual_top = leg_t
        actual_bot = leg_b
        actual_left = leg_l
        actual_right = leg_r

        if cross_seam_flat:
            # Top edge: if there's a panel above (not top row), flatten
            if r < qty_rows - 1:
                actual_top = 0.0
            # Bottom edge: if there's a panel below (not bottom row), flatten
            if r > 0:
                actual_bot = 0.0

        # ── Left leg ─────────────────────────────────────────────
        if actual_left > 0:
            left = _make_rectangle(
                fx0 - actual_left - stretchout, fy0,
                fx0, fy1)
        else:
            left = None
        result_leg_left.append(left)

        # ── Right leg ────────────────────────────────────────────
        if actual_right > 0:
            right = _make_rectangle(
                fx1, fy0,
                fx1 + actual_right + stretchout, fy1)
        else:
            right = None
        result_leg_right.append(right)

        # ── Bottom leg ───────────────────────────────────────────
        if actual_bot > 0:
            bot = _make_rectangle(
                fx0, fy0 - actual_bot - stretchout,
                fx1, fy0)
        else:
            bot = None
        result_leg_bottom.append(bot)

        # ── Top leg ──────────────────────────────────────────────
        if actual_top > 0:
            top = _make_rectangle(
                fx0, fy1,
                fx1, fy1 + actual_top + stretchout)
        else:
            top = None
        result_leg_top.append(top)

        # ── Corner notches ───────────────────────────────────────
        # Notches are only at corners where two legs meet
        notches = []

        # Bottom-left
        nw_bl = (actual_left + stretchout) if actual_left > 0 else 0
        nh_bl = (actual_bot + stretchout) if actual_bot > 0 else 0
        if nw_bl > 0 and nh_bl > 0:
            notches.append(_make_rectangle(fx0 - nw_bl, fy0 - nh_bl, fx0, fy0))

        # Bottom-right
        nw_br = (actual_right + stretchout) if actual_right > 0 else 0
        nh_br = (actual_bot + stretchout) if actual_bot > 0 else 0
        if nw_br > 0 and nh_br > 0:
            notches.append(_make_rectangle(fx1, fy0 - nh_br, fx1 + nw_br, fy0))

        # Top-right
        nw_tr = (actual_right + stretchout) if actual_right > 0 else 0
        nh_tr = (actual_top + stretchout) if actual_top > 0 else 0
        if nw_tr > 0 and nh_tr > 0:
            notches.append(_make_rectangle(fx1, fy1, fx1 + nw_tr, fy1 + nh_tr))

        # Top-left
        nw_tl = (actual_left + stretchout) if actual_left > 0 else 0
        nh_tl = (actual_top + stretchout) if actual_top > 0 else 0
        if nw_tl > 0 and nh_tl > 0:
            notches.append(_make_rectangle(fx0 - nw_tl, fy1, fx0, fy1 + nh_tl))

        notch_corners.append(notches)

        # ── Cross seam flat edges ────────────────────────────────
        if cross_seam_flat:
            if r > 0 and actual_bot == 0:
                cross_seam_flat_edges.append(
                    rg.LineCurve(rg.Point3d(fx0, fy0, 0), rg.Point3d(fx1, fy0, 0)))
            if r < qty_rows - 1 and actual_top == 0:
                cross_seam_flat_edges.append(
                    rg.LineCurve(rg.Point3d(fx0, fy1, 0), rg.Point3d(fx1, fy1, 0)))

    return {
        "leg_left": result_leg_left,
        "leg_right": result_leg_right,
        "leg_top": result_leg_top,
        "leg_bottom": result_leg_bottom,
        "notch_corners": notch_corners,
        "cross_seam_flat_edges": cross_seam_flat_edges,
    }