"""
Module 11: Panel Unfold
========================
Unfolds panel geometry to flat patterns for CNC fabrication.
Adds stretchout (bend allowance) to create the full flat blank.

Replaces: "Panel Unfold" group.

This module runs inside GH/Rhino.

Usage:
    from iw_product.panel_unfold import unfold_panels
    unfold = unfold_panels(config, grid_params, grid, faces)
"""

import Rhino.Geometry as rg


def _make_rectangle(x0, y0, x1, y1):
    """Create a rectangle polyline curve."""
    pts = [
        rg.Point3d(x0, y0, 0),
        rg.Point3d(x1, y0, 0),
        rg.Point3d(x1, y1, 0),
        rg.Point3d(x0, y1, 0),
        rg.Point3d(x0, y0, 0),
    ]
    return rg.Polyline(pts).ToPolylineCurve()


def unfold_panels(config, grid_params, grid, faces):
    """
    Create flat (unfolded) panel blanks for fabrication.

    For double-return styles, the flat blank includes:
    - Panel face (center)
    - Brake legs on all 4 sides
    - Stretchout allowance at each bend

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform/nonuniform grid
        faces: dict from panel_faces

    Returns:
        dict with:
            unfold_curves     - list of Curve: flat panel outlines
            unfold_dims       - list of (width, height): flat blank dimensions
            brake_leg_depth   - float: depth of brake legs
            stretchout        - float: bend allowance per side
            panel_names       - list of str (same as grid)
    """
    style_idx = grid_params["style_index"]
    stretchout = grid_params["stretchout_one_side"]
    material_t = config["material_thickness"]
    vertical = grid_params["vertical"]
    is_double_return = grid_params["is_double_return"]
    is_flat = grid_params["is_flat"]

    # Brake leg depth depends on style
    # Double Return: standard brake depth (typically 1.0" - 2.0")
    # Droplock: different leg profile
    # Flat: no legs
    if is_double_return:
        brake_leg_depth = 1.0  # standard; can be overridden by config
    elif grid_params["is_droplock"]:
        brake_leg_depth = 0.75
    else:
        brake_leg_depth = 0.0

    panel_faces_list = grid["panel_face_grids"]
    panel_names = grid["panel_names"]

    unfold_curves = []
    unfold_dims = []

    for idx, face in enumerate(panel_faces_list):
        bb = face.GetBoundingBox(True)
        face_w = bb.Max.X - bb.Min.X
        face_h = bb.Max.Y - bb.Min.Y

        if is_flat:
            # Flat panels: unfold = face size (no legs)
            flat_w = face_w
            flat_h = face_h
        else:
            # Add brake legs + stretchout on all 4 sides
            flat_w = face_w + 2 * (brake_leg_depth + stretchout)
            flat_h = face_h + 2 * (brake_leg_depth + stretchout)

        # Create flat blank at origin (will be positioned later)
        origin_x = bb.Min.X - brake_leg_depth - stretchout if not is_flat else bb.Min.X
        origin_y = bb.Min.Y - brake_leg_depth - stretchout if not is_flat else bb.Min.Y

        unfold = _make_rectangle(origin_x, origin_y,
                                  origin_x + flat_w, origin_y + flat_h)
        unfold_curves.append(unfold)
        unfold_dims.append((flat_w, flat_h))

    return {
        "unfold_curves": unfold_curves,
        "unfold_dims": unfold_dims,
        "brake_leg_depth": brake_leg_depth,
        "stretchout": stretchout,
        "panel_names": panel_names,
    }
