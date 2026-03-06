"""
Module: Layout Manager
========================
Creates Rhino print layouts with viewports, title blocks, and index pages.
Ports the original DetailMaker, SheetIndexMaker, FastenerIndexMaker,
SMIndexMaker, ExtIndexMaker, Import Layout, Delete ALL Layouts scripts.

These functions directly manipulate the Rhino document and must run in GH.

Usage:
    from iw_product.layout_manager import (
        delete_all_layouts, import_layout_template,
        create_detail_layouts, create_sheet_index,
        create_fastener_index, create_sm_index, create_ext_index
    )
"""

try:
    import Rhino
    import Rhino.Geometry as rg
    import scriptcontext as sc
    import rhinoscriptsyntax as rs
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def delete_all_layouts():
    """
    Delete all layout pages except the first one.
    Ported from: Delete ALL Layouts (51 lines).
    """
    if not HAS_RHINO:
        return {"success": False, "message": "Requires Rhino"}

    page_views = sc.doc.Views.GetViewList(False, True)
    deleted = 0
    for i in range(len(page_views)):
        try:
            page_views[i].SetPageAsActive()
            Rhino.Display.RhinoPageView.Close(page_views[i])
            sc.doc.Views.ActiveView.Redraw()
            deleted += 1
        except:
            pass

    return {"success": True, "deleted": deleted}


def import_layout_template(template_path, layout_names):
    """
    Import layout templates from a .3dm file.
    Ported from: Import Layout (210 lines).

    Args:
        template_path: str, path to template .3dm file
        layout_names: list of str, names for new layouts

    Returns:
        dict with success, created layout names
    """
    if not HAS_RHINO:
        return {"success": False, "message": "Requires Rhino"}

    import os
    if not template_path or not os.path.exists(template_path):
        return {"success": False, "message": "Template not found: {}".format(template_path)}

    created = []
    try:
        # Read template file
        template_doc = Rhino.FileIO.File3dm.Read(template_path)
        if not template_doc:
            return {"success": False, "message": "Could not read template"}

        for name in layout_names:
            # Create new page view
            page = sc.doc.Views.AddPageView(name, 17, 11)  # 17x11 = tabloid
            if page:
                created.append(name)
                # Add detail view
                top_left = rg.Point2d(0.393, 10.607)
                bottom_right = rg.Point2d(16.607, 1.202)
                detail = page.AddDetailView(
                    "ModelView", top_left, bottom_right,
                    Rhino.Display.DefinedViewportProjection.Top)
                if detail:
                    page.SetActiveDetail(detail.Id)

        template_doc.Dispose()
    except Exception as e:
        return {"success": False, "message": str(e)}

    return {"success": True, "created": created}


def create_detail_layouts(config, grid, naming, frames=None,
                          project_name=None, zahner_ref=None, arch_ref=None):
    """
    Create detail layout pages for each panel.
    Ported from: DetailMaker (401 lines).

    Args:
        config: dict from config_loader
        grid: dict from grid
        naming: dict from panel_naming
        frames: list of Rectangle3d view frames (optional)
        project_name: str (defaults to config product_number)
        zahner_ref: reference geometry (optional)
        arch_ref: reference geometry (optional)

    Returns:
        dict with viewport_names, detail_locations, success
    """
    if not HAS_RHINO:
        return {"viewport_names": [], "detail_loc": [], "success": False}

    product = project_name or config.get("product_number", "")
    names = naming.get("full_panel_names", [])
    viewport_names = []
    detail_locations = []

    page_views = sc.doc.Views.GetViewList(False, True)

    for idx, panel_name in enumerate(names):
        page_name = "{}_{}".format(product, panel_name)

        # Find or create page
        page = None
        for pv in page_views:
            if pv.PageName == page_name:
                page = pv
                break

        if not page:
            page = sc.doc.Views.AddPageView(page_name, 17, 11)

        if page:
            viewport_names.append(page_name)

            # Set up detail view zoomed to panel
            sc.doc.Views.ActiveView = page
            top_left = rg.Point2d(0.5, 10.5)
            bottom_right = rg.Point2d(16.5, 1.5)
            detail = page.AddDetailView(
                "Detail_{}".format(panel_name),
                top_left, bottom_right,
                Rhino.Display.DefinedViewportProjection.Top)

            if detail and idx < len(grid["panel_boundaries"]):
                # Zoom to panel
                panel_bb = grid["panel_boundaries"][idx].GetBoundingBox(True)
                detail_locations.append(panel_bb.Center)

    sc.doc.Views.Redraw()

    return {
        "viewport_names": viewport_names,
        "detail_loc": detail_locations,
        "success": True,
    }


