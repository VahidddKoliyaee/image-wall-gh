"""
Module 14: Panel Naming
========================
Generates panel naming/numbering and handles rotation of panels
for horizontal CNC output orientation.

Replaces: "Panel Names" + "Rotate for Horizontal" groups.

This module runs inside GH/Rhino.

Usage:
    from iw_product.panel_naming import name_and_orient_panels
    result = name_and_orient_panels(config, grid_params, grid, unfold)
"""

import Rhino.Geometry as rg


def name_and_orient_panels(config, grid_params, grid, unfold):
    """
    Generate final panel names and rotate panels for CNC if needed.

    Panel naming convention: {SCOPE_NAME}-{COL_LETTER}{ROW_NUMBER}
    e.g. "E1-A1", "E1-B1", "E1-A2"

    If panels are vertical and taller than wide, rotate 90 degrees
    for horizontal CNC orientation.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform/nonuniform grid
        unfold: dict from panel_unfold

    Returns:
        dict with:
            full_panel_names   - list of str: "SCOPE-COL_ROW" names
            short_panel_names  - list of str: "A1", "B2" etc
            rotate_for_cnc     - bool: whether panels should be rotated
            rotation_angle     - float: degrees (0 or -90)
            rotated_curves     - list of Curve: oriented flat panels
            name_planes        - list of Plane: text placement positions
    """
    scope_name = config["scope_name"]
    product_number = config["product_number"]
    vertical = grid_params["vertical"]
    panel_names = grid["panel_names"]
    unfold_curves = unfold["unfold_curves"]
    unfold_dims = unfold["unfold_dims"]

    # ── Full panel names ──────────────────────────────────────────
    full_panel_names = []
    for name in panel_names:
        full_name = "{}-{}".format(scope_name, name)
        full_panel_names.append(full_name)

    # ── Rotation for CNC ──────────────────────────────────────────
    # If vertical orientation and panel is taller than wide, rotate -90
    # so the long dimension runs horizontally on the CNC bed
    rotate_for_cnc = False
    rotation_angle = 0.0

    if unfold_dims:
        w, h = unfold_dims[0]
        if vertical and h > w:
            rotate_for_cnc = True
            rotation_angle = -90.0

    rotated_curves = []
    name_planes = []

    for idx, curve in enumerate(unfold_curves):
        if rotate_for_cnc:
            bb = curve.GetBoundingBox(True)
            center = rg.Point3d(
                (bb.Min.X + bb.Max.X) / 2.0,
                (bb.Min.Y + bb.Max.Y) / 2.0, 0)

            import math
            xform = rg.Transform.Rotation(
                math.radians(rotation_angle), rg.Vector3d.ZAxis, center)
            rotated = curve.DuplicateCurve()
            rotated.Transform(xform)
            rotated_curves.append(rotated)

            # Name plane at center of rotated panel
            rbb = rotated.GetBoundingBox(True)
            name_pt = rg.Point3d(
                (rbb.Min.X + rbb.Max.X) / 2.0,
                (rbb.Min.Y + rbb.Max.Y) / 2.0, 0)
            name_planes.append(rg.Plane(name_pt, rg.Vector3d.ZAxis))
        else:
            rotated_curves.append(curve)

            bb = curve.GetBoundingBox(True)
            name_pt = rg.Point3d(
                (bb.Min.X + bb.Max.X) / 2.0,
                (bb.Min.Y + bb.Max.Y) / 2.0, 0)
            name_planes.append(rg.Plane(name_pt, rg.Vector3d.ZAxis))

    return {
        "full_panel_names": full_panel_names,
        "short_panel_names": panel_names,
        "rotate_for_cnc": rotate_for_cnc,
        "rotation_angle": rotation_angle,
        "rotated_curves": rotated_curves,
        "name_planes": name_planes,
    }
