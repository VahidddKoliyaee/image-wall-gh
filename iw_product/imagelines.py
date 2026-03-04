"""
Module 09: ImageLines
======================
Handles image-mapped perforation patterns where perforation sizes vary
based on driver curves and image brightness mapping.

Replaces: "ImageLines Master Group" — driver curve interpolation,
spine generation, hit point spacing, rectangle/circle size mapping.

This module runs inside GH/Rhino.

Usage:
    from iw_product.imagelines import build_imagelines
    il = build_imagelines(config, grid_params, grid, point_grid)
"""

import math
import Rhino.Geometry as rg


def _parse_driver_pts(pts_string):
    """Parse '[-38.963,-14.963]#[-14.963,10.581]' into Point3d list."""
    if not pts_string:
        return []
    points = []
    for pt_str in str(pts_string).split("#"):
        pt_str = pt_str.strip().strip("[]")
        if "," in pt_str:
            parts = pt_str.split(",")
            points.append(rg.Point3d(float(parts[0].strip()), float(parts[1].strip()), 0))
    return points


def _build_driver_curve(pts):
    """Build an interpolated curve through driver points."""
    if len(pts) < 2:
        return None
    return rg.Curve.CreateInterpolatedCurve(pts, 3)


def _remap(value, from_min, from_max, to_min, to_max):
    """Remap a value from one range to another."""
    if from_max == from_min:
        return to_min
    t = (value - from_min) / (from_max - from_min)
    t = max(0.0, min(1.0, t))
    return to_min + t * (to_max - to_min)


def build_imagelines(config, grid_params, grid, point_grid):
    """
    Build image-line mapped perforations.

    Driver curves define how perforation sizes vary across the panel.
    Points closer to curve 1 get smaller perfs, closer to curve 2 get larger.

    If grid_pattern is not "Image Lines Grid", returns empty result.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform_grid/nonuniform_grid
        point_grid: dict from point_grid

    Returns:
        dict with:
            is_imagelines     - bool
            hit_diameters     - list of float per perf point
            hit_radii         - list of float per perf point
            imageline_spines  - list of curves (spine lines between driver curves)
            driver_curve_1    - Curve or None
            driver_curve_2    - Curve or None
    """
    if config["grid_pattern"] != "Image Lines Grid":
        return {
            "is_imagelines": False,
            "hit_diameters": [],
            "hit_radii": [],
            "imageline_spines": [],
            "driver_curve_1": None,
            "driver_curve_2": None,
        }

    # Parse driver curves
    pts1 = _parse_driver_pts(config["driver_curve_1_pts"])
    pts2 = _parse_driver_pts(config["driver_curve_2_pts"])
    curve1 = _build_driver_curve(pts1)
    curve2 = _build_driver_curve(pts2)

    if not curve1 or not curve2:
        return {
            "is_imagelines": True,
            "hit_diameters": [],
            "hit_radii": [],
            "imageline_spines": [],
            "driver_curve_1": curve1,
            "driver_curve_2": curve2,
        }

    min_rect = config["min_rectangle"]
    max_rect = config["max_rectangle"]
    min_bridge_along = config["min_bridge_along"]
    min_bridge_perp = config["min_bridge_perp"]
    line_spacing = config["line_spacing_target"]
    perf_points = point_grid["perf_points"]

    # ── Generate spines between driver curves ─────────────────────
    # Spines are lines connecting corresponding points on the two curves
    imageline_spines = []
    num_spines = max(2, int(math.ceil(
        grid_params["panel_face_height"] / line_spacing)) + 1)

    for i in range(num_spines):
        t = i / max(1, num_spines - 1)
        # Get points on each driver curve at parameter t
        pt1 = curve1.PointAtNormalizedLength(t)
        pt2 = curve2.PointAtNormalizedLength(t)
        if pt1 and pt2:
            spine = rg.LineCurve(pt1, pt2)
            imageline_spines.append(spine)

    # ── Map each perf point to a die size based on distance to curves ─
    hit_diameters = []
    hit_radii = []

    for pt in perf_points:
        # Distance from point to each driver curve
        success1, t1 = curve1.ClosestPoint(pt)
        success2, t2 = curve2.ClosestPoint(pt)

        if success1 and success2:
            d1 = pt.DistanceTo(curve1.PointAt(t1))
            d2 = pt.DistanceTo(curve2.PointAt(t2))
            total_d = d1 + d2

            if total_d > 0:
                # Normalized position between curves (0 = curve1, 1 = curve2)
                normalized = d1 / total_d
                # Map to rectangle size
                diameter = _remap(normalized, 0.0, 1.0, min_rect, max_rect)
            else:
                diameter = min_rect
        else:
            diameter = min_rect

        hit_diameters.append(diameter)
        hit_radii.append(diameter / 2.0)

    return {
        "is_imagelines": True,
        "hit_diameters": hit_diameters,
        "hit_radii": hit_radii,
        "imageline_spines": imageline_spines,
        "driver_curve_1": curve1,
        "driver_curve_2": curve2,
    }
