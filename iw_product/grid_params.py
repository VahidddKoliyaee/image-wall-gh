"""
Module 02: Grid Parameters
============================
Computes derived grid parameters from the config dictionary.
Includes accurate brake leg depths and stretchout per style
from the original GH definition.

Usage:
    from iw_product.grid_params import compute_grid_params
    gp = compute_grid_params(config)
"""

import math

# Brake leg depths per style index [primary, secondary]
# From GH "Brake Leg Depths" panels:
#   Primary:   6, 4, 2.75, 2.75, 0
#   Secondary: 2, 1.5, 0, 0, 0
BRAKE_LEG_TABLE = {
    # style_index: (primary_depth, secondary_depth)
    0: (6.0, 2.0),      # Double Return Long Span
    1: (4.0, 1.5),      # Double Return Short Span
    2: (2.75, 0.0),     # Droplock Hat Channel
    3: (2.75, 0.0),     # Droplock Mullion
    4: (0.0, 0.0),      # Flat (no legs at all)
}

# Style name → index mapping
STYLE_LIST = [
    "Double Return Long Span [Horizontal]",   # 0
    "Double Return Long Span [Vertical]",      # 1
    "Double Return Short Span [Horizontal]",   # 2
    "Double Return Short Span [Vertical]",     # 3
    "Droplock Hat Channel",                    # 4
    "Droplock Mullion",                        # 5
    "Flat [Horizontal]",                       # 6
    "Flat [Vertical]",                         # 7
]

# Map 8 styles to 5 brake leg indices:
# 0,1 → brake idx 0 (Long Span)
# 2,3 → brake idx 1 (Short Span)
# 4   → brake idx 2 (Hat Channel)
# 5   → brake idx 3 (Mullion)
# 6,7 → brake idx 4 (Flat)
STYLE_TO_BRAKE_INDEX = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4}


