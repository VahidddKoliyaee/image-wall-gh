"""
Module: Image Processor
========================
Reads a source image, applies preprocessing (blur, threshold, invert),
and samples brightness at perforation point locations.

Maps pixel brightness to perforation sizes for ImageLines patterns.

Uses System.Drawing in GH or Pillow standalone.

Usage:
    from iw_product.image_processor import process_image, sample_brightness
"""

import os
import math


def _load_image_dotnet(filepath):
    """Load image using System.Drawing (.NET)."""
    import System.Drawing as SD
    if not os.path.exists(filepath):
        raise FileNotFoundError("Image not found: {}".format(filepath))
    return SD.Bitmap(filepath)


def _apply_blur_dotnet(bmp, radius):
    """Apply Gaussian blur using System.Drawing (box blur approximation)."""
    import System.Drawing as SD
    import System.Drawing.Imaging as SDI

    # Simple box blur approximation: resize down then up
    if radius <= 0:
        return bmp
    w = bmp.Width
    h = bmp.Height
    small_w = max(1, w // (radius * 2))
    small_h = max(1, h // (radius * 2))

    small = SD.Bitmap(small_w, small_h)
    g = SD.Graphics.FromImage(small)
    g.InterpolationMode = SD.Drawing2D.InterpolationMode.HighQualityBilinear
    g.DrawImage(bmp, 0, 0, small_w, small_h)
    g.Dispose()

    result = SD.Bitmap(w, h)
    g2 = SD.Graphics.FromImage(result)
    g2.InterpolationMode = SD.Drawing2D.InterpolationMode.HighQualityBilinear
    g2.DrawImage(small, 0, 0, w, h)
    g2.Dispose()
    small.Dispose()

    return result


def _get_brightness_dotnet(bmp, x_frac, y_frac):
    """Get brightness (0-1) at fractional position in bitmap."""
    px = max(0, min(bmp.Width - 1, int(x_frac * bmp.Width)))
    py = max(0, min(bmp.Height - 1, int(y_frac * bmp.Height)))
    color = bmp.GetPixel(px, py)
    return color.GetBrightness()


def process_image(config):
    """
    Load and preprocess the source image.

    Args:
        config: dict with image_filepath, blur_on, blur_radius,
                threshold_overrule, threshold_value, invert_image

    Returns:
        dict with:
            bitmap      - loaded image object (System.Drawing.Bitmap or PIL.Image)
            width       - int pixel width
            height      - int pixel height
            is_loaded   - bool
            backend     - "dotnet" or "pillow"
    """
    filepath = config.get("image_filepath", "")
    if not filepath or not os.path.exists(filepath):
        return {"bitmap": None, "width": 0, "height": 0,
                "is_loaded": False, "backend": None}

    # Try System.Drawing first (GH/Rhino), fall back to Pillow
    try:
        bmp = _load_image_dotnet(filepath)
        blur_on = config.get("blur_on", False)
        blur_radius = config.get("blur_radius", 2)
        if blur_on and blur_radius > 0:
            blurred = _apply_blur_dotnet(bmp, blur_radius)
            bmp.Dispose()
            bmp = blurred
        return {
            "bitmap": bmp,
            "width": bmp.Width,
            "height": bmp.Height,
            "is_loaded": True,
            "backend": "dotnet",
        }
    except ImportError:
        pass

    # Pillow fallback
    try:
        from PIL import Image, ImageFilter
        img = Image.open(filepath).convert("L")  # grayscale
        blur_on = config.get("blur_on", False)
        blur_radius = config.get("blur_radius", 2)
        if blur_on and blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        return {
            "bitmap": img,
            "width": img.width,
            "height": img.height,
            "is_loaded": True,
            "backend": "pillow",
        }
    except ImportError:
        return {"bitmap": None, "width": 0, "height": 0,
                "is_loaded": False, "backend": None}


def sample_brightness(image_data, points, panel_bbox, config):
    """
    Sample image brightness at each perforation point location.

    Points are mapped from panel world coordinates to image pixel coordinates.

    Args:
        image_data: dict from process_image()
        points: list of (x, y) or Point3d perf locations
        panel_bbox: (x_min, y_min, x_max, y_max) panel face bounds
        config: dict with invert_image, threshold_overrule, threshold_value

    Returns:
        list of float: brightness value (0.0 to 1.0) per point
        0.0 = black (small/no perf), 1.0 = white (large perf)
        If invert_image: reversed.
    """
    if not image_data or not image_data.get("is_loaded"):
        return [0.5] * len(points)

    bmp = image_data["bitmap"]
    backend = image_data["backend"]
    invert = config.get("invert_image", False)
    threshold_on = config.get("threshold_overrule", False)
    threshold_val = config.get("threshold_value", 128)

    x_min, y_min, x_max, y_max = panel_bbox
    panel_w = x_max - x_min
    panel_h = y_max - y_min

    if panel_w <= 0 or panel_h <= 0:
        return [0.5] * len(points)

    brightness_list = []

    for pt in points:
        # Get point coordinates
        if hasattr(pt, "X"):
            px, py = pt.X, pt.Y
        else:
            px, py = pt[0], pt[1]

        # Map to 0-1 fraction within panel
        fx = (px - x_min) / panel_w
        fy = (py - y_min) / panel_h

        # Clamp
        fx = max(0.0, min(1.0, fx))
        fy = max(0.0, min(1.0, fy))

        # Image Y is typically flipped (top=0 in image, bottom=0 in Rhino)
        fy_img = 1.0 - fy

        # Sample brightness
        if backend == "dotnet":
            brightness = _get_brightness_dotnet(bmp, fx, fy_img)
        elif backend == "pillow":
            ix = max(0, min(bmp.width - 1, int(fx * bmp.width)))
            iy = max(0, min(bmp.height - 1, int(fy_img * bmp.height)))
            pixel = bmp.getpixel((ix, iy))
            brightness = pixel / 255.0
        else:
            brightness = 0.5

        # Apply threshold
        if threshold_on:
            threshold_norm = threshold_val / 255.0
            brightness = 1.0 if brightness >= threshold_norm else 0.0

        # Apply invert
        if invert:
            brightness = 1.0 - brightness

        brightness_list.append(brightness)

    return brightness_list


def brightness_to_die_size(brightness_list, min_size, max_size, available_dies=None):
    """
    Map brightness values to die sizes.

    Args:
        brightness_list: list of float (0-1)
        min_size: float, minimum die diameter
        max_size: float, maximum die diameter
        available_dies: list of float, snap to nearest (optional)

    Returns:
        list of float: die diameter per point
    """
    diameters = []
    for b in brightness_list:
        # Linear map: 0 brightness = min_size, 1 brightness = max_size
        d = min_size + b * (max_size - min_size)

        # Snap to nearest available die if provided
        if available_dies:
            d = min(available_dies, key=lambda x: abs(x - d))

        diameters.append(d)

    return diameters