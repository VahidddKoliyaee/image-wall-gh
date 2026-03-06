"""
Module: Collision Check
========================
Ensures perforations don't overlap panel edges, fasteners, or each other.
Replaces: StayOutside components.

Usage:
    from iw_product.collision_check import check_collisions
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def check_collisions(perf_points, perf_radii, panel_curves, fastener_points,
                     min_edge_distance=0.0, min_fastener_distance=0.0):
    """
    Filter perforations that collide with panel edges or fasteners.

    Args:
        perf_points: list of Point3d
        perf_radii: list of float
        panel_curves: list of Curve (panel face outlines)
        fastener_points: list of Point3d
        min_edge_distance: float, minimum distance from perf edge to panel edge
        min_fastener_distance: float, minimum distance from perf center to fastener

    Returns:
        dict with:
            valid_points  - list of Point3d (kept)
            valid_radii   - list of float (kept)
            valid_indices - list of int (original indices)
            removed_edge  - int count removed for edge collision
            removed_fast  - int count removed for fastener collision
    """
    if not perf_points:
        return {
            "valid_points": [], "valid_radii": [], "valid_indices": [],
            "removed_edge": 0, "removed_fast": 0,
        }

    valid_pts = []
    valid_rad = []
    valid_idx = []
    removed_edge = 0
    removed_fast = 0

    for i, pt in enumerate(perf_points):
        radius = perf_radii[i] if i < len(perf_radii) else 0.1
        keep = True

        # Check edge distance
        if HAS_RHINO and panel_curves and min_edge_distance >= 0:
            required_dist = radius + min_edge_distance
            for curve in panel_curves:
                if curve is None:
                    continue
                success, t = curve.ClosestPoint(pt)
                if success:
                    closest = curve.PointAt(t)
                    dist = pt.DistanceTo(closest)
                    if dist < required_dist:
                        keep = False
                        removed_edge += 1
                        break

        # Check fastener distance
        if keep and fastener_points and min_fastener_distance > 0:
            required_dist = radius + min_fastener_distance
            for fp in fastener_points:
                dist = pt.DistanceTo(fp) if HAS_RHINO else 999
                if dist < required_dist:
                    keep = False
                    removed_fast += 1
                    break

        if keep:
            valid_pts.append(pt)
            valid_rad.append(radius)
            valid_idx.append(i)

    return {
        "valid_points": valid_pts,
        "valid_radii": valid_rad,
        "valid_indices": valid_idx,
        "removed_edge": removed_edge,
        "removed_fast": removed_fast,
    }
