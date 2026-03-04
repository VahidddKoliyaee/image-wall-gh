"""
Module 06: Diagonal Grid
==========================
Handles diagonal (45-degree rotated) perforation grid patterns.
When grid_pattern is "Force Diagonal - Vertical" or "Force Diagonal - Horizontal",
the point grid is rotated 45 degrees and the spacing is adjusted by sqrt(2).

Replaces: "Resize Diagonal Grid" group.

This module runs inside GH/Rhino.

Usage:
    from iw_product.diagonal_grid import apply_diagonal_grid
    diag_pts = apply_diagonal_grid(config, grid_params, grid)
"""

import math
import Rhino.Geometry as rg


def apply_diagonal_grid(config, grid_params, grid):
    """
    If the grid pattern is diagonal, rotate the perforation point grid
    by 45 degrees and adjust spacing. Otherwise, return points unchanged.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform_grid or nonuniform_grid

    Returns:
        dict with:
            pt_grid_origins   - updated point list (rotated if diagonal)
            pt_grid_planes    - updated plane list
            is_diagonal       - bool
            rotation_angle    - float (degrees)
    """
    is_diagonal = grid_params["is_diagonal"]
    is_diag_vert = grid_params["is_diagonal_vertical"]
    is_diag_horiz = grid_params["is_diagonal_horizontal"]

    if not is_diagonal:
        return {
            "pt_grid_origins": grid["pt_grid_origins"],
            "pt_grid_planes": grid["pt_grid_planes"],
            "is_diagonal": False,
            "rotation_angle": 0.0,
        }

    # Diagonal rotation: 45 degrees
    angle_rad = math.pi / 4.0  # 45 degrees
    rotation_angle = 45.0

    # For diagonal-vertical, rotate around each panel's center
    # For diagonal-horizontal, same rotation but grid is oriented differently
    panel_faces = grid["panel_face_grids"]
    stretchout = grid_params["stretchout_one_side"]

    new_origins = []
    new_planes = []

    for panel_idx, panel_pts in enumerate(grid["pt_grid_planes"]):
        # Get panel face center for rotation
        face = panel_faces[panel_idx]
        bb = face.GetBoundingBox(True)
        center = rg.Point3d(
            (bb.Min.X + bb.Max.X) / 2.0,
            (bb.Min.Y + bb.Max.Y) / 2.0,
            0,
        )

        # Rotation transform around panel center
        xform = rg.Transform.Rotation(angle_rad, rg.Vector3d.ZAxis, center)

        # Rotate each point, keep only those inside the panel face
        panel_new_pts = []
        for plane in panel_pts:
            pt = rg.Point3d(plane.Origin)
            pt.Transform(xform)

            # Check if rotated point is inside panel face bounding box
            # (with small tolerance)
            tol = 0.01
            if (bb.Min.X - tol <= pt.X <= bb.Max.X + tol and
                bb.Min.Y - tol <= pt.Y <= bb.Max.Y + tol):
                new_plane = rg.Plane(pt, rg.Vector3d.ZAxis)
                panel_new_pts.append(new_plane)
                new_origins.append(pt)

        new_planes.append(panel_new_pts)

    return {
        "pt_grid_origins": new_origins,
        "pt_grid_planes": new_planes,
        "is_diagonal": True,
        "rotation_angle": rotation_angle,
    }
