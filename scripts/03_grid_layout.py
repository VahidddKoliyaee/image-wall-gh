"""
03_grid_layout.py — Compute 2D grid positions for the image wall.

=== GRASSHOPPER COMPONENT SETUP ===
Inputs:
    repo_root   (str)   - Repo root path
    aspects     (list)  - Aspect ratios from 02_analyze_images
    count       (int)   - Number of images
    columns_override (int) - Optional column count override (0 = use config)
Outputs:
    origins_x   (list)  - X coordinates of each cell origin (bottom-left)
    origins_y   (list)  - Y coordinates of each cell origin (bottom-left)
    cell_widths (list)  - Width of each cell in mm
    cell_heights(list)  - Height of each cell in mm
    wall_width  (float) - Total wall width
    wall_height (float) - Total wall height
    status      (str)
"""

import os
import sys
import math

_repo = str(repo_root).strip().strip('"') if repo_root else ""
_scripts_dir = os.path.join(_repo, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from utils import load_config

config = load_config(_repo)

cols = int(columns_override) if columns_override and int(columns_override) > 0 else config["grid_columns"]
cell_w = float(config["cell_width_mm"])
spacing = float(config["cell_spacing_mm"])
padding = float(config.get("wall_padding_mm", 20))
keep_aspect = config["maintain_aspect_ratio"]

n = int(count) if count else 0

if n == 0:
    origins_x = []
    origins_y = []
    cell_widths = []
    cell_heights = []
    wall_width = 0
    wall_height = 0
    status = "No images"
else:
    rows = int(math.ceil(float(n) / float(cols)))

    origins_x = []
    origins_y = []
    cell_widths = []
    cell_heights = []

    for i in range(n):
        col = i % cols
        row = rows - 1 - (i // cols)  # top-to-bottom, row 0 at top

        x = padding + col * (cell_w + spacing)

        if keep_aspect and i < len(aspects):
            ar = float(aspects[i])
            cell_h = cell_w / ar if ar > 0 else cell_w
        else:
            cell_h = cell_w  # square fallback

        # For uniform row height, use max height in that row
        y = padding + row * (cell_w + spacing)  # simplified uniform grid

        origins_x.append(round(x, 3))
        origins_y.append(round(y, 3))
        cell_widths.append(round(cell_w, 3))
        cell_heights.append(round(cell_h, 3))

    wall_width = round(padding * 2 + cols * cell_w + (cols - 1) * spacing, 3)
    wall_height = round(padding * 2 + rows * cell_w + (rows - 1) * spacing, 3)
    status = "OK: {}x{} grid, wall={}x{}mm".format(cols, rows, wall_width, wall_height)