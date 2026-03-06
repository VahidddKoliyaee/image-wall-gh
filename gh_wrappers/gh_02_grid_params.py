"""
GH Wrapper: Grid Parameters
Paste into a GhPython 3 component.

INPUTS:
    RepoPath  : str - Path to IMAGE-WALL-GH repo
    ConfigKey : str - Key from gh_01 ("iw_config")

OUTPUTS:
    GridKey   : str - Key to retrieve grid params ("iw_grid_params")
"""

import sys
import os
import scriptcontext as sc

GridKey = ""

if not ConfigKey:
    print("Waiting for ConfigKey from gh_01")
else:
    config = sc.sticky.get(str(ConfigKey))
    if not config or not isinstance(config, dict):
        print("ERROR: Config not found in sticky. Run gh_01 first.")
    elif not RepoPath:
        print("ERROR: Set RepoPath")
    else:
        rp = str(RepoPath)
        if rp not in sys.path:
            sys.path.insert(0, rp)

        for mod in list(sys.modules):
            if mod.startswith("iw_product"):
                del sys.modules[mod]

        from iw_product.grid_params import compute_grid_params
        gp = compute_grid_params(config)

        sc.sticky["iw_grid_params"] = gp
        GridKey = "iw_grid_params"

        print("Style: {} (idx={}, vert={})".format(
            config["style"], gp["style_index"], gp["vertical"]))
        print("Panel face: {:.2f} x {:.2f}".format(
            gp["panel_face_width"], gp["panel_face_height"]))
        print("Pt grid: {} x {}".format(
            gp["qty_pt_grid_cols"], gp["qty_pt_grid_rows"]))
        print("True spacing: {:.4f} x {:.4f}".format(
            gp["true_grid_col_spacing"], gp["true_grid_row_spacing"]))
        print("Stored in sticky['iw_grid_params']")