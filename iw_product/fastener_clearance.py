"""
Module 10: Fastener Clearance
================================
Removes or resizes perforations near fastener/connection locations
to maintain structural integrity at attachment points.

Replaces: "Edit Perf for Fastener Tooling" group.

This module runs inside GH/Rhino.

Usage:
    from iw_product.fastener_clearance import apply_fastener_clearance
    result = apply_fastener_clearance(config, point_grid, die_data, faces)
"""

import Rhino.Geometry as rg


def apply_fastener_clearance(config, point_grid, die_data, faces):
    """
    Remove perforations that are too close to fastener/connection points.

    Args:
        config: dict from config_loader
        point_grid: dict from point_grid
        die_data: dict from die_selection (or imagelines)
        faces: dict from panel_faces

    Returns:
        dict with:
            perf_points       - filtered list of Point3d
            perf_planes       - filtered list of Plane
            die_diameters     - filtered list of diameters
            die_radii         - filtered list of radii
            removed_count     - int: how many perfs were removed
            perf_panel_index  - filtered panel indices
    """
    perf_points = point_grid["perf_points"]
    perf_planes = point_grid["perf_planes"]
    panel_indices = point_grid["perf_panel_index"]
    connection_points = faces["connection_points"]

    # Get diameters from imagelines if available, otherwise from die_data
    if die_data.get("die_diameters") and len(die_data["die_diameters"]) == len(perf_points):
        diameters = die_data["die_diameters"]
    else:
        # Fallback: uniform die
        selected = die_data.get("selected_die", 0.25)
        diameters = [selected] * len(perf_points)

    # Clearance distance: min_bridge + half the largest nearby fastener
    # Typically 2x the die diameter as clearance zone
    min_bridge = config["min_bridge"]
    clearance_factor = 2.0  # multiplier for clearance zone

    if not connection_points:
        return {
            "perf_points": perf_points,
            "perf_planes": perf_planes,
            "die_diameters": diameters,
            "die_radii": [d / 2.0 for d in diameters],
            "removed_count": 0,
            "perf_panel_index": panel_indices,
        }

    # ── Filter perforations ───────────────────────────────────────
    filtered_pts = []
    filtered_planes = []
    filtered_diameters = []
    filtered_radii = []
    filtered_indices = []
    removed = 0

    for i, pt in enumerate(perf_points):
        diameter = diameters[i]
        clearance = (diameter / 2.0) + min_bridge * clearance_factor

        # Check distance to all connection points
        too_close = False
        for cp in connection_points:
            dist = pt.DistanceTo(cp)
            if dist < clearance:
                too_close = True
                break

        if too_close:
            removed += 1
        else:
            filtered_pts.append(pt)
            filtered_planes.append(perf_planes[i])
            filtered_diameters.append(diameter)
            filtered_radii.append(diameter / 2.0)
            filtered_indices.append(panel_indices[i])

    return {
        "perf_points": filtered_pts,
        "perf_planes": filtered_planes,
        "die_diameters": filtered_diameters,
        "die_radii": filtered_radii,
        "removed_count": removed,
        "perf_panel_index": filtered_indices,
    }
