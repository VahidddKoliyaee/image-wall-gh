"""
Module 13: Drop Locks
======================
Adds drop lock hardware (block instances) at connection points.

Replaces: "Add Drop Locks" group — InBlock component, block placement.

This module runs inside GH/Rhino.

Usage:
    from iw_product.drop_locks import add_drop_locks
    locks = add_drop_locks(config, grid_params, grid, faces)
"""

import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc


def _find_block(block_name):
    """Find a block definition by name in the current Rhino document."""
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return None
    idef_table = doc.InstanceDefinitions
    for i in range(idef_table.Count):
        idef = idef_table[i]
        if idef and not idef.IsDeleted and idef.Name == block_name:
            return idef
    return None


def add_drop_locks(config, grid_params, grid, faces):
    """
    Place drop lock block instances at connection points.

    The block "Standard Drop Lock Blocks" must exist in the Rhino document.

    Args:
        config: dict from config_loader
        grid_params: dict from grid_params
        grid: dict from uniform/nonuniform grid
        faces: dict from panel_faces

    Returns:
        dict with:
            lock_planes    - list of Plane: placement planes for blocks
            lock_xforms    - list of Transform: transforms for block insertion
            block_name     - str: name of the block definition
            block_found    - bool: whether the block was found
            lock_count     - int
    """
    block_name = "Standard Drop Lock Blocks"
    connection_pts = faces["connection_points"]
    is_droplock = grid_params["is_droplock"]

    if not is_droplock or not connection_pts:
        return {
            "lock_planes": [],
            "lock_xforms": [],
            "block_name": block_name,
            "block_found": False,
            "lock_count": 0,
        }

    block_def = _find_block(block_name)
    block_found = block_def is not None

    lock_planes = []
    lock_xforms = []

    for pt in connection_pts:
        plane = rg.Plane(pt, rg.Vector3d.ZAxis)
        lock_planes.append(plane)

        # Transform: translation to point
        xform = rg.Transform.Translation(rg.Vector3d(pt))
        lock_xforms.append(xform)

    return {
        "lock_planes": lock_planes,
        "lock_xforms": lock_xforms,
        "block_name": block_name,
        "block_found": block_found,
        "lock_count": len(lock_planes),
    }
