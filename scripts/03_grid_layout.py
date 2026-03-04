# 03_grid_layout.py - Circle packing layout based on image pixel widths.
# Inputs: repo_root (str), widths (list), heights (list), count (int), columns_override (int)
# Outputs: origins_x, origins_y, radii, wall_width, wall_height, status

import os
import sys
import math

_repo = str(repo_root).strip().strip('"').replace("\\", "/") if repo_root else ""
_scripts_dir = os.path.join(_repo, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from utils import load_config
config = load_config(_repo)

padding = float(config.get("wall_padding_mm", 20))
min_radius = float(config.get("min_radius_mm", 20))
max_radius = float(config.get("max_radius_mm", 100))

def to_list(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    return [val]

_widths = to_list(widths)
n = len(_widths)

if n == 0:
    origins_x = []
    origins_y = []
    radii = []
    wall_width = 0
    wall_height = 0
    status = "No images"
else:
    # Map pixel widths to radii (linear scale between min and max radius)
    w_min = float(min(_widths))
    w_max = float(max(_widths))
    w_range = w_max - w_min if w_max > w_min else 1.0

    radii = []
    for w in _widths:
        t = (float(w) - w_min) / w_range
        r = min_radius + t * (max_radius - min_radius)
        radii.append(round(r, 3))

    # Sort by radius descending (pack big circles first)
    indexed = sorted(enumerate(radii), key=lambda x: -x[1])

    # Circle packing algorithm (greedy front-chain approach)
    placed_x = [0.0] * n
    placed_y = [0.0] * n
    placed_r = [0.0] * n
    placed_count = 0

    for idx, r in indexed:
        if placed_count == 0:
            # Place first circle at origin
            placed_x[idx] = padding + r
            placed_y[idx] = padding + r
            placed_r[idx] = r
            placed_count += 1
            continue

        # Try to place touching an existing circle, as close to origin as possible
        best_x = 0
        best_y = 0
        best_dist = float("inf")

        # Try positions around each already-placed circle
        for j in range(n):
            if placed_r[j] == 0:
                continue
            # Try angles around circle j
            for angle_deg in range(0, 360, 15):
                angle = math.radians(angle_deg)
                cx = placed_x[j] + (placed_r[j] + r + 2) * math.cos(angle)
                cy = placed_y[j] + (placed_r[j] + r + 2) * math.sin(angle)

                # Check no overlap with any placed circle
                overlap = False
                for k in range(n):
                    if placed_r[k] == 0:
                        continue
                    dx = cx - placed_x[k]
                    dy = cy - placed_y[k]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < (r + placed_r[k] + 1):
                        overlap = True
                        break

                if not overlap:
                    # Prefer positions closest to center
                    d = math.sqrt(cx * cx + cy * cy)
                    if d < best_dist:
                        best_dist = d
                        best_x = cx
                        best_y = cy

        placed_x[idx] = round(best_x, 3)
        placed_y[idx] = round(best_y, 3)
        placed_r[idx] = r
        placed_count += 1

    # Shift everything so minimum x,y starts at padding
    min_x = min(placed_x[i] - radii[i] for i in range(n))
    min_y = min(placed_y[i] - radii[i] for i in range(n))
    origins_x = [round(placed_x[i] - min_x + padding, 3) for i in range(n)]
    origins_y = [round(placed_y[i] - min_y + padding, 3) for i in range(n)]

    max_x = max(origins_x[i] + radii[i] for i in range(n))
    max_y = max(origins_y[i] + radii[i] for i in range(n))
    wall_width = round(max_x + padding, 3)
    wall_height = round(max_y + padding, 3)

    status = "OK: Packed {} circles, wall={}x{}mm".format(n, wall_width, wall_height)