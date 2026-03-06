"""
Module: Inner Corners
======================
Handles special corner conditions for panels at inside corners.

Replaces: PANEL INNER CORNERS, Inside Corners, CORNERS WITH NO NOTCHES data flow.

Usage:
    from iw_product.inner_corners import detect_inner_corners
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def detect_inner_corners(config, grid, faces):
    """
    Detect which panel corners are inner corners (concave) vs outer.

    Inner corners don't get notched because the material folds inward.

    Args:
        config: dict from config_loader
        grid: dict from grid
        faces: dict from panel_faces

    Returns:
        dict with:
            inner_corners          - list of (panel_idx, corner_name)
            corners_with_no_notch  - list of (panel_idx, corner_name)
            notched_corners        - list of (panel_idx, corner_name)
    """
    panel_row_col = faces.get("panel_row_col", [])
    qty_cols = config["qty_columns"]
    qty_rows = config["qty_rows"]
    left_corner = faces.get("left_is_corner", [])
    right_corner = faces.get("right_is_corner", [])

    inner_corners = []
    corners_no_notch = []
    notched_corners = []

    for idx, (r, c) in enumerate(panel_row_col):
        corners = ["BL", "BR", "TR", "TL"]

        for corner in corners:
            is_inner = False

            # Inner corner detection:
            # A corner is "inner" if it's shared by 3 or 4 panels
            # (i.e., it's not at the wall perimeter)
            is_perimeter = False
            if "B" in corner and r == 0:
                is_perimeter = True
            if "T" in corner and r == qty_rows - 1:
                is_perimeter = True
            if "L" in corner and c == 0:
                is_perimeter = True
            if "R" in corner and c == qty_cols - 1:
                is_perimeter = True

            if not is_perimeter:
                is_inner = True
                inner_corners.append((idx, corner))
                corners_no_notch.append((idx, corner))
            else:
                notched_corners.append((idx, corner))

    return {
        "inner_corners": inner_corners,
        "corners_with_no_notch": corners_no_notch,
        "notched_corners": notched_corners,
    }
