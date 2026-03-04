"""
GH Wrapper: Nonuniform Grid
Paste into a GhPython 3 component.

INPUTS:
    RepoPath   : str    - Path to IMAGE-WALL-GH repo
    Config     : object - Config dict from gh_01
    GridParams : object - Grid params dict from gh_02

OUTPUTS:
    Grid             : object
    PanelBoundaries  : list[Curve]
    PanelFaceGrids   : list[Curve]
    PanelNames       : list[str]
    PtGridOrigins    : list[Point3d]
    OverallBoundary  : Curve
"""

import sys
import os

Grid = None
PanelBoundaries = []
PanelFaceGrids = []
PanelNames = []
PtGridOrigins = []
OverallBoundary = None

if not Config or not GridParams:
    print("Waiting for Config and GridParams")
elif not RepoPath or not os.path.isdir(RepoPath):
    print("ERROR: Set RepoPath")
else:
    if RepoPath not in sys.path:
        sys.path.insert(0, RepoPath)

    for mod in list(sys.modules):
        if mod.startswith("iw_product"):
            del sys.modules[mod]

    from iw_product.nonuniform_grid import build_nonuniform_grid
    Grid = build_nonuniform_grid(Config, GridParams)

    PanelBoundaries = Grid["panel_boundaries"]
    PanelFaceGrids = Grid["panel_face_grids"]
    PanelNames = Grid["panel_names"]
    PtGridOrigins = Grid["pt_grid_origins"]
    OverallBoundary = Grid["overall_boundary"]

    print("{} panels: {}".format(len(PanelNames), ", ".join(PanelNames)))
    print("{} perf grid points".format(len(PtGridOrigins)))
