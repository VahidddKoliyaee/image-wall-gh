"""
Module: Cross Seam
===================
Handles cross-seam joint variations between panel rows.

Cross seam styles:
- Default: standard flat seam
- 1-Row: single row of perforations at seam
- 2-Row: double row of perforations at seam

Replaces: Cross Seam Style, Cross Seam Flat?, Cross Seam Hits,
CROSS SEAM INDICES, 1 Row (Cross Seam) Indices data flow.

Usage:
    from iw_product.cross_seam import compute_cross_seam
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def compute_cross_seam(config, grid_params, grid, faces):
    """
    Compute cross-seam geometry and affected perforation indices.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from grid
        faces: dict from panel_faces

    Returns:
        dict with:
            cross_seam_style   - str
            cross_seam_flat    - bool
            seam_y_positions   - list of float (Y positions of seams)
            seam_lines         - list of LineCurve
            indices_1_row      - list of int (perf indices at 1-row seams)
            indices_2_row      - list of int (perf indices at 2-row seams)
            seam_hits          - list of bool per perf point
    """
    cross_seam = config.get("cross_seam", "Default")
    qty_rows = config["qty_rows"]
    row_h = config["panel_row_height"]
    overall_w = grid_params["overall_width"]
    perf_spacing = config["perf_spacing"]

    # Seam Y positions (between row boundaries)
    seam_y_positions = []
    for r in range(1, qty_rows):
        seam_y_positions.append(r * row_h)

    # Seam lines
    seam_lines = []
    if HAS_RHINO:
        for y in seam_y_positions:
            line = rg.LineCurve(
                rg.Point3d(0, y, 0),
                rg.Point3d(overall_w, y, 0))
            seam_lines.append(line)

    # Determine style
    is_flat = cross_seam == "Default"
    is_1_row = "1" in str(cross_seam)
    is_2_row = "2" in str(cross_seam)

    # Compute which perf points fall near seam lines
    indices_1_row = []
    indices_2_row = []
    seam_hits = []

    # These will be populated when we have actual perf point data
    # For now, return the structure

    return {
        "cross_seam_style": cross_seam,
        "cross_seam_flat": is_flat,
        "seam_y_positions": seam_y_positions,
        "seam_lines": seam_lines,
        "indices_1_row": indices_1_row,
        "indices_2_row": indices_2_row,
        "seam_hits": seam_hits,
    }


def filter_perfs_at_seams(perf_points, seam_y_positions, perf_spacing, cross_seam_style):
    """
    Filter perforation points near cross-seam locations.

    Args:
        perf_points: list of Point3d
        seam_y_positions: list of float
        perf_spacing: float
        cross_seam_style: str

    Returns:
        list of bool: True if point should be kept
    """
    keep = []
    seam_zone = perf_spacing * 1.5  # zone around seam

    for pt in perf_points:
        y = pt.Y if hasattr(pt, "Y") else pt[1]
        near_seam = any(abs(y - sy) < seam_zone for sy in seam_y_positions)

        if near_seam and cross_seam_style == "Default":
            keep.append(True)  # Default: keep all
        elif near_seam:
            keep.append(False)  # Non-default: remove near seam
        else:
            keep.append(True)

    return keep
