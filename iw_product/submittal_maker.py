"""
Module 18: Submittal Maker
============================
Generates submittal documentation layouts.
Includes download URL generation and area calculations.

Usage:
    from iw_product.submittal_maker import make_submittal
    result = make_submittal(config, grid, faces, naming)
"""

try:
    import Rhino
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def make_submittal(config, grid, faces, naming):
    """
    Generate submittal data for documentation.
    """
    product_number = config["product_number"]
    scope_name = config["scope_name"]
    material = config["material"]
    surface = config["surface"]
    style = config["style"]
    do_area = config.get("area_calculation", True)

    # ── Project info ──────────────────────────────────────────────
    overall_w_ft = (config["qty_columns"] * config["panel_col_width"]) / 12.0
    overall_h_ft = (config["qty_rows"] * config["panel_row_height"]) / 12.0

    project_info = {
        "product_number": product_number,
        "scope_name": scope_name,
        "material": material,
        "surface": surface,
        "style": style,
        "qty_panels": len(grid["panel_names"]),
        "overall_width_ft": overall_w_ft,
        "overall_height_ft": overall_h_ft,
        "total_area_sqft": faces["total_area_sqft"],
        "image_edited_url": config.get("image_edited_url", ""),
        "image_highres_url": config.get("image_highres_url", ""),
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

    # ── Sheet data ────────────────────────────────────────────────
    sheet_data = []
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


def open_download_url(url):
    """Open a download URL in the default browser."""
    if not url:
        return False
    try:
        import webbrowser
        webbrowser.open_new_tab(url)
        return True
    except:
        return False