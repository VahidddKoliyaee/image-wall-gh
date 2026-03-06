"""
Module: Structural Members
============================
Generates structural member geometry: hat channels (sticks),
hooks, and mullion profiles.

Replaces: STICKS, Add Hooks, MULLION SIZE data flow.

Usage:
    from iw_product.structural_members import generate_sticks, generate_hooks
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def parse_mullion_size(mullion_str):
    """Parse mullion size string like '2x4' -> (2.0, 4.0)."""
    if not mullion_str or mullion_str == "None":
        return (0, 0)
    try:
        parts = mullion_str.lower().split("x")
        return (float(parts[0].strip()), float(parts[1].strip()))
    except (ValueError, IndexError):
        return (0, 0)


def generate_sticks(config, grid_params, grid):
    """
    Generate structural stick (hat channel) geometry.

    Sticks run vertically or horizontally between panels,
    providing structural support for the panel system.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from grid

    Returns:
        dict with:
            stick_curves  - list of LineCurve
            stick_lengths - list of float
            stick_count   - int
    """
    if not HAS_RHINO:
        return {"stick_curves": [], "stick_lengths": [], "stick_count": 0}

    mullion_w, mullion_d = parse_mullion_size(config.get("mullion_size", ""))
    is_droplock = grid_params["is_droplock"]
    vertical = grid_params["vertical"]
    qty_cols = config["qty_columns"]
    qty_rows = config["qty_rows"]
    col_w = config["panel_col_width"]
    row_h = config["panel_row_height"]
    overall_w = grid_params["overall_width"]
    overall_h = grid_params["overall_height"]

    stick_curves = []
    stick_lengths = []

    if is_droplock and mullion_w > 0:
        # Vertical sticks at each column boundary
        for c in range(qty_cols + 1):
            x = c * col_w
            line = rg.LineCurve(
                rg.Point3d(x, 0, 0),
                rg.Point3d(x, overall_h, 0))
            stick_curves.append(line)
            stick_lengths.append(overall_h)

        # Horizontal sticks at each row boundary
        for r in range(qty_rows + 1):
            y = r * row_h
            line = rg.LineCurve(
                rg.Point3d(0, y, 0),
                rg.Point3d(overall_w, y, 0))
            stick_curves.append(line)
            stick_lengths.append(overall_w)

    return {
        "stick_curves": stick_curves,
        "stick_lengths": stick_lengths,
        "stick_count": len(stick_curves),
        "mullion_width": mullion_w,
        "mullion_depth": mullion_d,
    }


def generate_hooks(config, grid_params, grid, faces):
    """
    Generate hook hardware geometry at panel top edges.

    Hooks are used in some styles to hang panels from the structural grid.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from grid
        faces: dict from panel_faces

    Returns:
        dict with:
            hook_points   - list of Point3d
            hook_planes   - list of Plane
            hook_count    - int
            add_hooks     - bool
    """
    if not HAS_RHINO:
        return {"hook_points": [], "hook_planes": [], "hook_count": 0, "add_hooks": False}

    is_droplock = grid_params["is_droplock"]

    if not is_droplock:
        return {"hook_points": [], "hook_planes": [], "hook_count": 0, "add_hooks": False}

    hook_points = []
    hook_planes = []

    for face in grid["panel_face_grids"]:
        bb = face.GetBoundingBox(True)
        # Hooks at top edge, evenly spaced
        top_y = bb.Max.Y
        left_x = bb.Min.X
        right_x = bb.Max.X
        cx = (left_x + right_x) / 2.0

        # Two hooks per panel top edge
        pts = [
            rg.Point3d(left_x + (right_x - left_x) * 0.25, top_y, 0),
            rg.Point3d(left_x + (right_x - left_x) * 0.75, top_y, 0),
        ]
        for pt in pts:
            hook_points.append(pt)
            hook_planes.append(rg.Plane(pt, rg.Vector3d.ZAxis))

    return {
        "hook_points": hook_points,
        "hook_planes": hook_planes,
        "hook_count": len(hook_points),
        "add_hooks": True,
    }
