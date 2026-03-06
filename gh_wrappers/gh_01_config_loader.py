"""
GH Wrapper: Config Loader
Paste into a GhPython 3 component.

INPUTS:
    RepoPath    : str   - Path to IMAGE-WALL-GH repo
    ExcelPath   : str   - Path to IW-Product.xlsx
    RunImport   : bool  - Trigger

OUTPUTS:
    Done        : bool  - True when config is loaded
"""

import sys
import os

Done = False

if not RunImport:
    print("Standing by")
elif not RepoPath or not os.path.isdir(str(RepoPath)):
    print("ERROR: Set RepoPath to your IMAGE-WALL-GH folder")
elif not ExcelPath:
    print("ERROR: Set ExcelPath to your IW-Product.xlsx")
else:
    rp = str(RepoPath)
    if rp not in sys.path:
        sys.path.insert(0, rp)

    # Force reimport
    for mod in list(sys.modules):
        if mod.startswith("iw_product"):
            del sys.modules[mod]

    from iw_product.config_loader import load_config
    from iw_product import shared

    config = load_config(str(ExcelPath))
    shared.put("config", config)
    Done = True

    print("Loaded: {} - {}".format(config["product_number"], config["scope_name"]))
    print("Material: {} | Style: {}".format(config["material"], config["style"]))
    print("Grid: {}x{} panels, {}x{} in".format(
        config["qty_columns"], config["qty_rows"],
        config["panel_col_width"], config["panel_row_height"]))