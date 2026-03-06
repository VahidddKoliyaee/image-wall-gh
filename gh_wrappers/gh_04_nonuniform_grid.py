"""
GH Wrapper: Nonuniform Grid
Paste into a GhPython 3 component.

Use this INSTEAD of gh_03 when NonUniform? is True.
Wire Done2 from gh_02 into this.

INPUTS:
    RepoPath : str  - Path to IMAGE-WALL-GH repo
    Done2    : bool - Wire from gh_02 Done2 output

OUTPUTS:
    Done4            : bool
    PanelBoundaries  : list
    PanelFaceGrids   : list
    PanelNames       : list
    PtGridOrigins    : list
    OverallBoundary  : object
"""

import sys
import os

Done4 = False
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

    if "iw_product.nonuniform_grid" in sys.modules:
        del sys.modules["iw_product.nonuniform_grid"]

    from iw_product import shared
    from iw_product.nonuniform_grid import build_nonuniform_grid

    config = shared.get("config")
    grid_params = shared.get("grid_params")

    if not config or not grid_params:
        print("ERROR: Config or GridParams not found.")
    else:
        grid = build_nonuniform_grid(config, grid_params)
        shared.put("grid", grid)
        Done4 = True

        PanelBoundaries = grid["panel_boundaries"]
        PanelFaceGrids = grid["panel_face_grids"]
        PanelNames = grid["panel_names"]
        PtGridOrigins = grid["pt_grid_origins"]
        OverallBoundary = grid["overall_boundary"]

        print("{} panels: {}".format(len(PanelNames), ", ".join(PanelNames)))
        print("{} perf grid points".format(len(PtGridOrigins)))