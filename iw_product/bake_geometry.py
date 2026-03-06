"""
Module 20: Bake Geometry
==========================
Bakes panel geometry to Rhino document with proper layers,
names, attributes, and line weights.

Usage:
    from iw_product.bake_geometry import bake_panels
    result = bake_panels(config, grid, naming, unfold, perf_data, run=True)
"""

import Rhino
import Rhino.Geometry as rg
import Rhino.DocObjects as rd


def _ensure_layer(layer_name, color=None):
    doc = Rhino.RhinoDoc.ActiveDoc
    layer_idx = doc.Layers.FindByFullPath(layer_name, -1)
    if layer_idx < 0:
        layer = rd.Layer()
        layer.Name = layer_name
        if color:
            import System.Drawing as SD
            layer.Color = SD.Color.FromArgb(color[0], color[1], color[2])
        layer_idx = doc.Layers.Add(layer)
    return layer_idx


def bake_panels(config, grid, naming, unfold=None, perf_data=None, run=False):
    """
    Bake panel geometry to the Rhino document.
    """
    if not run:
        return {"success": False, "baked_count": 0, "layer_names": []}

    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return {"success": False, "baked_count": 0, "layer_names": []}

    product = config["product_number"]
    line_weight = config.get("line_weight", 2)
    do_area = config.get("area_calculation", True)
    layer_names = []
    baked = 0

    # ── Panel boundaries ──────────────────────────────────────────
    bl_name = "{}_Panel_Boundaries".format(product)
    bl_idx = _ensure_layer(bl_name, (0, 0, 255))
    layer_names.append(bl_name)

    for idx, curve in enumerate(grid["panel_boundaries"]):
        attrs = rd.ObjectAttributes()
        attrs.LayerIndex = bl_idx
        attrs.Name = naming["full_panel_names"][idx]
        attrs.PlotWeight = line_weight
        doc.Objects.AddCurve(curve, attrs)
        baked += 1

    # ── Panel faces ───────────────────────────────────────────────
    fl_name = "{}_Panel_Faces".format(product)
    fl_idx = _ensure_layer(fl_name, (0, 200, 0))
    layer_names.append(fl_name)

    for idx, curve in enumerate(grid["panel_face_grids"]):
        attrs = rd.ObjectAttributes()
        attrs.LayerIndex = fl_idx
        attrs.Name = naming["full_panel_names"][idx]
        attrs.PlotWeight = line_weight
        doc.Objects.AddCurve(curve, attrs)
        baked += 1

    # ── Unfold ────────────────────────────────────────────────────
    if unfold and unfold.get("unfold_curves"):
        ul_name = "{}_Unfold".format(product)
        ul_idx = _ensure_layer(ul_name, (200, 0, 200))
        layer_names.append(ul_name)

        curves = naming.get("rotated_curves") or unfold["unfold_curves"]
        for idx, curve in enumerate(curves):
            if curve:
                attrs = rd.ObjectAttributes()
                attrs.LayerIndex = ul_idx
                attrs.Name = naming["full_panel_names"][idx]
                attrs.PlotWeight = line_weight
                doc.Objects.AddCurve(curve, attrs)
                baked += 1

    # ── Perforations ──────────────────────────────────────────────
    if perf_data and perf_data.get("perf_points"):
        pl_name = "{}_Perforations".format(product)
        pl_idx = _ensure_layer(pl_name, (255, 0, 0))
        layer_names.append(pl_name)

        pts = perf_data["perf_points"]
        radii = perf_data.get("die_radii", [])

        for i, pt in enumerate(pts):
            r = radii[i] if i < len(radii) else 0.1
            circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), r)
            attrs = rd.ObjectAttributes()
            attrs.LayerIndex = pl_idx
            attrs.PlotWeight = line_weight
            doc.Objects.AddCircle(circle, attrs)
            baked += 1

    # ── Panel name text dots ──────────────────────────────────────
    if naming.get("name_planes"):
        nl_name = "{}_Panel_Names".format(product)
        nl_idx = _ensure_layer(nl_name, (0, 0, 0))
        layer_names.append(nl_name)

        for idx, plane in enumerate(naming["name_planes"]):
            name = naming["full_panel_names"][idx]
            dot = rg.TextDot(name, plane.Origin)
            attrs = rd.ObjectAttributes()
            attrs.LayerIndex = nl_idx
            attrs.Name = name
            doc.Objects.AddTextDot(dot, attrs)
            baked += 1

    # ── Area calculation annotation ───────────────────────────────
    if do_area and grid.get("panel_face_grids"):
        total_area = 0
        for face in grid["panel_face_grids"]:
            bb = face.GetBoundingBox(True)
            w = bb.Max.X - bb.Min.X
            h = bb.Max.Y - bb.Min.Y
            total_area += w * h
        total_sqft = total_area / 144.0
        # Add as text dot at origin
        attrs = rd.ObjectAttributes()
        attrs.Name = "Total Area: {:.1f} sq ft".format(total_sqft)
        dot = rg.TextDot(attrs.Name, rg.Point3d(0, -5, 0))
        doc.Objects.AddTextDot(dot, attrs)
        baked += 1

    doc.Views.Redraw()

    return {
        "success": True,
        "baked_count": baked,
        "layer_names": layer_names,
    }