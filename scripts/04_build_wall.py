# 04_build_wall.py - Build circle geometry for the image wall.
# Inputs: repo_root, image_paths, origins_x, origins_y, radii, wall_width, wall_height
# Outputs: frames, bg_surface, labels, status

import os
import sys
import Rhino.Geometry as rg

_repo = str(repo_root).strip().strip('"').replace("\\", "/") if repo_root else ""
_scripts_dir = os.path.join(_repo, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from utils import load_config
config = load_config(_repo)

def to_list(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    return [val]

_image_paths = to_list(image_paths)
_origins_x = to_list(origins_x)
_origins_y = to_list(origins_y)
_radii = to_list(radii)

frames = []
labels = []

n = len(_image_paths)

# Background surface
if wall_width and wall_height:
    ww = float(wall_width)
    wh = float(wall_height)
    bg_surface = rg.PlaneSurface(
        rg.Plane.WorldXY,
        rg.Interval(0, ww),
        rg.Interval(0, wh)
    )
else:
    bg_surface = None

for i in range(n):
    x = float(_origins_x[i])
    y = float(_origins_y[i])
    r = float(_radii[i])
    img_path = str(_image_paths[i])

    # Create circle at center point
    center = rg.Point3d(x, y, 0)
    circle = rg.Circle(center, r)
    frames.append(circle.ToNurbsCurve())

    # Label
    fname = os.path.splitext(os.path.basename(img_path))[0]
    labels.append(fname)

status = "OK: Built {} circles".format(n)