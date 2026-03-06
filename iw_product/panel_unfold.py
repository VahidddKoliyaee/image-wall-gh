"""
Module 11: Panel Unfold
========================
Unfolds panel geometry to flat patterns for CNC fabrication.
Uses accurate brake leg depths per style from the GH definition.

Usage:
    from iw_product.panel_unfold import unfold_panels
    unfold = unfold_panels(config, grid_params, grid, faces)
"""

import Rhino.Geometry as rg


def _make_rectangle(x0, y0, x1, y1):
    pts = [
        rg.Point3d(x0, y0, 0), rg.Point3d(x1, y0, 0),
        rg.Point3d(x1, y1, 0), rg.Point3d(x0, y1, 0),
        rg.Point3d(x0, y0, 0),
    ]
    return rg.Polyline(pts).ToPolylineCurve()


def unfold_panels(config, grid_params, grid, faces):
    """
    Create flat (unfolded) panel blanks for fabrication.

    Brake leg depths (from GH "Brake Leg Depths" panels):
        Double Return Long Span:  primary=6.0,  secondary=2.0
        Double Return Short Span: primary=4.0,  secondary=1.5
        Droplock Hat Channel:     primary=2.75, secondary=0.0
        Droplock Mullion:         primary=2.75, secondary=0.0
        Flat:                     primary=0.0,  secondary=0.0

    For vertical styles, primary leg = top/bottom, secondary = left/right.
    For horizontal styles, primary leg = left/right, secondary = top/bottom.
    """
    stretchout = grid_params["stretchout_one_side"]
    vertical = grid_params["vertical"]
    is_flat = grid_params["is_flat"]
    primary_depth = grid_params["effective_primary_leg"]
    secondary_depth = grid_params["effective_secondary_leg"]

    panel_faces_list = grid["panel_face_grids"]
    panel_names = grid["panel_names"]

    # For vertical panels: primary = top/bottom (span direction), secondary = left/right
    # For horizontal panels: primary = left/right (span direction), secondary = top/bottom
    if vertical:
        leg_top = primary_depth
        leg_bottom = primary_depth
        leg_left = secondary_depth
        leg_right = secondary_depth
    else:
        leg_left = primary_depth
        leg_right = primary_depth
        leg_top = secondary_depth
        leg_bottom = secondary_depth

    unfold_curves = []
    unfold_dims = []

    for idx, face in enumerate(panel_faces_list):
        bb = face.GetBoundingBox(True)
        face_w = bb.Max.X - bb.Min.X
        face_h = bb.Max.Y - bb.Min.Y

        if is_flat:
            flat_w = face_w
            flat_h = face_h
            ox = bb.Min.X
            oy = bb.Min.Y
        else:
            # Flat blank = face + legs + stretchout on each side
            ext_left = leg_left + stretchout
            ext_right = leg_right + stretchout
            ext_bottom = leg_bottom + stretchout
            ext_top = leg_top + stretchout

            flat_w = face_w + ext_left + ext_right
            flat_h = face_h + ext_bottom + ext_top

            ox = bb.Min.X - ext_left
            oy = bb.Min.Y - ext_bottom

        unfold = _make_rectangle(ox, oy, ox + flat_w, oy + flat_h)
        unfold_curves.append(unfold)
        unfold_dims.append((flat_w, flat_h))

    return {
        "unfold_curves": unfold_curves,
        "unfold_dims": unfold_dims,
        "primary_leg_depth": primary_depth,
        "secondary_leg_depth": secondary_depth,
        "leg_top": leg_top,
        "leg_bottom": leg_bottom,
        "leg_left": leg_left,
        "leg_right": leg_right,
        "brake_leg_depth": primary_depth,  # backward compat
        "stretchout": stretchout,
        "panel_names": panel_names,
    }