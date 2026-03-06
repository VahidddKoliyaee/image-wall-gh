"""
Module: Rule Zone
==================
Handles restricted perforation zones where patterns are modified or excluded.
Includes problem zone width and threshold overrule logic.

Replaces: RULE ZONE?, PROBLEM ZONE WIDTH data flow.

Usage:
    from iw_product.rule_zone import apply_rule_zones
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def apply_rule_zones(perf_points, perf_radii, panel_curves, config):
    """
    Apply rule zone restrictions to perforation points.

    Rule zones are regions near panel edges where perforations
    are excluded or reduced in size.

    Args:
        perf_points: list of Point3d
        perf_radii: list of float
        panel_curves: list of Curve (panel face outlines)
        config: dict with rule zone settings

    Returns:
        dict with:
            points      - filtered list of Point3d
            radii       - filtered list of float
            in_zone     - list of bool per original point
            removed     - int count
    """
    rule_zone_active = config.get("rule_zone", False)
    problem_zone_width = config.get("problem_zone_width", 0.0)

    if not rule_zone_active or problem_zone_width <= 0 or not HAS_RHINO:
        return {
            "points": perf_points,
            "radii": perf_radii,
            "in_zone": [False] * len(perf_points),
            "removed": 0,
        }

    filtered_pts = []
    filtered_rad = []
    in_zone = []
    removed = 0

    for i, pt in enumerate(perf_points):
        radius = perf_radii[i] if i < len(perf_radii) else 0.1
        is_in_zone = False

        for curve in panel_curves:
            if curve is None:
                continue
            success, t = curve.ClosestPoint(pt)
            if success:
                closest = curve.PointAt(t)
                dist = pt.DistanceTo(closest)
                if dist < problem_zone_width:
                    is_in_zone = True
                    break

        in_zone.append(is_in_zone)
        if is_in_zone:
            removed += 1
        else:
            filtered_pts.append(pt)
            filtered_rad.append(radius)

    return {
        "points": filtered_pts,
        "radii": filtered_rad,
        "in_zone": in_zone,
        "removed": removed,
    }
