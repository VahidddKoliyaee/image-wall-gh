"""
Module 13: Drop Locks
======================
Adds drop lock hardware (block instances) at connection points.
Supports loading blocks from an external file path.

Usage:
    from iw_product.drop_locks import add_drop_locks
    locks = add_drop_locks(config, grid_params, grid, faces)
"""

try:
    import Rhino
    import Rhino.Geometry as rg
    HAS_RHINO = True
except ImportError:
    HAS_RHINO = False


def _find_block(block_name, block_file_path=None):
    """Find a block definition by name. Optionally import from file."""
    if not HAS_RHINO:
        return None
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc:
        return None

    idef_table = doc.InstanceDefinitions
    for i in range(idef_table.Count):
        idef = idef_table[i]
        if idef and not idef.IsDeleted and idef.Name == block_name:
            return idef

    # If not found and file path provided, try importing
    if block_file_path:
        import os
        if os.path.exists(block_file_path):
            # Import blocks from 3dm file
            try:
                import_opts = Rhino.FileIO.FileReadOptions()
                import_opts.ImportMode = True
                Rhino.RhinoDoc.ActiveDoc.ReadFile(block_file_path, import_opts)
                # Try again
                for i in range(idef_table.Count):
                    idef = idef_table[i]
                    if idef and not idef.IsDeleted and idef.Name == block_name:
                        return idef
            except:
                pass

    return None


def add_drop_locks(config, grid_params, grid, faces):
    """
    Place drop lock block instances at connection points.
    """
    block_name = "Standard Drop Lock Blocks"
    block_file_path = config.get("drop_lock_block_path", "")
    connection_pts = faces["connection_points"]
    is_droplock = grid_params["is_droplock"]

    if not is_droplock or not connection_pts:
        return {
            "lock_planes": [], "lock_xforms": [],
            "block_name": block_name, "block_found": False, "lock_count": 0,
        }

    block_def = _find_block(block_name, block_file_path) if HAS_RHINO else None
    block_found = block_def is not None

    lock_planes = []
    lock_xforms = []

    for pt in connection_pts:
        if HAS_RHINO:
            plane = rg.Plane(pt, rg.Vector3d.ZAxis)
            xform = rg.Transform.Translation(rg.Vector3d(pt))
        else:
            plane = pt
            xform = None
        lock_planes.append(plane)
        lock_xforms.append(xform)

    return {
        "lock_planes": lock_planes,
        "lock_xforms": lock_xforms,
        "block_name": block_name,
        "block_found": block_found,
        "lock_count": len(lock_planes),
    }