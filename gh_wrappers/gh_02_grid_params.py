"""
GH Wrapper: Grid Parameters
Paste into a GhPython 3 component.

IMPORTANT: Right-click each input and set Type Hint to "No Type Hint"
  - RepoPath : str (Type Hint: str is fine)
  - Config   : object (Type Hint: NO TYPE HINT — not str!)

INPUTS:
    RepoPath : str    - Path to IMAGE-WALL-GH repo
    Config   : object - Config dict from gh_01_config_loader

OUTPUTS:
    GridParams : object - Full grid params dict
"""

import sys
import os

GridParams = None

if not Config:
    print("Waiting for Config input")
elif isinstance(Config, str):
    print("ERROR: Config arrived as a string, not a dict.")
    print("FIX: Right-click the Config input on this component")
    print("     -> Type Hint -> No Type Hint")
    print("     Then reconnect the wire from gh_01.")
elif not RepoPath:
    print("ERROR: Set RepoPath")
else:
    if RepoPath not in sys.path:
        sys.path.insert(0, RepoPath)

    for mod in list(sys.modules):
        if mod.startswith("iw_product"):
            del sys.modules[mod]

    from iw_product.grid_params import compute_grid_params
    GridParams = compute_grid_params(Config)

    print("Style: {} (idx={}, vert={})".format(
        Config["style"], GridParams["style_index"], GridParams["vertical"]))
    print("Panel face: {:.2f} x {:.2f}".format(
        GridParams["panel_face_width"], GridParams["panel_face_height"]))
    print("Pt grid: {} x {}".format(
        GridParams["qty_pt_grid_cols"], GridParams["qty_pt_grid_rows"]))
    print("True spacing: {:.4f} x {:.4f}".format(
        GridParams["true_grid_col_spacing"], GridParams["true_grid_row_spacing"]))