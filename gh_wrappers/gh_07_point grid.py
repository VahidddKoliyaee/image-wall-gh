"""
GH Wrapper: Point Grid
Paste into a GhPython 3 component.

INPUTS:
    RepoPath : str  - Path to IMAGE-WALL-GH repo
    Done6    : bool - Wire from gh_06

OUTPUTS:
    Done7         : bool
    PerfPoints    : list - Point3d perf centers
    QtyPoints     : int
"""

import sys, os

Done7 = False
PerfPoints = []
QtyPoints = 0

if not Done6:
    print("Waiting for gh_06")
else:
    rp = str(RepoPath)
    if rp not in sys.path:
        sys.path.insert(0, rp)
    if "iw_product.point_grid" in sys.modules:
        del sys.modules["iw_product.point_grid"]

    from iw_product import shared
    from iw_product.point_grid import build_point_grid

    config = shared.get("config")
    grid_params = shared.get("grid_params")
    grid = shared.get("grid")
    diag = shared.get("diag_result")

    if not config or not grid_params or not grid:
        print("ERROR: Missing data.")
    else:
        pg = build_point_grid(config, grid_params, grid, diag)
        shared.put("point_grid", pg)
        Done7 = True

        PerfPoints = pg["perf_points"]
        QtyPoints = pg["qty_points_total"]

        print("{} perf points across {} panels".format(
            QtyPoints, len(pg["points_per_panel"])))