"""
GH Wrapper: Uniform Grid
Paste into a GhPython 3 component.

INPUTS:
    RepoPath : str  - Path to IMAGE-WALL-GH repo
    Done2    : bool - Wire from gh_02 Done2 output

OUTPUTS:
    Done3            : bool
    PanelBoundaries  : list - Panel outline curves
    PanelFaceGrids   : list - Panel face curves (inset)
    PanelNames       : list - Panel name strings
    PtGridOrigins    : list - All perf grid points
    OverallBoundary  : object - Full scope outline
"""

import sys
import os

Done3 = False
PanelBoundaries = []
PanelFaceGrids = []
PanelNames = []
PtGridOrigins = []
OverallBoundary = None

if not Done2:
    print("Waiting for gh_02")
else:
    rp = str(RepoPath)
    if rp not in sys.path:
        sys.path.insert(0, rp)

    # Reimport only the module we need
    if "iw_product.uniform_grid" in sys.modules:
        del sys.modules["iw_product.uniform_grid"]

    from iw_product import shared
    from iw_product.uniform_grid import build_uniform_grid

    config = shared.get("config")
    grid_params = shared.get("grid_params")

    if not config or not grid_params:
        print("ERROR: Config or GridParams not found. Check gh_01 and gh_02.")
    else:
        grid = build_uniform_grid(config, grid_params)
        shared.put("grid", grid)
        Done3 = True

        PanelBoundaries = grid["panel_boundaries"]
        PanelFaceGrids = grid["panel_face_grids"]
        PanelNames = grid["panel_names"]
        PtGridOrigins = grid["pt_grid_origins"]
        OverallBoundary = grid["overall_boundary"]

        print("{} panels: {}".format(len(PanelNames), ", ".join(PanelNames)))
        print("{} perf grid points".format(len(PtGridOrigins)))