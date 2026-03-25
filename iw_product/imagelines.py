"""
Module 09: ImageLines
======================
Handles image-mapped perforation patterns.
Now uses exact C# GrayScale sampler algorithm from the original GH cluster.

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
    Build image-line mapped perforations using exact C# sampling algorithm.

    The original C# script:
    1. Loads image, converts to greyscale
    2. Scans all pixels to find min/max grayscale
    3. For each pick point, maps world coords → pixel coords
    4. Samples grayscale at that pixel
    5. Returns raw grayscale value (or 0 if <= min)

    Then downstream components map grayscale → die size.
    """
    is_imagelines = config["grid_pattern"] == "Image Lines Grid"

    if not is_imagelines:
        return {
            "is_imagelines": False,
            "hit_diameters": [],
            "hit_radii": [],
            "grayscale_values": [],
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

    # ── Sample grayscale and map to die sizes ─────────────────────
    hit_diameters = []
    hit_radii = []
    grayscale_values = []

    if image_data and image_data.get("is_loaded"):
        # Use the exact C# sampling algorithm
        from iw_product.image_processor import sample_grayscale, grayscale_to_die_size

        # MappedRegion bbox = overall panel boundary
        overall = grid.get("overall_boundary")
        if overall and HAS_RHINO:
            bb = overall.GetBoundingBox(True)
            mapped_bbox = (bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y)
        else:
            w = grid_params["overall_width"]
            h = grid_params["overall_height"]
            mapped_bbox = (0, 0, w, h)

        # Step 1: Sample grayscale at each perf point (exact C# port)
        grayscale_values = sample_grayscale(
            image_data, perf_points, mapped_bbox, config)

        # Step 2: Map grayscale → die sizes
        snap_dies = imagelines_die_list if punch_maximizer else None
        hit_diameters = grayscale_to_die_size(
            grayscale_values, min_rect, max_rect,
            image_data["min_gray"], image_data["max_gray"],
            snap_dies)
        hit_radii = [d / 2.0 for d in hit_diameters]

    elif HAS_RHINO and curve1 and curve2:
        # Fallback: distance-to-curves mapping
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
            grayscale_values.append(0)
    else:
        hit_diameters = [min_rect] * len(perf_points)
        hit_radii = [min_rect / 2.0] * len(perf_points)
        grayscale_values = [0] * len(perf_points)

    return {
        "is_imagelines": True,
        "hit_diameters": hit_diameters,
        "hit_radii": hit_radii,
        "grayscale_values": grayscale_values,
        "imageline_spines": imageline_spines,
        "driver_curve_1": curve1,
        "driver_curve_2": curve2,
    }