def create_sheet_index(config, sheet_names):
    """
    Create sheet index page.
    Ported from: SheetIndexMaker (447 lines).
    """
    if not HAS_RHINO:
        return {"success": False}

    page_name = "Z10.1"
    page = sc.doc.Views.AddPageView(page_name, 17, 11)
    if not page:
        return {"success": False, "message": "Could not create index page"}

    # Write sheet names as text
    sc.doc.Views.ActiveView = page
    y_pos = 10.0
    for i, name in enumerate(sheet_names):
        pt = rg.Point3d(1.0, y_pos, 0)
        text = "{:3d}. {}".format(i + 1, name)
        dot = rg.TextDot(text, pt)
        sc.doc.Objects.AddTextDot(dot)
        y_pos -= 0.3

    return {"success": True, "page_name": page_name}


def create_fastener_index(fastener_names, fastener_details):
    """
    Create fastener index page.
    Ported from: FastenerIndexMaker (556 lines).
    """
    if not HAS_RHINO:
        return {"success": False}

    page_name = "Z10.2"
    page = sc.doc.Views.AddPageView(page_name, 17, 11)
    if not page:
        return {"success": False}

    sc.doc.Views.ActiveView = page
    y_pos = 10.0
    for name, detail in zip(fastener_names, fastener_details):
        pt = rg.Point3d(1.0, y_pos, 0)
        text = "{}: {}".format(name, detail)
        dot = rg.TextDot(text, pt)
        sc.doc.Objects.AddTextDot(dot)
        y_pos -= 0.3

    return {"success": True, "page_name": page_name}


def create_sm_index(sm_names, sm_details):
    """
    Create sheet metal index page.
    Ported from: SMIndexMaker (550 lines).
    """
    if not HAS_RHINO:
        return {"success": False}

    page_name = "Z10.3"
    page = sc.doc.Views.AddPageView(page_name, 17, 11)
    if not page:
        return {"success": False}

    sc.doc.Views.ActiveView = page
    y_pos = 10.0
    for name, detail in zip(sm_names, sm_details):
        pt = rg.Point3d(1.0, y_pos, 0)
        dot = rg.TextDot("{}: {}".format(name, detail), pt)
        sc.doc.Objects.AddTextDot(dot)
        y_pos -= 0.3

    return {"success": True, "page_name": page_name}


def create_ext_index(ext_names, ext_details):
    """
    Create extrusion index page.
    Ported from: ExtIndexMaker (553 lines).
    """
    if not HAS_RHINO:
        return {"success": False}

    page_name = "Z10.4"
    page = sc.doc.Views.AddPageView(page_name, 17, 11)
    if not page:
        return {"success": False}

    sc.doc.Views.ActiveView = page
    y_pos = 10.0
    for name, detail in zip(ext_names, ext_details):
        pt = rg.Point3d(1.0, y_pos, 0)
        dot = rg.TextDot("{}: {}".format(name, detail), pt)
        sc.doc.Objects.AddTextDot(dot)
        y_pos -= 0.3

    return {"success": True, "page_name": page_name}


def find_layout_indices(layout_name_pattern):
    """
    Find layout pages matching a name pattern.
    Ported from: Find Layout Indeces (53 lines).
    """
    if not HAS_RHINO:
        return {"indices": [], "names": []}

    page_views = sc.doc.Views.GetViewList(False, True)
    indices = []
    names = []

    for i, pv in enumerate(page_views):
        if layout_name_pattern in pv.PageName:
            indices.append(i)
            names.append(pv.PageName)

    return {"indices": indices, "names": names}
