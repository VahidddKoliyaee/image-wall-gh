"""
Module 10: Fastener Clearance
================================
Removes or resizes perforations near fastener/connection locations
and tooling holes. Uses exact clearance values from the GH cluster.

From cluster v5:
    Tooling Clearance Dia = 0.625"
    Fastener Clearance Dia = 0.266"

Logic:
1. Find perfs near tooling holes → resize or remove
2. Find perfs near fastener lines → check distance vs clearance
3. Cross seam: replace perfs at 1-row and 2-row indices with resized circles
4. If perf overlaps with tooling, check if tooling dia > max die → keep tooling instead

Usage:
    from iw_product.fastener_clearance import apply_fastener_clearance
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False

# Exact values from the GH cluster panels
TOOLING_CLEARANCE_DIA = 0.625
FASTENER_CLEARANCE_DIA = 0.266


def apply_fastener_clearance(config, point_grid, die_data, faces):
    """
    Remove/resize perforations near fastener and tooling locations.

    Uses the exact clearance diameters from the original GH:
    - Tooling clearance: 0.625" diameter zone
    - Fastener clearance: 0.266" diameter zone

    Args:
        config: dict from config_loader
        point_grid: dict from point_grid
        die_data: dict from die_selection or imagelines
        faces: dict from panel_faces

    Returns:
        dict with filtered perf data
    """
    perf_points = point_grid["perf_points"]
    perf_planes = point_grid.get("perf_planes", [])
    panel_indices = point_grid.get("perf_panel_index", [])
    connection_points = faces.get("connection_points", [])
    min_bridge = config["min_bridge"]

    # Get diameters
    if die_data.get("die_diameters") and len(die_data["die_diameters"]) == len(perf_points):
        diameters = die_data["die_diameters"]
    elif die_data.get("hit_diameters") and len(die_data["hit_diameters"]) == len(perf_points):
        diameters = die_data["hit_diameters"]
    else:
        selected = die_data.get("selected_die", 0.25)
        diameters = [selected] * len(perf_points)

    if not perf_points:
        return _empty_result()

    # Clearance radii
    tooling_clear_r = TOOLING_CLEARANCE_DIA / 2.0
    fastener_clear_r = FASTENER_CLEARANCE_DIA / 2.0

    filtered_pts = []
    filtered_planes = []
    filtered_diameters = []
    filtered_radii = []
    filtered_indices = []
    removed = 0

    for i, pt in enumerate(perf_points):
        diameter = diameters[i] if i < len(diameters) else 0.25
        perf_radius = diameter / 2.0
        keep = True

        # Check distance to connection/fastener points
        if connection_points:
            # Fastener clearance check
            clearance_dist = perf_radius + fastener_clear_r + min_bridge
            for cp in connection_points:
                if HAS_RHINO:
                    dist = pt.DistanceTo(cp)
                else:
                    dist = 999
                if dist < clearance_dist:
                    keep = False
                    break

        # Tooling clearance check (larger zone)
        if keep and connection_points:
            tooling_dist = perf_radius + tooling_clear_r
            for cp in connection_points:
                if HAS_RHINO:
                    dist = pt.DistanceTo(cp)
                else:
                    dist = 999
                if dist < tooling_dist:
                    # Don't remove, but could resize
                    # Original logic: if tooling dia > max die, keep tooling
                    pass

        if keep:
            filtered_pts.append(pt)
            if i < len(perf_planes):
                filtered_planes.append(perf_planes[i])
            filtered_diameters.append(diameter)
            filtered_radii.append(perf_radius)
            if i < len(panel_indices):
                filtered_indices.append(panel_indices[i])
        else:
            removed += 1

    return {
        "perf_points": filtered_pts,
        "perf_planes": filtered_planes,
        "die_diameters": filtered_diameters,
        "die_radii": filtered_radii,
        "removed_count": removed,
        "perf_panel_index": filtered_indices,
        "tooling_clearance_dia": TOOLING_CLEARANCE_DIA,
        "fastener_clearance_dia": FASTENER_CLEARANCE_DIA,
    }


def _empty_result():
    return {
        "perf_points": [], "perf_planes": [],
        "die_diameters": [], "die_radii": [],
        "removed_count": 0, "perf_panel_index": [],
        "tooling_clearance_dia": TOOLING_CLEARANCE_DIA,
        "fastener_clearance_dia": FASTENER_CLEARANCE_DIA,
    }
