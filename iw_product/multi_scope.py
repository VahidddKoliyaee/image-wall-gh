"""
Module: Multi-Scope Support
==============================
Handles multiple scopes (image regions) on a single wall.
Each scope can have different images, positions, and perforation patterns.

Replaces: Multi-scope routing, SCOPE NAME, SCOPE X,Y, Number of Scopes,
Scope Alignment data flow.

Usage:
    from iw_product.multi_scope import parse_scopes, apply_scope_offset
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def parse_scopes(config):
    """
    Parse scope information from config.

    Multi-scope projects have multiple scope names and positions.
    Single-scope is the default.

    Args:
        config: dict from config_loader

    Returns:
        list of scope dicts, each with:
            name     - str scope name
            origin_x - float X offset
            origin_y - float Y offset
            index    - int scope index
    """
    scope_name = config.get("scope_name", "E1")
    scope_bot_left = config.get("scope_bot_left", "0,0")

    # Parse scope origin
    try:
        parts = scope_bot_left.split(",")
        ox = float(parts[0].strip())
        oy = float(parts[1].strip())
    except (ValueError, IndexError):
        ox, oy = 0.0, 0.0

    # For now, single scope support
    # Multi-scope would parse multiple scope names from Excel
    scopes = [{
        "name": scope_name,
        "origin_x": ox,
        "origin_y": oy,
        "index": 0,
    }]

    return scopes


def apply_scope_offset(geometry_list, scope):
    """
    Move geometry by scope offset.

    Args:
        geometry_list: list of Rhino geometry objects
        scope: scope dict from parse_scopes

    Returns:
        list of moved geometry
    """
    if not HAS_RHINO:
        return geometry_list

    ox = scope["origin_x"]
    oy = scope["origin_y"]

    if ox == 0 and oy == 0:
        return geometry_list

    vec = rg.Vector3d(ox, oy, 0)
    xform = rg.Transform.Translation(vec)

    moved = []
    for geo in geometry_list:
        if geo is not None:
            copy = geo.Duplicate()
            copy.Transform(xform)
            moved.append(copy)
        else:
            moved.append(None)

    return moved


def get_scope_boundary(scope, config):
    """
    Get the overall boundary rectangle for a scope.

    Returns:
        PolylineCurve or None
    """
    if not HAS_RHINO:
        return None

    ox = scope["origin_x"]
    oy = scope["origin_y"]
    w = config["qty_columns"] * config["panel_col_width"]
    h = config["qty_rows"] * config["panel_row_height"]

    pts = [
        rg.Point3d(ox, oy, 0),
        rg.Point3d(ox + w, oy, 0),
        rg.Point3d(ox + w, oy + h, 0),
        rg.Point3d(ox, oy + h, 0),
        rg.Point3d(ox, oy, 0),
    ]
    return rg.Polyline(pts).ToPolylineCurve()
