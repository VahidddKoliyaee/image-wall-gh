"""
Module 08: Die Selection
==========================
Maps perforation points to available punch die sizes.
Uses configurable die list from config instead of hardcoded values.

Usage:
    from iw_product.die_selection import select_die_sizes
    dies = select_die_sizes(config, grid_params, point_grid)
"""

import math

DEFAULT_ROUND_DIES = [
    0.0625, 0.09375, 0.125, 0.15625, 0.1875, 0.21875, 0.25,
    0.3125, 0.375, 0.4375, 0.5, 0.5625, 0.625, 0.75, 0.875,
    1.0, 1.125, 1.25, 1.375, 1.5, 1.625, 1.75, 2.0,
]


def _available_dies(smallest_perf, custom_list=None):
    source = custom_list if custom_list else DEFAULT_ROUND_DIES
    return sorted(d for d in source if d >= smallest_perf - 0.0001)


def _max_die_for_spacing(spacing, min_bridge):
    return max(0, spacing - min_bridge)


def select_die_sizes(config, grid_params, point_grid):
    """
    For each perforation point, select the largest available die
    that fits within the spacing/bridge constraints.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        point_grid: dict from point_grid

    Returns:
        dict with:
            die_diameters       - list of float per point
            die_radii           - list of float per point
            size_selection_index - list of int
            available_dies      - sorted list of available sizes
            selected_die        - float uniform die size
            total_die_count     - int
    """
    smallest_perf = config["smallest_perf"]
    min_bridge = config["min_bridge"]
    custom_dies = config.get("imagelines_die_list")
    punch_maximizer = config.get("punch_use_maximizer", False)

    available = _available_dies(smallest_perf, custom_dies if punch_maximizer else None)
    perf_points = point_grid["perf_points"]

    if not perf_points or not available:
        return {
            "die_diameters": [],
            "die_radii": [],
            "size_selection_index": [],
            "available_dies": available,
            "selected_die": 0.0,
            "total_die_count": 0,
        }

    true_col_sp = grid_params["true_grid_col_spacing"]
    true_row_sp = grid_params["true_grid_row_spacing"]
    min_spacing = min(true_col_sp, true_row_sp)
    max_die = _max_die_for_spacing(min_spacing, min_bridge)

    if grid_params["is_diagonal"]:
        diag_spacing = min_spacing * math.sqrt(2)
        max_die_diag = _max_die_for_spacing(diag_spacing, min_bridge)
        max_die = min(max_die, max_die_diag)

    selected_die = available[0]
    selected_index = 0
    for i, d in enumerate(available):
        if d <= max_die + 0.0001:
            selected_die = d
            selected_index = i
        else:
            break

    n = len(perf_points)
    die_diameters = [selected_die] * n
    die_radii = [selected_die / 2.0] * n
    size_selection_index = [selected_index] * n

    return {
        "die_diameters": die_diameters,
        "die_radii": die_radii,
        "size_selection_index": size_selection_index,
        "available_dies": available,
        "selected_die": selected_die,
        "total_die_count": n,
    }