"""
01_load_images.py — Load image file paths from a folder.

=== GRASSHOPPER COMPONENT SETUP ===
Component: GhPython (Rhino 8 Script Editor or legacy GhPython)
Inputs:
    repo_root  (str)  - Panel with path to repo clone, e.g. "C:\Users\You\repos\image-wall-gh"
    img_folder (str)  - Optional override folder path. If empty, uses repo_root/images/
Outputs:
    image_paths (list) - List of full image file paths
    count       (int)  - Number of images found
    status      (str)  - Status message
"""

import os
import sys

# --- Resolve paths ---
_repo = str(repo_root).strip().strip('"').replace("\\", "/") if repo_root else ""
if not _repo:
    status = "ERROR: Set repo_root panel to your clone path"
    image_paths = []
    count = 0
else:
    # Add scripts/ to path so we can import utils
    _scripts_dir = os.path.join(_repo, "scripts")
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)

    from utils import load_config, get_image_extensions, safe_path

    config = load_config(_repo)
    extensions = get_image_extensions()

    # Determine image folder
    if img_folder and str(img_folder).strip():
        _folder = str(img_folder).strip().strip('"')
    else:
        _folder = safe_path(_repo, "images")

    if not os.path.isdir(_folder):
        status = "ERROR: Folder not found: {}".format(_folder)
        image_paths = []
        count = 0
    else:
        # Collect image files, sorted alphabetically
        image_paths = sorted([
            os.path.join(_folder, f)
            for f in os.listdir(_folder)
            if os.path.splitext(f)[1].lower() in extensions
        ])
        count = len(image_paths)
        status = "OK: Found {} images in {}".format(count, _folder)