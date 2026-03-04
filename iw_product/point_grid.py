"""
Module 07: Point Grid
======================
Generates the primary perforation point grid from panel face geometry.
Handles staggered patterns, grid-to-panel mapping, and point filtering.

Replaces: "Pert Pt Grid" group — the Rectangular grid component,
Box Corners → XY Plane chain, and Merge/Clean/Dispatch logic.

This module runs inside GH/Rhino.

Usage:
    from iw_product.point_grid import build_point_grid
    pg = build_point_grid(config, grid_params, grid, diag_result)
"""

import Rhino.Geometry as rg


def _point_in_curve(pt, curve, tolerance=0.001):
    """Check if a point is inside a closed curve (XY plane)."""
    result = curve.Contains(rg.Point3d(pt.X, pt.Y, 0), rg.Plane.WorldXY, tolerance)
    return result == rg.PointContainment.Inside


def build_point_grid(config, grid_params, grid, diag_result=None):
    """
    Build the perforation point grid for all panels.

    Points are generated on a rectangular grid within each panel face,
    then optionally filtered by the panel face curve boundary.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform_grid or nonuniform_grid
        diag_result: dict from diagonal_grid (optional, for diagonal patterns)

    Returns:
        dict with:
            perf_points       - list of Point3d for all perforation centers
            perf_planes       - list of Plane at each perf point
            perf_panel_index  - list of int: which panel each point belongs to
            points_per_panel  - nested list: [panel_idx][point_idx] = Point3d
            qty_points_total  - int
    """
    # Use diagonal-adjusted points if available
    if diag_result and diag_result.get("pt_grid_origins"):
        all_origins = diag_result["pt_grid_origins"]
        all_planes_nested = diag_result["pt_grid_planes"]
    else:
        all_origins = grid["pt_grid_origins"]
        all_planes_nested = grid["pt_grid_planes"]

    panel_faces = grid["panel_face_grids"]
    no_perf = config.get("no_perf_level", False)

    if no_perf:
        return {
            "perf_points": [],
            "perf_planes": [],
            "perf_panel_index": [],
            "points_per_panel": [[] for _ in panel_faces],
            "qty_points_total": 0,
        }

    # ── Filter points to be inside panel face curves ──────────────
    perf_points = []
    perf_planes = []
    perf_panel_index = []
    points_per_panel = []

    for panel_idx, face_curve in enumerate(panel_faces):
        panel_pts = []

        if panel_idx < len(all_planes_nested):
            planes = all_planes_nested[panel_idx]
        else:
            planes = []

        for plane in planes:
            pt = plane.Origin
            # Check if point is inside the panel face curve
            if _point_in_curve(pt, face_curve):
                perf_points.append(pt)
                perf_planes.append(plane)
                perf_panel_index.append(panel_idx)
                panel_pts.append(pt)

        points_per_panel.append(panel_pts)

    return {
        "perf_points": perf_points,
        "perf_planes": perf_planes,
        "perf_panel_index": perf_panel_index,
        "points_per_panel": points_per_panel,
        "qty_points_total": len(perf_points),
    }
