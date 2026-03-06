"""
Module 09: ImageLines
======================
Handles image-mapped perforation patterns where perforation sizes vary
based on image brightness at each point location.

Supports driver curves AND direct image brightness mapping.

Usage:
    from iw_product.imagelines import build_imagelines
    il = build_imagelines(config, grid_params, grid, point_grid, image_data)
"""

import math

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def _parse_driver_pts(pts_string):
    if not pts_string:
        return []
    points = []
    for pt_str in str(pts_string).split("#"):
        pt_str = pt_str.strip().strip("[]")
        if "," in pt_str:
            parts = pt_str.split(",")
            if HAS_RHINO:
                points.append(rg.Point3d(float(parts[0].strip()), float(parts[1].strip()), 0))
            else:
                points.append((float(parts[0].strip()), float(parts[1].strip())))
    return points


def _build_driver_curve(pts):
    if not HAS_RHINO or len(pts) < 2:
        return None
    return rg.Curve.CreateInterpolatedCurve(pts, 3)


def build_imagelines(config, grid_params, grid, point_grid, image_data=None):
    """
    Build image-line mapped perforations.

    If image_data is provided and image is loaded, brightness at each point
    is sampled and mapped to die sizes.

    If driver curves are defined, they modulate the mapping region.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from grid
        point_grid: dict from point_grid
        image_data: dict from image_processor.process_image() (optional)

    Returns:
        dict with:
            is_imagelines     - bool
            hit_diameters     - list of float per perf point
            hit_radii         - list of float per perf point
            imageline_spines  - list of curves
            driver_curve_1    - Curve or None
            driver_curve_2    - Curve or None
    """
    is_imagelines = config["grid_pattern"] == "Image Lines Grid"

    if not is_imagelines:
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

    min_rect = config["min_rectangle"]
    max_rect = config["max_rectangle"]
    line_spacing = config["line_spacing_target"]
    perf_points = point_grid["perf_points"]
    imagelines_die_list = config.get("imagelines_die_list", [])
    punch_maximizer = config.get("punch_use_maximizer", False)

    # ── Generate spines ───────────────────────────────────────────
    imageline_spines = []
    if HAS_RHINO and curve1 and curve2:
        num_spines = max(2, int(math.ceil(
            grid_params["panel_face_height"] / line_spacing)) + 1)
        for i in range(num_spines):
            t = i / max(1, num_spines - 1)
            pt1 = curve1.PointAtNormalizedLength(t)
            pt2 = curve2.PointAtNormalizedLength(t)
            if pt1 and pt2:
                imageline_spines.append(rg.LineCurve(pt1, pt2))

    # ── Map brightness to die sizes ───────────────────────────────
    hit_diameters = []
    hit_radii = []

    if image_data and image_data.get("is_loaded"):
        # Use image brightness mapping
        from iw_product.image_processor import sample_brightness, brightness_to_die_size

        # Get panel bounding box for coordinate mapping
        overall = grid.get("overall_boundary")
        if overall and HAS_RHINO:
            bb = overall.GetBoundingBox(True)
            panel_bbox = (bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y)
        else:
            w = grid_params["overall_width"]
            h = grid_params["overall_height"]
            panel_bbox = (0, 0, w, h)

        brightness = sample_brightness(image_data, perf_points, panel_bbox, config)

        # Snap to available dies if punch_maximizer is on
        snap_dies = imagelines_die_list if punch_maximizer else None
        hit_diameters = brightness_to_die_size(brightness, min_rect, max_rect, snap_dies)
        hit_radii = [d / 2.0 for d in hit_diameters]

    elif HAS_RHINO and curve1 and curve2:
        # Fallback: use distance-to-curves mapping
        for pt in perf_points:
            success1, t1 = curve1.ClosestPoint(pt)
            success2, t2 = curve2.ClosestPoint(pt)
            if success1 and success2:
                d1 = pt.DistanceTo(curve1.PointAt(t1))
                d2 = pt.DistanceTo(curve2.PointAt(t2))
                total_d = d1 + d2
                if total_d > 0:
                    normalized = d1 / total_d
                    diameter = min_rect + normalized * (max_rect - min_rect)
                else:
                    diameter = min_rect
            else:
                diameter = min_rect
            hit_diameters.append(diameter)
            hit_radii.append(diameter / 2.0)
    else:
        # No image, no curves — uniform
        hit_diameters = [min_rect] * len(perf_points)
        hit_radii = [min_rect / 2.0] * len(perf_points)

    return {
        "is_imagelines": True,
        "hit_diameters": hit_diameters,
        "hit_radii": hit_radii,
        "imageline_spines": imageline_spines,
        "driver_curve_1": curve1,
        "driver_curve_2": curve2,
    }