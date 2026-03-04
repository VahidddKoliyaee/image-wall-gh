"""
Module 15: Image Resolution
==============================
Computes the raster image resolution for panel rendering,
with auto-calculation and 500M pixel cap.

Replaces: "Image Resolution" group.

Usage:
    from iw_product.image_resolution import compute_resolution
    res = compute_resolution(panel_width, panel_height, user_resolution)
"""

import math

MAX_PIXELS = 500_000_000  # 500 megapixels cap


def compute_resolution(panel_width, panel_height, user_resolution=0, default_ppi=32):
    """
    Compute the rendering resolution (pixels per inch).

    Args:
        panel_width: float, panel width in inches
        panel_height: float, panel height in inches
        user_resolution: float, user-specified px/in (0 = auto)
        default_ppi: float, fallback resolution

    Returns:
        dict with:
            resolution    - int: final px/in
            image_width   - int: total image width in pixels
            image_height  - int: total image height in pixels
            total_pixels  - int
            was_clamped   - bool: True if resolution was reduced for pixel cap
    """
    if panel_width <= 0 or panel_height <= 0:
        return {
            "resolution": default_ppi,
            "image_width": 0,
            "image_height": 0,
            "total_pixels": 0,
            "was_clamped": False,
        }

    if user_resolution > 0:
        res = user_resolution
    else:
        # Auto: calculate max resolution within pixel cap
        res = math.sqrt(MAX_PIXELS / (panel_width * panel_height))

    # Check pixel cap
    total = panel_width * panel_height * res * res
    was_clamped = False
    if total > MAX_PIXELS:
        res = math.sqrt(MAX_PIXELS / (panel_width * panel_height))
        was_clamped = True

    res = max(1, int(res))
    img_w = int(panel_width * res)
    img_h = int(panel_height * res)

    return {
        "resolution": res,
        "image_width": img_w,
        "image_height": img_h,
        "total_pixels": img_w * img_h,
        "was_clamped": was_clamped,
    }
