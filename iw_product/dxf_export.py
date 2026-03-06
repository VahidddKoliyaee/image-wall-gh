"""
Module: DXF Export
===================
Exports panel flat patterns and perforation geometry to DXF files
for CNC machines.

Replaces: dxf, FileType data flow.

Usage:
    from iw_product.dxf_export import export_dxf
"""

import os

try:
    import Rhino
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def export_dxf(output_folder, naming, unfold, final_perf, scribe_data=None,
               fastener_data=None, file_type="dxf"):
    """
    Export each panel as a separate DXF file.

    Args:
        output_folder: str, folder to save DXF files
        naming: dict from panel_naming
        unfold: dict from panel_unfold
        final_perf: dict from fastener_clearance
        scribe_data: dict from scribe (optional)
        fastener_data: dict from fastener_geometry (optional)
        file_type: str, "dxf" or "dwg"

    Returns:
        dict with:
            exported_files - list of str file paths
            success        - bool
            message        - str
    """
    if not HAS_RHINO:
        return {"exported_files": [], "success": False, "message": "Requires Rhino"}

    if not output_folder:
        return {"exported_files": [], "success": False, "message": "No output folder"}

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    doc = Rhino.RhinoDoc.ActiveDoc
    exported_files = []
    names = naming.get("full_panel_names", [])
    curves = naming.get("rotated_curves") or unfold.get("unfold_curves", [])

    for idx, (name, curve) in enumerate(zip(names, curves)):
        if curve is None:
            continue

        # Create temporary objects for export
        obj_ids = []

        # Panel outline
        oid = doc.Objects.AddCurve(curve)
        if oid:
            obj_ids.append(oid)

        # Perforations for this panel
        if final_perf:
            panel_idx_list = final_perf.get("perf_panel_index", [])
            pts = final_perf.get("perf_points", [])
            radii = final_perf.get("die_radii", [])
            for i, pt in enumerate(pts):
                if i < len(panel_idx_list) and panel_idx_list[i] == idx:
                    r = radii[i] if i < len(radii) else 0.1
                    circle = rg.Circle(rg.Plane(pt, rg.Vector3d.ZAxis), r)
                    oid = doc.Objects.AddCircle(circle)
                    if oid:
                        obj_ids.append(oid)

        # Fastener holes for this panel
        if fastener_data and idx < len(fastener_data.get("connection_by_panel", [])):
            panel_fasteners = fastener_data["connection_by_panel"][idx]
            fdia = fastener_data.get("fastener_hole_dia", 0.25)
            for fp in panel_fasteners:
                circle = rg.Circle(rg.Plane(fp, rg.Vector3d.ZAxis), fdia / 2.0)
                oid = doc.Objects.AddCircle(circle)
                if oid:
                    obj_ids.append(oid)

        # Select objects and export
        if obj_ids:
            safe_name = name.replace("/", "_").replace("\\", "_")
            ext = "dxf" if file_type.lower() == "dxf" else "dwg"
            filepath = os.path.join(output_folder, "{}.{}".format(safe_name, ext))

            # Select only our objects
            doc.Objects.UnselectAll()
            for oid in obj_ids:
                doc.Objects.Select(oid)

            # Export selected
            cmd = '-_Export "{}" _Enter'.format(filepath)
            Rhino.RhinoApp.RunScript(cmd, False)
            exported_files.append(filepath)

            # Delete temporary objects
            for oid in obj_ids:
                doc.Objects.Delete(oid, True)

    return {
        "exported_files": exported_files,
        "success": len(exported_files) > 0,
        "message": "{} files exported".format(len(exported_files)),
    }
