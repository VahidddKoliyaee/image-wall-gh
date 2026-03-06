"""
GH Wrapper: Panel Faces
Paste into a GhPython 3 component.

INPUTS:
    RepoPath : str  - Path to IMAGE-WALL-GH repo
    Done3    : bool - Wire from gh_03 Done3 output

OUTPUTS:
    Done5            : bool
    TotalAreaSqFt    : float
    ConnectionPoints : list - Point3d for fastener locations
"""

import sys
import os

Done5 = False
TotalAreaSqFt = 0.0
ConnectionPoints = []

if not Done3:
    print("Waiting for gh_03")
else:
    rp = str(RepoPath)
    if rp not in sys.path:
        sys.path.insert(0, rp)

    if "iw_product.panel_faces" in sys.modules:
        del sys.modules["iw_product.panel_faces"]

    from iw_product import shared
    from iw_product.panel_faces import build_panel_faces

    config = shared.get("config")
    grid_params = shared.get("grid_params")
    grid = shared.get("grid")

    if not config or not grid_params or not grid:
        print("ERROR: Missing data. Check previous modules.")
    else:
        faces = build_panel_faces(config, grid_params, grid)
        shared.put("faces", faces)
        Done5 = True

        TotalAreaSqFt = faces["total_area_sqft"]
        ConnectionPoints = faces["connection_points"]

        print("Total area: {:.1f} sq ft".format(TotalAreaSqFt))
        print("{} connection points".format(len(ConnectionPoints)))
        print("Face sizes: {:.2f} x {:.2f} in".format(
            faces["panel_face_widths"][0], faces["panel_face_heights"][0]))
        print("Corners: {}".format(faces["corner_indices"]))