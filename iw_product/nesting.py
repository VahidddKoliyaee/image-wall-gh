"""
Module: Nesting
================
Sheet nesting optimization for material usage.
Places panel flat patterns on standard sheet sizes to minimize waste.

Replaces: OpenNest/Nesting components.

Usage:
    from iw_product.nesting import nest_panels
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def nest_panels(unfold, naming, sheet_width=48.0, sheet_length=120.0, spacing=0.25):
    """
    Simple strip-nesting of panel flat patterns onto standard sheets.

    This is a basic left-to-right, bottom-to-top packing algorithm.
    For production, consider using OpenNest or similar.

    Args:
        unfold: dict from panel_unfold
        naming: dict from panel_naming
        sheet_width: float, sheet width in inches
        sheet_length: float, sheet length in inches
        spacing: float, gap between nested parts

    Returns:
        dict with:
            nested_curves   - list of Curve (positioned on sheets)
            sheet_count     - int
            sheet_outlines  - list of Curve (sheet rectangles)
            utilization     - float (0-1, material usage ratio)
            panel_positions - list of (sheet_idx, x, y)
    """
    dims = unfold.get("unfold_dims", [])
    curves = unfold.get("unfold_curves", [])
    names = naming.get("full_panel_names", [])

    if not dims or not HAS_RHINO:
        return {
            "nested_curves": [], "sheet_count": 0,
            "sheet_outlines": [], "utilization": 0,
            "panel_positions": [],
        }

    # Sort panels by height (tallest first) for better packing
    indexed = sorted(enumerate(dims), key=lambda x: -x[1][1])

    sheets = []  # list of (x_cursor, y_cursor, row_height, panels_on_sheet)
    current_sheet = {"x": 0, "y": 0, "row_h": 0, "panels": []}
    sheet_idx = 0

    nested_curves = [None] * len(dims)
    panel_positions = [None] * len(dims)

    for orig_idx, (w, h) in indexed:
        placed = False

        # Try to fit in current row
        if current_sheet["x"] + w <= sheet_length and current_sheet["y"] + h <= sheet_width:
            # Fits in current row
            nx = current_sheet["x"]
            ny = current_sheet["y"]
            current_sheet["x"] += w + spacing
            current_sheet["row_h"] = max(current_sheet["row_h"], h)
            current_sheet["panels"].append(orig_idx)
            placed = True
        else:
            # Try next row
            new_y = current_sheet["y"] + current_sheet["row_h"] + spacing
            if new_y + h <= sheet_width and w <= sheet_length:
                current_sheet["x"] = w + spacing
                current_sheet["y"] = new_y
                current_sheet["row_h"] = h
                nx = 0
                ny = new_y
                current_sheet["panels"].append(orig_idx)
                placed = True

        if not placed:
            # New sheet
            sheets.append(current_sheet)
            sheet_idx += 1
            current_sheet = {"x": w + spacing, "y": 0, "row_h": h, "panels": [orig_idx]}
            nx = 0
            ny = 0

        # Position the curve
        panel_positions[orig_idx] = (sheet_idx, nx, ny)
        sheet_offset_x = sheet_idx * (sheet_length + 5)  # space between sheets
        move_vec = rg.Vector3d(sheet_offset_x + nx, ny, 0)

        # Get original curve and move it
        orig_curve = curves[orig_idx]
        if orig_curve:
            bb = orig_curve.GetBoundingBox(True)
            # Move from original position to nested position
            offset = rg.Vector3d(
                move_vec.X - bb.Min.X,
                move_vec.Y - bb.Min.Y, 0)
            moved = orig_curve.DuplicateCurve()
            moved.Transform(rg.Transform.Translation(offset))
            nested_curves[orig_idx] = moved

    sheets.append(current_sheet)
    total_sheets = sheet_idx + 1

    # Sheet outlines
    sheet_outlines = []
    for s in range(total_sheets):
        sx = s * (sheet_length + 5)
        pts = [
            rg.Point3d(sx, 0, 0),
            rg.Point3d(sx + sheet_length, 0, 0),
            rg.Point3d(sx + sheet_length, sheet_width, 0),
            rg.Point3d(sx, sheet_width, 0),
            rg.Point3d(sx, 0, 0),
        ]
        sheet_outlines.append(rg.Polyline(pts).ToPolylineCurve())

    # Utilization
    total_panel_area = sum(w * h for w, h in dims)
    total_sheet_area = total_sheets * sheet_width * sheet_length
    utilization = total_panel_area / total_sheet_area if total_sheet_area > 0 else 0

    return {
        "nested_curves": [c for c in nested_curves if c],
        "sheet_count": total_sheets,
        "sheet_outlines": sheet_outlines,
        "utilization": utilization,
        "panel_positions": panel_positions,
    }
