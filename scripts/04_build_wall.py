"""
04_build_wall.py — Build Rhino geometry for the image wall.

=== GRASSHOPPER COMPONENT SETUP ===
Inputs:
    repo_root    (str)
    image_paths  (list)
    origins_x    (list)
    origins_y    (list)
    cell_widths  (list)
    cell_heights (list)
    wall_width   (float)
    wall_height  (float)
Outputs:
    frames       (list)  - Rectangle curves for each image cell
    bg_surface   (srf)   - Background surface
    picture_frames (list) - PictureFrame objects (surfaces with textures)
    labels       (list)  - Text labels (filenames)
    status       (str)
"""

import os
import sys
import Rhino.Geometry as rg
import scriptcontext as sc

_repo = str(repo_root).strip().strip('"') if repo_root else ""
_scripts_dir = os.path.join(_repo, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from utils import load_config
config = load_config(_repo)

border_w = float(config.get("border_width_mm", 2))

frames = []
picture_frames = []
labels = []

n = len(image_paths) if image_paths else 0

# Background surface
if wall_width and wall_height:
    ww = float(wall_width)
    wh = float(wall_height)
    bg_plane = rg.Plane.WorldXY
    bg_interval_x = rg.Interval(0, ww)
    bg_interval_y = rg.Interval(0, wh)
    bg_surface = rg.PlaneSurface(bg_plane, bg_interval_x, bg_interval_y)
else:
    bg_surface = None

for i in range(n):
    x = float(origins_x[i])
    y = float(origins_y[i])
    w = float(cell_widths[i])
    h = float(cell_heights[i])
    img_path = str(image_paths[i])

    # Create rectangle frame
    corner = rg.Point3d(x, y, 0)
    plane = rg.Plane(corner, rg.Vector3d.ZAxis)
    rect = rg.Rectangle3d(plane, w, h)
    frames.append(rect.ToNurbsCurve())

    # Create PictureFrame (textured surface)
    try:
        pf_plane = rg.Plane(corner, rg.Vector3d.XAxis, rg.Vector3d.YAxis)
        pf = sc.doc.Objects.AddPictureFrame(pf_plane, img_path, False, w, h, False, False)
        if pf:
            picture_frames.append(pf)
    except Exception as e:
        # Fallback: plain surface
        srf = rg.PlaneSurface(
            rg.Plane(corner, rg.Vector3d.ZAxis),
            rg.Interval(0, w),
            rg.Interval(0, h)
        )
        picture_frames.append(srf)

    # Label (filename without extension)
    fname = os.path.splitext(os.path.basename(img_path))[0]
    labels.append(fname)

status = "OK: Built {} frames".format(n)