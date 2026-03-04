"""
Module 18: Submittal Maker
============================
Generates submittal documentation layouts.

Replaces: "Make Submittal" + "Documentation" groups,
including DetailMaker, SheetIndexMaker, etc.

This module runs inside GH/Rhino (uses Rhino layout API).

Usage:
    from iw_product.submittal_maker import make_submittal
    result = make_submittal(config, grid, faces, naming)
"""

import Rhino
import Rhino.Geometry as rg


def make_submittal(config, grid, faces, naming):
    """
    Generate submittal data for documentation.

    This creates the data needed for layout generation, but actual
    Rhino layout creation requires the DetailMaker Python scripts
    which interact directly with the Rhino document.

    Args:
        config: dict from config_loader
        grid: dict from grid
        faces: dict from panel_faces
        naming: dict from panel_naming

    Returns:
        dict with:
            sheet_data       - list of dicts per sheet
            project_info     - dict with project header data
            panel_schedule   - list of dicts per panel
            total_area_sqft  - float
    """
    product_number = config["product_number"]
    scope_name = config["scope_name"]
    material = config["material"]
    surface = config["surface"]
    style = config["style"]

    # ── Project info header ───────────────────────────────────────
    project_info = {
        "product_number": product_number,
        "scope_name": scope_name,
        "material": material,
        "surface": surface,
        "style": style,
        "qty_panels": len(grid["panel_names"]),
        "overall_width_ft": (config["qty_columns"] * config["panel_col_width"]) / 12.0,
        "overall_height_ft": (config["qty_rows"] * config["panel_row_height"]) / 12.0,
        "total_area_sqft": faces["total_area_sqft"],
    }

    # ── Panel schedule ────────────────────────────────────────────
    panel_schedule = []
    for idx, name in enumerate(naming["full_panel_names"]):
        r, c = faces["panel_row_col"][idx]
        w = faces["panel_face_widths"][idx]
        h = faces["panel_face_heights"][idx]
        area = faces["panel_areas"][idx]

        panel_schedule.append({
            "name": name,
            "short_name": naming["short_panel_names"][idx],
            "row": r,
            "col": c,
            "face_width": w,
            "face_height": h,
            "area_sqin": area,
            "area_sqft": area / 144.0,
        })

    # ── Sheet data (for layout generation) ────────────────────────
    sheet_data = []
    # One sheet per panel (typical submittal layout)
    for idx, panel in enumerate(panel_schedule):
        sheet_data.append({
            "sheet_number": idx + 1,
            "panel_name": panel["name"],
            "title": "{} - {}".format(product_number, panel["name"]),
        })

    return {
        "sheet_data": sheet_data,
        "project_info": project_info,
        "panel_schedule": panel_schedule,
        "total_area_sqft": faces["total_area_sqft"],
    }
