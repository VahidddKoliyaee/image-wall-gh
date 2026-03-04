"""
GH Wrapper: Config Loader
Paste into a GhPython 3 component.

INPUTS:
    RepoPath    : str   - Path to IMAGE-WALL-GH repo
    ExcelPath   : str   - Path to IW-Product.xlsx
    RunImport   : bool  - Trigger

OUTPUTS:
    Config      : object - Full config dict
"""

import sys
import os

Config = None

if not RunImport:
    print("Standing by")
elif not RepoPath or not os.path.isdir(RepoPath):
    print("ERROR: Set RepoPath to your IMAGE-WALL-GH folder")
elif not ExcelPath:
    print("ERROR: Set ExcelPath to your IW-Product.xlsx")
else:
    if RepoPath not in sys.path:
        sys.path.insert(0, RepoPath)

    # Force reimport so repo edits are picked up
    for mod in list(sys.modules):
        if mod.startswith("iw_product"):
            del sys.modules[mod]

    from iw_product.config_loader import load_config
    Config = load_config(ExcelPath)

    print("Loaded: {} - {}".format(Config["product_number"], Config["scope_name"]))
    print("Material: {} | Style: {}".format(Config["material"], Config["style"]))
    print("Grid: {}x{} panels, {}x{} in".format(
        Config["qty_columns"], Config["qty_rows"],
        Config["panel_col_width"], Config["panel_row_height"]))
