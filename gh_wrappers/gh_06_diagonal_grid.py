"""
GH Wrapper: Diagonal Grid
Paste into a GhPython 3 component.

INPUTS:
    RepoPath   : str    - Path to IMAGE-WALL-GH repo
    Config     : object - Config dict
    GridParams : object - Grid params dict
    Grid       : object - Grid dict from gh_03/04

OUTPUTS:
    DiagResult    : object
    PtGridOrigins : list[Point3d]
    IsDiagonal    : bool
"""

import sys, os

DiagResult = None
PtGridOrigins = []
IsDiagonal = False

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

    from iw_product.diagonal_grid import apply_diagonal_grid
    DiagResult = apply_diagonal_grid(Config, GridParams, Grid)

    PtGridOrigins = DiagResult["pt_grid_origins"]
    IsDiagonal = DiagResult["is_diagonal"]

    print("Diagonal: {} ({} pts)".format(IsDiagonal, len(PtGridOrigins)))
