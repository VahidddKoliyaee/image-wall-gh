"""
Module 08: Die Selection
==========================
Maps each perforation point to an available punch die size based on
spacing constraints (minimum bridge between perforations).

Replaces: "Select Punch Die Sizes" group — the die size matching,
Available Dies lookup, and size selection index logic.

This module runs inside GH/Rhino.

Usage:
    from iw_product.die_selection import select_die_sizes
    dies = select_die_sizes(config, grid_params, point_grid)
"""

import math
import Rhino.Geometry as rg


# Standard Zahner punch die inventory (diameters in inches)
DEFAULT_ROUND_DIES = [
    0.0625, 0.09375, 0.125, 0.15625, 0.1875, 0.21875, 0.25,
    0.3125, 0.375, 0.4375, 0.5, 0.5625, 0.625, 0.75, 0.875,
    1.0, 1.125, 1.25, 1.375, 1.5, 1.625, 1.75, 2.0,
]


def _available_dies(smallest_perf):
    """Get sorted list of available die sizes >= smallest_perf."""
    return sorted(d for d in DEFAULT_ROUND_DIES if d >= smallest_perf - 0.0001)


def _max_die_for_spacing(spacing, min_bridge):
    """Maximum die diameter that fits with given spacing and min bridge."""
    # diameter + bridge <= spacing (center-to-center)
    return max(0, spacing - min_bridge)


def select_die_sizes(config, grid_params, point_grid):
    """
    For each perforation point, select the largest available die that
    fits within the spacing/bridge constraints.

    For uniform grids, all points typically get the same die size.
    For image-mapped patterns, sizes vary per point.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        point_grid: dict from point_grid

    Returns:
        dict with:
            die_diameters       - list of float: diameter per perf point
            die_radii           - list of float: radius per perf point
            size_selection_index - list of int: index into available_dies list
            available_dies      - sorted list of available die sizes
            selected_die        - float: the uniform die size (if uniform)
            total_die_count     - int
    """
    smallest_perf = config["smallest_perf"]
    min_bridge = config["min_bridge"]
    perf_spacing = config["perf_spacing"]

    available = _available_dies(smallest_perf)
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

    # For uniform circular perforations:
    # Max diameter = spacing - min_bridge
    true_col_sp = grid_params["true_grid_col_spacing"]
    true_row_sp = grid_params["true_grid_row_spacing"]
    min_spacing = min(true_col_sp, true_row_sp)

    max_die = _max_die_for_spacing(min_spacing, min_bridge)

    # Find largest available die that fits
    selected_die = available[0]  # smallest as fallback
    selected_index = 0
    for i, d in enumerate(available):
        if d <= max_die + 0.0001:
            selected_die = d
            selected_index = i
        else:
            break

    # For diagonal grids, the diagonal spacing is different
    if grid_params["is_diagonal"]:
        diag_spacing = min_spacing * math.sqrt(2)
        max_die_diag = _max_die_for_spacing(diag_spacing, min_bridge)
        # Use the smaller of the two constraints
        max_die = min(max_die, max_die_diag)
        selected_die = available[0]
        selected_index = 0
        for i, d in enumerate(available):
            if d <= max_die + 0.0001:
                selected_die = d
                selected_index = i
            else:
                break

    # Assign same die to all points (uniform mode)
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