def compute_grid_params(config):
    """
    Compute all derived grid parameters from the project config.
    """
    style = config["style"]
    vertical = config["vertical"]
    panel_col_width = config["panel_col_width"]
    panel_row_height = config["panel_row_height"]
    qty_columns = config["qty_columns"]
    qty_rows = config["qty_rows"]
    grid_pattern = config["grid_pattern"]
    perf_spacing = config["perf_spacing"]
    material_thickness = config["material_thickness"]

    # ── Style index ───────────────────────────────────────────────
    style_index = STYLE_LIST.index(style) if style in STYLE_LIST else 0

    # ── Style flags ───────────────────────────────────────────────
    is_double_return = style_index in (0, 1, 2, 3)
    is_droplock = style_index in (4, 5)
    is_flat = style_index in (6, 7)
    is_long_span = style_index in (0, 1)
    is_short_span = style_index in (2, 3)
    is_horizontal = style_index in (0, 2, 6)

    # ── Brake leg index and depths ────────────────────────────────
    brake_index = STYLE_TO_BRAKE_INDEX.get(style_index, 4)
    primary_leg_depth, secondary_leg_depth = BRAKE_LEG_TABLE.get(brake_index, (0, 0))

    # ── Gate indices ──────────────────────────────────────────────
    # Gate [Brake Legs]: 0=DR Long, 1=DR Short, 2=Droplock HC, 3=Droplock Mull, 4=Flat
    gate_brake_legs = brake_index

    # Gate [Connection]: 0=Double Return, 1=Other
    gate_connection = 0 if is_double_return else 1

    # Gate [Perf]: 0=standard, 1=image lines, 2=no perf
    if config["no_perf_level"]:
        gate_perf = 2
    elif grid_pattern == "Image Lines Grid":
        gate_perf = 1
    else:
        gate_perf = 0

    # Gate [Stretch]: 0=standard, 1=special
    gate_stretch = 0 if is_double_return else 1

    # ── Stretchout (bend allowance) ───────────────────────────────
    # For sheet metal bending, stretchout = material thickness per bend
    # Double Return has bends, Flat does not
    if is_flat:
        stretchout_one_side = 0.0
    else:
        stretchout_one_side = material_thickness

    # ── Panel joint ───────────────────────────────────────────────
    # From GH: Item(Brake Leg Depths) - PANEL JOINT
    # Panel joint is subtracted from brake leg depth
    # Default panel joint = 0 (typical for ImageWall)
    panel_joint = 0.0

    # Effective brake depth = primary_leg_depth - panel_joint
    effective_primary_leg = primary_leg_depth - panel_joint
    effective_secondary_leg = secondary_leg_depth - panel_joint

    # ── Grid spacing ──────────────────────────────────────────────
    grid_spacing = perf_spacing
    grid_spacing_width_min = perf_spacing
    grid_spacing_height_min = perf_spacing

    is_diagonal = "Diagonal" in grid_pattern
    if is_diagonal:
        diagonal_factor = math.sqrt(2)
        grid_spacing_width_min = perf_spacing * diagonal_factor
        grid_spacing_height_min = perf_spacing * diagonal_factor

    is_force_square = grid_pattern == "Force Square"

    # ── Panel face dimensions (before stretch) ────────────────────
    # Panel face = panel size - 2 * stretchout
    panel_face_width = panel_col_width - (stretchout_one_side * 2)
    panel_face_height = panel_row_height - (stretchout_one_side * 2)

    # ── Point grid dimensions ─────────────────────────────────────
    if grid_spacing_width_min > 0:
        qty_pt_grid_cols = max(1, round(panel_face_width / grid_spacing_width_min))
    else:
        qty_pt_grid_cols = 1

    if grid_spacing_height_min > 0:
        qty_pt_grid_rows = max(1, round(panel_face_height / grid_spacing_height_min))
    else:
        qty_pt_grid_rows = 1

    true_grid_col_spacing = panel_face_width / qty_pt_grid_cols if qty_pt_grid_cols > 0 else 0
    true_grid_row_spacing = panel_face_height / qty_pt_grid_rows if qty_pt_grid_rows > 0 else 0

    # ── Column/Row series ─────────────────────────────────────────
    col_series = [i * panel_col_width for i in range(qty_columns)]
    row_series = [i * panel_row_height for i in range(qty_rows)]

    # ── Overall dimensions ────────────────────────────────────────
    overall_width = qty_columns * panel_col_width
    overall_height = qty_rows * panel_row_height

    # ── Cross seam ────────────────────────────────────────────────
    cross_seam = config["cross_seam"]
    cross_seam_flat = cross_seam == "Default"

    # ── Diagonal flags ────────────────────────────────────────────
    is_diagonal_vertical = grid_pattern == "Force Diagonal - Vertical"
    is_diagonal_horizontal = grid_pattern == "Force Diagonal - Horizontal"

    # ── Invert ────────────────────────────────────────────────────
    invert = config["invert_image"]

    return {
        # Style routing
        "style_index": style_index,
        "vertical": vertical,
        "is_double_return": is_double_return,
        "is_droplock": is_droplock,
        "is_flat": is_flat,
        "is_long_span": is_long_span,
        "is_short_span": is_short_span,
        "is_horizontal": is_horizontal,

        # Gate indices
        "gate_brake_legs": gate_brake_legs,
        "gate_connection": gate_connection,
        "gate_perf": gate_perf,
        "gate_stretch": gate_stretch,

        # Brake legs (from GH Brake Leg Depths panels)
        "brake_index": brake_index,
        "primary_leg_depth": primary_leg_depth,
        "secondary_leg_depth": secondary_leg_depth,
        "effective_primary_leg": effective_primary_leg,
        "effective_secondary_leg": effective_secondary_leg,

        # Grid spacing
        "grid_spacing": grid_spacing,
        "grid_spacing_width_min": grid_spacing_width_min,
        "grid_spacing_height_min": grid_spacing_height_min,
        "is_diagonal": is_diagonal,
        "is_diagonal_vertical": is_diagonal_vertical,
        "is_diagonal_horizontal": is_diagonal_horizontal,
        "is_force_square": is_force_square,

        # Panel face
        "stretchout_one_side": stretchout_one_side,
        "panel_face_width": panel_face_width,
        "panel_face_height": panel_face_height,

        # Point grid
        "qty_pt_grid_cols": qty_pt_grid_cols,
        "qty_pt_grid_rows": qty_pt_grid_rows,
        "true_grid_col_spacing": true_grid_col_spacing,
        "true_grid_row_spacing": true_grid_row_spacing,

        # Series
        "col_series": col_series,
        "row_series": row_series,

        # Panel layout
        "panel_joint": panel_joint,
        "overall_width": overall_width,
        "overall_height": overall_height,

        # Cross seam
        "cross_seam": cross_seam,
        "cross_seam_flat": cross_seam_flat,

        # Flags
        "invert": invert,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from config_loader import load_config

    path = sys.argv[1] if len(sys.argv) > 1 else "IW-Product.xlsx"
    config = load_config(path)
    gp = compute_grid_params(config)

    print("Style: {} (index={})".format(config["style"], gp["style_index"]))
    print("Brake legs: primary={}, secondary={}".format(
        gp["primary_leg_depth"], gp["secondary_leg_depth"]))
    print("Stretchout: {}".format(gp["stretchout_one_side"]))
    print("Panel face: {} x {}".format(gp["panel_face_width"], gp["panel_face_height"]))