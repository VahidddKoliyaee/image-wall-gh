"""
Module 02: Grid Parameters
============================
Computes derived grid parameters from the config dictionary.
Replaces: Style routing (Equality checks + Gate indices), grid spacing
calculations, Series generators, VERTICAL? flag, panel dimension validation.

Usage:
    from iw_product.grid_params import compute_grid_params
    gp = compute_grid_params(config)
"""

import math


def compute_grid_params(config):
    """
    Compute all derived grid parameters from the project config.

    Args:
        config: dict from config_loader.load_config()

    Returns:
        dict with all derived grid parameters.
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
    smallest_perf = config["smallest_perf"]
    min_bridge = config["min_bridge"]

    # ── Style index (maps style name to numeric index) ────────────
    # The GH definition uses Equality checks against STYLE index
    # to route data through Pick'n'Choose / Stream Filters
    style_list = [
        "Double Return Long Span [Horizontal]",   # 0
        "Double Return Long Span [Vertical]",      # 1
        "Double Return Short Span [Horizontal]",   # 2
        "Double Return Short Span [Vertical]",     # 3
        "Droplock Hat Channel",                    # 4
        "Droplock Mullion",                        # 5
        "Flat [Horizontal]",                       # 6
        "Flat [Vertical]",                         # 7
    ]
    style_index = style_list.index(style) if style in style_list else 0

    # ── Gate indices (from Equality + Gate Or + Addition chains) ───
    # These control which code paths are active for different styles
    is_double_return = style_index in (0, 1, 2, 3)
    is_droplock = style_index in (4, 5)
    is_flat = style_index in (6, 7)
    is_long_span = style_index in (0, 1)
    is_short_span = style_index in (2, 3)
    is_horizontal = style_index in (0, 2, 6)

    # Gate Index [Brake Legs]: 0=Double Return, 1=Droplock, 2=Flat
    # From GH: Or(Equals(STYLE,0), Equals(STYLE,1), ...) → A×B(Or, 2) + ...
    if is_double_return:
        gate_brake_legs = 0
    elif is_droplock:
        gate_brake_legs = 1
    else:
        gate_brake_legs = 2

    # Gate Index [Connection]: 0 or 1
    # Double Return styles have connection type 0, others 1
    gate_connection = 0 if is_double_return else 1

    # Gate Index [Perf]: controls perforation approach
    # 0 = standard circle perf, 1 = image lines, 2 = no perf
    if config["no_perf_level"]:
        gate_perf = 2
    elif grid_pattern == "Image Lines Grid":
        gate_perf = 1
    else:
        gate_perf = 0

    # Gate Index [Stretch]: controls stretchout calculation
    # 0 = standard, 1 = special (droplock/flat)
    gate_stretch = 0 if is_double_return else 1

    # ── Grid spacing calculation ──────────────────────────────────
    # From GH: GRID SPACING feeds into expressions for row/col spacing
    # The definition computes min grid spacing for width and height
    # based on smallest perf + min bridge: spacing = smallest_perf * 2 + min_bridge
    # Then: GRID SPACING WIDTH MIN = GRID SPACING HEIGHT MIN = perf_spacing
    # (unless overridden by diagonal patterns)
    grid_spacing = perf_spacing
    grid_spacing_width_min = perf_spacing
    grid_spacing_height_min = perf_spacing

    # For diagonal patterns, spacing is multiplied by sqrt(2)
    is_diagonal = "Diagonal" in grid_pattern
    if is_diagonal:
        diagonal_factor = math.sqrt(2)
        grid_spacing_width_min = perf_spacing * diagonal_factor
        grid_spacing_height_min = perf_spacing * diagonal_factor

    # For "Force Square", width and height spacing are equal
    is_force_square = grid_pattern == "Force Square"

    # ── Panel face dimensions (before stretch) ────────────────────
    # STRETCHOUT [1 SIDE] depends on style and material thickness
    # Double Return: stretchout = material_thickness (one bend)
    # Droplock/Flat: stretchout varies
    if is_double_return:
        stretchout_one_side = material_thickness
    elif is_droplock:
        stretchout_one_side = material_thickness * 2
    else:
        stretchout_one_side = 0.0

    panel_face_width = panel_col_width - (stretchout_one_side * 2)
    panel_face_height = panel_row_height - (stretchout_one_side * 2)

    # ── Point grid dimensions ─────────────────────────────────────
    # QTY OF PT GRID COLUMNS = Round(panel_face_width / grid_spacing_width_min)
    # QTY OF PT GRID ROWS = Round(panel_face_height / grid_spacing_height_min)
    if grid_spacing_width_min > 0:
        qty_pt_grid_cols = max(1, round(panel_face_width / grid_spacing_width_min))
    else:
        qty_pt_grid_cols = 1

    if grid_spacing_height_min > 0:
        qty_pt_grid_rows = max(1, round(panel_face_height / grid_spacing_height_min))
    else:
        qty_pt_grid_rows = 1

    # TRUE GRID spacing = panel_face / qty_pt_grid (actual spacing after rounding)
    true_grid_col_spacing = panel_face_width / qty_pt_grid_cols if qty_pt_grid_cols > 0 else 0
    true_grid_row_spacing = panel_face_height / qty_pt_grid_rows if qty_pt_grid_rows > 0 else 0

    # ── Column/Row series ─────────────────────────────────────────
    # Series(Start=0, Step=COLUMN_WIDTH, Count=QTY_COLUMNS)
    col_series = [i * panel_col_width for i in range(qty_columns)]
    row_series = [i * panel_row_height for i in range(qty_rows)]

    # ── Panel joint (gap between panels) ──────────────────────────
    # Default panel joint = 0 (tight fit), but can be specified
    panel_joint = 0.0  # TODO: read from config if available

    # ── Overall dimensions ────────────────────────────────────────
    overall_width = qty_columns * panel_col_width
    overall_height = qty_rows * panel_row_height

    # ── Cross seam ────────────────────────────────────────────────
    cross_seam = config["cross_seam"]
    cross_seam_flat = cross_seam == "Default"

    # ── Diagonal flag ─────────────────────────────────────────────
    is_diagonal_vertical = grid_pattern == "Force Diagonal - Vertical"
    is_diagonal_horizontal = grid_pattern == "Force Diagonal - Horizontal"

    # ── Invert ────────────────────────────────────────────────────
    invert = config["invert_image"]

    # ── Build output dict ─────────────────────────────────────────
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
    import sys, json
    sys.path.insert(0, ".")
    from config_loader import load_config

    path = sys.argv[1] if len(sys.argv) > 1 else "IW-Product.xlsx"
    config = load_config(path)
    gp = compute_grid_params(config)

    print("Style: {} (index={})".format(config["style"], gp["style_index"]))
    print("Vertical: {}".format(gp["vertical"]))
    print("Gates: brake={}, conn={}, perf={}, stretch={}".format(
        gp["gate_brake_legs"], gp["gate_connection"],
        gp["gate_perf"], gp["gate_stretch"]))
    print("Grid spacing: {} (true: {}x{})".format(
        gp["grid_spacing"], gp["true_grid_col_spacing"], gp["true_grid_row_spacing"]))
    print("Panel face: {} x {}".format(gp["panel_face_width"], gp["panel_face_height"]))
    print("Pt grid: {} x {}".format(gp["qty_pt_grid_cols"], gp["qty_pt_grid_rows"]))
    print("Col series: {}".format(gp["col_series"]))
    print("Row series: {}".format(gp["row_series"]))
    print("Overall: {} x {}".format(gp["overall_width"], gp["overall_height"]))
