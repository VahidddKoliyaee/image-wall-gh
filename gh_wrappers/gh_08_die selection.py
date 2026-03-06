"""
GH Wrapper: Die Selection
Paste into a GhPython 3 component.

INPUTS:
    RepoPath : str  - Path to IMAGE-WALL-GH repo
    Done7    : bool - Wire from gh_07

OUTPUTS:
    Done8       : bool
    SelectedDie : float - Uniform die diameter
    DieCount    : int
"""

import sys, os

Done8 = False
SelectedDie = 0.0
DieCount = 0

if not Done7:
    print("Waiting for gh_07")
else:
    rp = str(RepoPath)
    if rp not in sys.path:
        sys.path.insert(0, rp)
    if "iw_product.die_selection" in sys.modules:
        del sys.modules["iw_product.die_selection"]

    from iw_product import shared
    from iw_product.die_selection import select_die_sizes

    config = shared.get("config")
    grid_params = shared.get("grid_params")
    pg = shared.get("point_grid")

    if not config or not grid_params or not pg:
        print("ERROR: Missing data.")
    else:
        dies = select_die_sizes(config, grid_params, pg)
        shared.put("die_data", dies)
        Done8 = True

        SelectedDie = dies["selected_die"]
        DieCount = dies["total_die_count"]

        print("Selected die: {:.4f} in".format(SelectedDie))
        print("Available dies: {}".format(
            ["{:.4f}".format(d) for d in dies["available_dies"][:8]]))
        print("{} perforations".format(DieCount))