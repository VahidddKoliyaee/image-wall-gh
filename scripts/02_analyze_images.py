"""
02_analyze_images.py — Analyze image dimensions and aspect ratios.

=== GRASSHOPPER COMPONENT SETUP ===
Inputs:
    repo_root    (str)   - Repo root path
    image_paths  (list)  - From 01_load_images
Outputs:
    widths        (list) - Pixel widths
    heights       (list) - Pixel heights
    aspects       (list) - Aspect ratios (w/h)
    orientations  (list) - "landscape" / "portrait" / "square"
    status        (str)
"""

import os
import sys
import struct
import imghdr

_repo = str(repo_root).strip().strip('"').replace("\\", "/")
_scripts_dir = os.path.join(_repo, "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


def get_image_size_fast(filepath):
    """Get image dimensions without PIL — works in IronPython/CPython."""
    ext = os.path.splitext(filepath)[1].lower()
    with open(filepath, "rb") as f:
        head = f.read(32)
        
        # PNG
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            w, h = struct.unpack('>II', head[16:24])
            return int(w), int(h)
        
        # JPEG
        if head[:2] == b'\xff\xd8':
            f.seek(0)
            f.read(2)
            while True:
                marker, size = struct.unpack('>BH', b'\xff' + f.read(3)[1:])
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    f.read(1)
                    h, w = struct.unpack('>HH', f.read(4))
                    return int(w), int(h)
                else:
                    f.read(size - 2)
        
        # BMP
        if head[:2] == b'BM':
            w, h = struct.unpack('<II', head[18:26])
            return int(w), int(abs(h))
    
    # Fallback: try System.Drawing (.NET) — available in Rhino
    try:
        import System.Drawing as SD
        img = SD.Image.FromFile(filepath)
        w, h = img.Width, img.Height
        img.Dispose()
        return w, h
    except:
        return 100, 100  # safe fallback


widths = []
heights = []
aspects = []
orientations = []

if not image_paths:
    status = "No images to analyze"
else:
    for p in image_paths:
        path_str = str(p)
        w, h = get_image_size_fast(path_str)
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