"""
GH Wrapper: Grid Parameters
Paste into a GhPython 3 component.

INPUTS:
    RepoPath : str  - Path to IMAGE-WALL-GH repo
    Done     : bool - Wire from gh_01 Done output

OUTPUTS:
    Done2    : bool - True when grid params are computed
"""

import sys
import os

Done2 = False

if not Done:
    print("Waiting for gh_01 to finish")
else:
    rp = str(RepoPath)
    if rp not in sys.path:
        sys.path.insert(0, rp)

    # Do NOT reimport shared — we need the same instance that gh_01 wrote to
    # Only reimport the grid_params module
    if "iw_product.grid_params" in sys.modules:
        del sys.modules["iw_product.grid_params"]

    from iw_product import shared
    from iw_product.grid_params import compute_grid_params

    config = shared.get("config")
    if not config or not isinstance(config, dict):
        print("ERROR: Config not found. Check gh_01.")
        print("shared._store keys: {}".format(list(shared._store.keys())))
    else:
        gp = compute_grid_params(config)
        shared.put("grid_params", gp)
        Done2 = True

        print("Style: {} (idx={}, vert={})".format(
            config["style"], gp["style_index"], gp["vertical"]))
        print("Panel face: {:.2f} x {:.2f}".format(
            gp["panel_face_width"], gp["panel_face_height"]))
        print("Pt grid: {} x {}".format(
            gp["qty_pt_grid_cols"], gp["qty_pt_grid_rows"]))
        print("True spacing: {:.4f} x {:.4f}".format(
            gp["true_grid_col_spacing"], gp["true_grid_row_spacing"]))