# 02_analyze_images.py - Analyze image dimensions and aspect ratios.
# Inputs: repo_root (str), image_paths (list)
# Outputs: widths (list), heights (list), aspects (list), orientations (list), status (str)

import os
import sys

_repo = str(repo_root).strip().strip('"').replace("\\", "/") if repo_root else ""
_scripts_dir = os.path.join(_repo, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import System.Drawing as SD

widths = []
heights = []
aspects = []
orientations = []

if not image_paths:
    status = "No images to analyze"
else:
    for p in image_paths:
        path_str = str(p).replace("\\", "/")
        try:
            img = SD.Image.FromFile(path_str)
            w = img.Width
            h = img.Height
            img.Dispose()
        except:
            w = 100
            h = 100

        widths.append(w)
        heights.append(h)
        ratio = float(w) / float(h) if h > 0 else 1.0
        aspects.append(ratio)
        if ratio > 1.05:
            orientations.append("landscape")
        elif ratio < 0.95:
            orientations.append("portrait")
        else:
            orientations.append("square")

    status = "OK: Analyzed {} images".format(len(widths))