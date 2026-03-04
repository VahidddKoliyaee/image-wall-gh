"""
Module 20: Bake Geometry
==========================
Bakes panel geometry to Rhino document with proper layers,
names, and attributes for downstream fabrication workflows.

Replaces: "Bake Geometry to Rhino" + "Bake 0" + "Bake Scribe" groups.

This module runs inside GH/Rhino.

Usage:
    from iw_product.bake_geometry import bake_panels
    result = bake_panels(config, grid, naming, run=True)
"""

import Rhino
import Rhino.Geometry as rg
import Rhino.DocObjects as rd
import scriptcontext as sc


def _ensure_layer(layer_name, color=None):
    """Create a layer if it doesn't exist, return layer index."""
    doc = Rhino.RhinoDoc.ActiveDoc
    layer_idx = doc.Layers.FindByFullPath(layer_name, -1)
    if layer_idx < 0:
        layer = rd.Layer()
        layer.Name = layer_name
        if color:
            layer.Color = Rhino.Display.Color4f(
                color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, 1.0
            ).AsSystemColor()
        layer_idx = doc.Layers.Add(layer)
    return layer_idx


def bake_panels(config, grid, naming, unfold=None, perf_data=None, run=False):
    """
    Bake panel geometry to the Rhino document.

    Args:
        config: dict from config_loader
        grid: dict from grid
        naming: dict from panel_naming
        unfold: dict from panel_unfold (optional)
        perf_data: dict with perf geometry (optional)
        run: bool, trigger

    Returns:
        dict with:
            success      - bool
            baked_count  - int
            layer_names  - list of str
    """
    if not run:
        return {"success": False, "baked_count": 0, "layer_names": []}

    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return {"success": False, "baked_count": 0, "layer_names": []}

    product = config["product_number"]
    layer_names = []
    baked = 0

    # ── Panel boundaries layer ────────────────────────────────────
    boundary_layer = "{}_Panel_Boundaries".format(product)
    bl_idx = _ensure_layer(boundary_layer, (0, 0, 255))
    layer_names.append(boundary_layer)

    for idx, curve in enumerate(grid["panel_boundaries"]):
        attrs = rd.ObjectAttributes()
        attrs.LayerIndex = bl_idx
        attrs.Name = naming["full_panel_names"][idx]
        doc.Objects.AddCurve(curve, attrs)
        baked += 1

    # ── Panel face grids layer ────────────────────────────────────
    face_layer = "{}_Panel_Faces".format(product)
    fl_idx = _ensure_layer(face_layer, (0, 200, 0))
    layer_names.append(face_layer)

    for idx, curve in enumerate(grid["panel_face_grids"]):
        attrs = rd.ObjectAttributes()
        attrs.LayerIndex = fl_idx
        attrs.Name = naming["full_panel_names"][idx]
        doc.Objects.AddCurve(curve, attrs)
        baked += 1

    # ── Unfold layer ──────────────────────────────────────────────
    if unfold and unfold.get("unfold_curves"):
        unfold_layer = "{}_Unfold".format(product)
        ul_idx = _ensure_layer(unfold_layer, (200, 0, 200))
        layer_names.append(unfold_layer)

        curves = (naming.get("rotated_curves") or unfold["unfold_curves"])
        for idx, curve in enumerate(curves):
            attrs = rd.ObjectAttributes()
            attrs.LayerIndex = ul_idx
            attrs.Name = naming["full_panel_names"][idx]
            doc.Objects.AddCurve(curve, attrs)
            baked += 1

    # ── Perforation circles layer ─────────────────────────────────
    if perf_data and perf_data.get("perf_points"):
        perf_layer = "{}_Perforations".format(product)
        pl_idx = _ensure_layer(perf_layer, (255, 0, 0))
        layer_names.append(perf_layer)

        pts = perf_data["perf_points"]
        radii = perf_data.get("die_radii", [])

        for i, pt in enumerate(pts):
            r = radii[i] if i < len(radii) else 0.1
            circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), r)
            attrs = rd.ObjectAttributes()
            attrs.LayerIndex = pl_idx
            doc.Objects.AddCircle(circle, attrs)
            baked += 1

    doc.Views.Redraw()

    return {
        "success": True,
        "baked_count": baked,
        "layer_names": layer_names,
    }
