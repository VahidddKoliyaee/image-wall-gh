"""
GH Wrapper: Panel Faces
Paste into a GhPython 3 component.

INPUTS:
    RepoPath   : str    - Path to IMAGE-WALL-GH repo
    Config     : object - Config dict from gh_01
    GridParams : object - Grid params dict from gh_02
    Grid       : object - Grid dict from gh_03 or gh_04

OUTPUTS:
    Faces            : object
    TotalAreaSqFt    : float
    PanelRowCol      : list
    ConnectionPoints : list[Point3d]
"""

import sys, os

Faces = None
TotalAreaSqFt = 0.0
PanelRowCol = []
ConnectionPoints = []

if not Config or not GridParams or not Grid:
    print("Waiting for inputs")
elif not RepoPath or not os.path.isdir(RepoPath):
    print("ERROR: Set RepoPath")
else:
    if RepoPath not in sys.path:
        sys.path.insert(0, RepoPath)
    for mod in list(sys.modules):
        if mod.startswith("iw_product"):
            del sys.modules[mod]

    from iw_product.panel_faces import build_panel_faces
    Faces = build_panel_faces(Config, GridParams, Grid)

    TotalAreaSqFt = Faces["total_area_sqft"]
    PanelRowCol = Faces["panel_row_col"]
    ConnectionPoints = Faces["connection_points"]

    print("Total area: {:.1f} sq ft".format(TotalAreaSqFt))
    print("{} connection points".format(len(ConnectionPoints)))
    print("Corners: {}".format(Faces["corner_indices"]))
