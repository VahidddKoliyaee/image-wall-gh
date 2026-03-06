"""
Module: Scribe
===============
Generates scribe/engraving marks for panel identification on CNC.
These are light etching marks that identify panel names, orientation,
and alignment points.

Replaces: Bake Scribe? toggle and scribe geometry generation.

Usage:
    from iw_product.scribe import generate_scribe_marks
"""

try:
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def generate_scribe_marks(config, grid, naming, unfold):
    """
    Generate scribe mark geometry for CNC engraving.

    Scribe marks include:
    - Panel name text location
    - Orientation arrow
    - Alignment crosshairs at corners

    Args:
        config: dict from config_loader
        grid: dict from grid
        naming: dict from panel_naming
        unfold: dict from panel_unfold

    Returns:
        dict with:
            scribe_curves  - list of Curve
            scribe_text    - list of (text, plane) tuples
            scribe_points  - list of Point3d
            bake_scribe    - bool
    """
    if not HAS_RHINO:
        return {"scribe_curves": [], "scribe_text": [], "scribe_points": [], "bake_scribe": False}

    scribe_curves = []
    scribe_text = []
    scribe_points = []

    curves = naming.get("rotated_curves") or unfold.get("unfold_curves", [])
    names = naming.get("full_panel_names", [])

    for idx, curve in enumerate(curves):
        if curve is None:
            continue

        bb = curve.GetBoundingBox(True)
        cx = (bb.Min.X + bb.Max.X) / 2.0
        cy = (bb.Min.Y + bb.Max.Y) / 2.0

        # Panel name text position (center of panel, slightly offset)
        text_pt = rg.Point3d(cx, cy - 1.0, 0)
        text_plane = rg.Plane(text_pt, rg.Vector3d.ZAxis)
        name = names[idx] if idx < len(names) else "P{}".format(idx)
        scribe_text.append((name, text_plane))

        # Orientation arrow (small arrow pointing up/right)
        arrow_base = rg.Point3d(cx, cy + 0.5, 0)
        arrow_tip = rg.Point3d(cx, cy + 1.5, 0)
        arrow_line = rg.LineCurve(arrow_base, arrow_tip)
        scribe_curves.append(arrow_line)

        # Arrow head
        head_l = rg.LineCurve(arrow_tip, rg.Point3d(cx - 0.25, cy + 1.2, 0))
        head_r = rg.LineCurve(arrow_tip, rg.Point3d(cx + 0.25, cy + 1.2, 0))
        scribe_curves.append(head_l)
        scribe_curves.append(head_r)

        # Corner crosshairs (small + marks at panel corners)
        cross_size = 0.25
        corners = [
            rg.Point3d(bb.Min.X, bb.Min.Y, 0),
            rg.Point3d(bb.Max.X, bb.Min.Y, 0),
            rg.Point3d(bb.Max.X, bb.Max.Y, 0),
            rg.Point3d(bb.Min.X, bb.Max.Y, 0),
        ]
        for corner in corners:
            h_line = rg.LineCurve(
                rg.Point3d(corner.X - cross_size, corner.Y, 0),
                rg.Point3d(corner.X + cross_size, corner.Y, 0))
            v_line = rg.LineCurve(
                rg.Point3d(corner.X, corner.Y - cross_size, 0),
                rg.Point3d(corner.X, corner.Y + cross_size, 0))
            scribe_curves.append(h_line)
            scribe_curves.append(v_line)
            scribe_points.append(corner)

    return {
        "scribe_curves": scribe_curves,
        "scribe_text": scribe_text,
        "scribe_points": scribe_points,
        "bake_scribe": True,
    }
