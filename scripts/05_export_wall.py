"""
05_export_wall.py — Export the image wall to PNG/PDF.

=== GRASSHOPPER COMPONENT SETUP ===
Inputs:
    repo_root    (str)
    wall_width   (float)
    wall_height  (float)
    export_name  (str) - Optional filename (default: "wall")
    do_export    (bool) - Button toggle to trigger export
Outputs:
    output_path  (str) - Path to exported file
    status       (str)
"""

import os
import sys
import Rhino
import scriptcontext as sc

_repo = str(repo_root).strip().strip('"') if repo_root else ""
_scripts_dir = os.path.join(_repo, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from utils import load_config
config = load_config(_repo)

output_path = ""

if not do_export:
    status = "Toggle do_export to True to export"
else:
    dpi = config.get("output_dpi", 300)
    fmt = config.get("output_format", "png")
    fname = str(export_name).strip() if export_name else "wall"
    out_dir = os.path.join(_repo, "output")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    
    output_path = os.path.join(out_dir, "{}.{}".format(fname, fmt))

    # Use Rhino's ViewCapture for high-res export
    try:
        view = sc.doc.Views.ActiveView
        vp = view.ActiveViewport

        # Zoom extents
        vp.ZoomExtents()

        # Set up capture
        size_x = int(float(wall_width) * dpi / 25.4)  # mm to pixels
        size_y = int(float(wall_height) * dpi / 25.4)
        
        capture = Rhino.Display.ViewCapture()
        capture.Width = size_x
        capture.Height = size_y
        capture.ScaleScreenItems = False
        capture.DrawAxes = False
        capture.DrawGrid = False
        capture.DrawGridAxes = False
        capture.TransparentBackground = False

        bitmap = capture.CaptureToBitmap(view)
        if bitmap:
            bitmap.Save(output_path)
            bitmap.Dispose()
            status = "OK: Exported to {}".format(output_path)
        else:
            status = "ERROR: Capture returned null"
    except Exception as e:
        status = "ERROR: {}".format(str(e))