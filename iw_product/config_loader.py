"""
Module 01: Config Loader
=========================
Reads IW-Product.xlsx and returns a config dictionary.
Includes ALL inputs from the original GH definition.
Uses only Python standard library — no external dependencies.

Usage:
    from iw_product.config_loader import load_config
    config = load_config(r"C:\\path\\to\\IW-Product.xlsx")
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET

_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_int(val, default=1):
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def _safe_bool(val, default=False):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "yes", "1")
    return default


def _parse_material_thickness(material_str):
    try:
        return float(material_str.split('"')[0].strip())
    except (ValueError, IndexError):
        return 0.0


def _col_to_index(col_str):
    result = 0
    for ch in col_str.upper():
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def _parse_cell_ref(ref):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    if not m:
        return (0, 0)
    return (_col_to_index(m.group(1)), int(m.group(2)))


def _read_xlsx(path):
    sheets = {}
    with zipfile.ZipFile(path, "r") as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            with z.open("xl/sharedStrings.xml") as f:
                tree = ET.parse(f)
                for si in tree.getroot().findall(".//s:si", _NS):
                    parts = []
                    for t_el in si.findall(".//s:t", _NS):
                        if t_el.text:
                            parts.append(t_el.text)
                    strings.append("".join(parts))
        with z.open("xl/workbook.xml") as f:
            wb_tree = ET.parse(f)
        wb_ns = {
            "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        }
        sheet_elems = wb_tree.getroot().findall(".//s:sheet", wb_ns)
        rid_map = {}
        with z.open("xl/_rels/workbook.xml.rels") as f:
            rels_tree = ET.parse(f)
        for rel in rels_tree.getroot():
            rid_map[rel.get("Id", "")] = rel.get("Target", "")
        for sheet_el in sheet_elems:
            name = sheet_el.get("name", "")
            rid = sheet_el.get(
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
            target = rid_map.get(rid, "")
            if not target:
                continue
            sheet_path = "xl/" + target if not target.startswith("/") else target.lstrip("/")
            if sheet_path not in z.namelist():
                continue
            cells = {}
            with z.open(sheet_path) as f:
                sheet_tree = ET.parse(f)
            for row_el in sheet_tree.getroot().findall(".//s:row", _NS):
                for cell_el in row_el.findall("s:c", _NS):
                    ref = cell_el.get("r", "")
                    cell_type = cell_el.get("t", "")
                    v_el = cell_el.find("s:v", _NS)
                    raw = v_el.text if v_el is not None else None
                    if raw is None:
                        is_el = cell_el.find("s:is", _NS)
                        if is_el is not None:
                            t_el = is_el.find(".//s:t", _NS)
                            raw = t_el.text if t_el is not None else None
                    if raw is None:
                        continue
                    if cell_type == "s":
                        idx = int(raw)
                        val = strings[idx] if idx < len(strings) else raw
                    elif cell_type == "b":
                        val = raw == "1"
                    else:
                        try:
                            if "." in raw:
                                val = float(raw)
                            else:
                                val = int(raw)
                        except ValueError:
                            val = raw
                    col_idx, row_num = _parse_cell_ref(ref)
                    cells[(row_num, col_idx)] = val
            sheets[name] = cells
    return sheets


def _get(cells, row, col, default=None):
    return cells.get((row, col), default)


def load_config(excel_path, **overrides):
    """
    Load full project configuration from IW-Product.xlsx.

    Args:
        excel_path: Path to the Excel file.
        **overrides: Override any config value, e.g.:
            image_filepath="C:/path/to/image.jpg"
            drop_lock_block_path="C:/path/to/blocks"
            shop_template_path="C:/path/to/template.3dm"
            imagelines_die_list=[0.125, 0.25, 0.375, ...]
            blur_on=True
            blur_radius=2
            threshold_overrule=False
            threshold_value=128
            punch_use_maximizer=False
            line_weight=2
            make_image=False
            user_resolution=0

    Returns:
        dict with all project parameters.
    """
    if not excel_path or not os.path.exists(excel_path):
        raise FileNotFoundError("Excel file not found: {}".format(excel_path))

    all_sheets = _read_xlsx(excel_path)
    config = {}

    # ── IWParameters ──────────────────────────────────────────────
    ws = all_sheets.get("IWParameters", {})
    if ws:
        params = {}
        for row in range(1, 50):
            key = _get(ws, row, 0)
            val = _get(ws, row, 1)
            if key:
                params[str(key).strip()] = val

        material = str(params.get("Material", ""))
        style = str(params.get("Style", ""))

        config.update({
            # ── Project info ──────────────────────────────────────
            "product_number":       str(params.get("Product Number", "")),
            "scope_name":           str(params.get("Scope Name", "")),
            "image_name":           str(params.get("Image Name", "")),
            "scope_bot_left":       str(params.get("Scope Bot Left (X,Y)", "0,0")),

            # ── Material / Surface ────────────────────────────────
            "material":             material,
            "material_thickness":   _parse_material_thickness(material),
            "surface":              str(params.get("Surface", "")),

            # ── Style ─────────────────────────────────────────────
            "style":                style,
            "product_style":        str(params.get("Product Style", "")),

            # ── Panel dimensions ──────────────────────────────────
            "panel_row_height":     _safe_float(params.get("Panel Row Height (in)")),
            "panel_col_width":      _safe_float(params.get("Panel Column Width (in)")),
            "qty_columns":          _safe_int(params.get("QTY of Columns")),
            "qty_rows":             _safe_int(params.get("QTY of Rows")),

            # ── Image / Invert ────────────────────────────────────
            "invert_image":         _safe_bool(params.get("Invert Image")),

            # ── Grid / Perf ───────────────────────────────────────
            "grid_pattern":         str(params.get("Grid Pattern", "Default")),
            "cross_seam":           str(params.get("Cross Seam", "Default")),
            "no_perf_level":        _safe_bool(params.get("No Perforation Level")),
            "smallest_perf":        _safe_float(params.get("Smallest Perforation"), 0.1875),
            "perf_spacing":         _safe_float(params.get("Perf Spacing"), 1.0),
            "min_bridge":           _safe_float(params.get("Minimum Bridge"), 0.125),

            # ── ImageLines settings ───────────────────────────────
            "line_spacing_target":  _safe_float(params.get("Line Spacing Target"), 1.25),
            "min_bridge_along":     _safe_float(params.get("Min Bridge Along Line"), 0.25),
            "min_bridge_perp":      _safe_float(params.get("Min Bridge Perp to Line"), 0.25),
            "min_rectangle":        _safe_float(params.get("Min Rectangle"), 0.1875),
            "max_rectangle":        _safe_float(params.get("Max Rectangle"), 2.0),
            "driver_curve_1_pts":   str(params.get("Driver Curve 1 Pts", "")),
            "driver_curve_2_pts":   str(params.get("Driver Curve 2 Pts", "")),

            # ── Mullion / Color ───────────────────────────────────
            "mullion_size":         str(params.get("Mullion Size (if exist)", "")),
            "surface_rgb":          str(params.get("Surface RGB", "200,200,200")),
            "transparency":         _safe_bool(params.get("Transparency")),

            # ── Derived flags ─────────────────────────────────────
            "vertical":             "[Vertical]" in style,

            # ── Dimensions ────────────────────────────────────────
            "overall_height":       _safe_float(_get(ws, 3, 7)),
            "overall_width":        _safe_float(_get(ws, 6, 7)),
            "max_panel_length":     _safe_float(_get(ws, 10, 5), 120.0),
            "max_panel_width":      _safe_float(_get(ws, 13, 5), 40.0),
        })

    # ── IWProduct (lookups) ───────────────────────────────────────
    ws2 = all_sheets.get("IWProduct", {})
    if ws2:
        materials = []
        for row in range(3, 50):
            val = _get(ws2, row, 1)
            if val:
                materials.append(str(val))
            else:
                break
        grid_patterns = []
        for row in range(3, 50):
            val = _get(ws2, row, 3)
            if val:
                grid_patterns.append(str(val))
            else:
                break
        styles = []
        for row in range(3, 50):
            val = _get(ws2, row, 4)
            if val:
                styles.append(str(val))
            else:
                break
        panel_sizes = []
        for row in range(3, 50):
            w = _get(ws2, row, 5)
            l = _get(ws2, row, 6)
            if w and l:
                panel_sizes.append({"width": float(w), "length": float(l)})
            else:
                break
        surface_colors = {}
        for row in range(13, 60):
            name = _get(ws2, row, 14)
            rgb = _get(ws2, row, 15)
            if name and rgb:
                surface_colors[str(name)] = str(rgb)
        config["material_list"] = materials
        config["style_list"] = styles
        config["grid_pattern_list"] = grid_patterns
        config["panel_sizes"] = panel_sizes
        config["surface_colors"] = surface_colors

    # ── IW-NonUniformGrid ─────────────────────────────────────────
    ws3 = all_sheets.get("IW-NonUniformGrid", {})
    if ws3:
        nonuniform = []
        for row in range(1, 200):
            row_vals = []
            for col in range(0, 50):
                val = _get(ws3, row, col)
                if val is not None:
                    row_vals.append(val)
            if row_vals:
                nonuniform.append(row_vals)
        config["nonuniform_grid"] = nonuniform if nonuniform else None
    else:
        config["nonuniform_grid"] = None

    # ── NON-EXCEL INPUTS (set via overrides or defaults) ──────────
    # These come from GH panels, toggles, sliders — not from Excel

    # Image
    config["image_filepath"] = ""
    config["make_image"] = False
    config["user_resolution"] = 0

    # Image processing
    config["blur_on"] = False
    config["blur_radius"] = 2
    config["threshold_overrule"] = False
    config["threshold_value"] = 128

    # Punch optimization
    config["punch_use_maximizer"] = False

    # ImageLines die list (from GH panel, default Zahner inventory)
    config["imagelines_die_list"] = [
        0.125, 0.25, 0.375, 0.5, 0.625, 0.8125, 1.0, 1.25, 1.5, 1.75
    ]

    # File paths
    config["drop_lock_block_path"] = ""
    config["shop_template_path"] = ""

    # Documentation
    config["line_weight"] = 2
    config["area_calculation"] = True

    # Download URLs (set by the system after image generation)
    config["image_edited_url"] = ""
    config["image_highres_url"] = ""

    # ── Apply overrides ───────────────────────────────────────────
    for key, value in overrides.items():
        config[key] = value

    return config


def parse_rgb(rgb_string):
    """Parse '201,205,197' -> (201, 205, 197)."""
    parts = str(rgb_string).split(",")
    return (int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip()))


def parse_point_list(pts_string):
    """Parse '[-38.963,-14.963]#[-14.963,10.581]' -> [(-38.963,-14.963), ...]."""
    if not pts_string:
        return []
    points = []
    for pt_str in str(pts_string).split("#"):
        pt_str = pt_str.strip().strip("[]")
        if "," in pt_str:
            parts = pt_str.split(",")
            points.append((float(parts[0].strip()), float(parts[1].strip())))
    return points


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "IW-Product.xlsx"
    config = load_config(path)
    print("Product: {} - {}".format(config["product_number"], config["scope_name"]))
    print("Config keys: {}".format(len(config)))