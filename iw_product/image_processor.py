"""
Module: Image Processor
========================
Exact port of the C# GrayScale sampler script from inside the GH cluster.

Original C# logic:
1. Load image as bitmap, convert to greyscale
2. Scan ALL pixels to find MinGrayscale and MaxGrayscale (R channel)
3. For each perforation point:
   - Map point (X,Y) world coords to image pixel coords using MappedRegion bbox
   - Sample the greyscale value at that pixel
   - Output raw greyscale value (0-255) if > MinGrayscale, else 0

Key coordinate mapping from original C#:
    pixelX = ImageWidth * (point.X - regionMin.X) / regionWidth
    pixelY = ImageHeight * (1 - (point.Y - regionMin.Y) / regionHeight)

Usage:
    from iw_product.image_processor import process_image, sample_grayscale
"""

import os

try:
    import System.Drawing as SD
    import Grasshopper as GH
    HAS_DOTNET = True
except ImportError:
    HAS_DOTNET = False


def process_image(config):
    """
    Load and preprocess source image.
    Returns image data dict for use with sample_grayscale().
    """
    filepath = config.get("image_filepath", "")
    if not filepath or not os.path.exists(filepath):
        return {"bitmap": None, "width": 0, "height": 0,
                "is_loaded": False, "backend": None,
                "min_gray": 0, "max_gray": 255, "gray_range": 256}

    # Try System.Drawing + GH_MemoryBitmap (exact match to original C#)
    if HAS_DOTNET:
        try:
            bitmap = SD.Bitmap(filepath)
            sampler = GH.GH_MemoryBitmap(bitmap)
            sampler.Filter_GreyScale()

            img_w = bitmap.Width
            img_h = bitmap.Height

            # Scan all pixels to find min/max grayscale (exactly like original C#)
            col = SD.Color.Transparent
            sampler.Sample(0, 0, col)
            min_gray = col.R
            max_gray = col.R

            for k in range(img_w + 1):
                for j in range(img_h + 1):
                    sampler.Sample(k, j, col)
                    if col.R < min_gray:
                        min_gray = col.R
                    if col.R > max_gray:
                        max_gray = col.R

            gray_range = max_gray - min_gray + 1

            return {
                "bitmap": bitmap,
                "sampler": sampler,
                "width": img_w,
                "height": img_h,
                "is_loaded": True,
                "backend": "dotnet",
                "min_gray": int(min_gray),
                "max_gray": int(max_gray),
                "gray_range": int(gray_range),
            }
        except Exception as e:
            print("System.Drawing load failed: {}".format(e))

    # Pillow fallback
    try:
        from PIL import Image, ImageFilter
        img = Image.open(filepath).convert("L")  # greyscale

        blur_on = config.get("blur_on", False)
        blur_radius = config.get("blur_radius", 2)
        if blur_on and blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        img_w, img_h = img.size
        pixels = list(img.getdata())
        min_gray = min(pixels)
        max_gray = max(pixels)
        gray_range = max_gray - min_gray + 1

        return {
            "bitmap": img,
            "sampler": None,
            "width": img_w,
            "height": img_h,
            "is_loaded": True,
            "backend": "pillow",
            "min_gray": min_gray,
            "max_gray": max_gray,
            "gray_range": gray_range,
        }
    except ImportError:
        return {"bitmap": None, "width": 0, "height": 0,
                "is_loaded": False, "backend": None,
                "min_gray": 0, "max_gray": 255, "gray_range": 256}


def sample_grayscale(image_data, pick_points, mapped_region_bbox, config):
    """
    Exact port of the C# GrayScale sampling logic.

    For each point, maps world coordinates to image pixel coordinates
    and returns the raw grayscale value.

    Args:
        image_data: dict from process_image()
        pick_points: list of Point3d or (x,y) tuples
        mapped_region_bbox: (x_min, y_min, x_max, y_max) — bounding box of the mapping region
        config: dict with invert_image, threshold settings

    Returns:
        list of float: grayscale value (0-255) per point
    """
    if not image_data or not image_data.get("is_loaded"):
        return [0.0] * len(pick_points)

    img_w = image_data["width"]
    img_h = image_data["height"]
    min_gray = image_data["min_gray"]
    max_gray = image_data["max_gray"]
    backend = image_data["backend"]
    invert = config.get("invert_image", False)

    x_min, y_min, x_max, y_max = mapped_region_bbox
    region_x = x_max - x_min  # regionx = bounds.Diagonal.X
    region_y = y_max - y_min  # regiony = bounds.Diagonal.Y

    if region_x <= 0 or region_y <= 0:
        return [0.0] * len(pick_points)

    grayscale_values = []

    for pt in pick_points:
        # Get point coords
        if hasattr(pt, "X"):
            px, py = pt.X, pt.Y
        else:
            px, py = pt[0], pt[1]

        # Original C# coordinate mapping:
        # pixelX = X * (point.X - regionmin.X) / regionx
        # pixelY = Y * (1 - (point.Y - regionmin.Y) / regiony)
        target_x = img_w * (px - x_min) / region_x
        target_y = img_h * (1.0 - (py - y_min) / region_y)

        # Sample grayscale
        gray = 0.0
        if backend == "dotnet":
            sampler = image_data.get("sampler")
            if sampler:
                col = SD.Color.Transparent
                if sampler.Sample(target_x, target_y, col):
                    raw = float(col.R)
                    if raw > min_gray:
                        gray = raw
                    else:
                        gray = 0.0
        elif backend == "pillow":
            bmp = image_data["bitmap"]
            ix = max(0, min(img_w - 1, int(target_x)))
            iy = max(0, min(img_h - 1, int(target_y)))
            raw = float(bmp.getpixel((ix, iy)))
            if raw > min_gray:
                gray = raw
            else:
                gray = 0.0

        # Apply invert
        if invert and gray > 0:
            gray = max_gray - gray + min_gray

        grayscale_values.append(gray)

    return grayscale_values


def grayscale_to_die_size(grayscale_values, min_size, max_size,
                          min_gray, max_gray, available_dies=None):
    """
    Map grayscale values (0-255) to die sizes.

    Linear mapping: min_gray → min_size, max_gray → max_size

    Args:
        grayscale_values: list of float (0-255)
        min_size: float, minimum die diameter
        max_size: float, maximum die diameter
        min_gray: int, minimum grayscale in image
        max_gray: int, maximum grayscale in image
        available_dies: list of float, snap to nearest (optional)

    Returns:
        list of float: die diameter per point
    """
    gray_range = max_gray - min_gray
    if gray_range <= 0:
        gray_range = 1

    diameters = []
    for g in grayscale_values:
        if g <= 0:
            d = 0.0  # no perforation
        else:
            # Normalize to 0-1
            normalized = (g - min_gray) / gray_range
            normalized = max(0.0, min(1.0, normalized))
            d = min_size + normalized * (max_size - min_size)

        # Snap to nearest available die
        if available_dies and d > 0:
            d = min(available_dies, key=lambda x: abs(x - d))

        diameters.append(d)

    return diameters


# Keep old function names for backward compatibility
def sample_brightness(image_data, points, panel_bbox, config):
    """Backward-compatible wrapper. Returns normalized 0-1 values."""
    raw = sample_grayscale(image_data, points, panel_bbox, config)
    max_g = image_data.get("max_gray", 255)
    if max_g <= 0:
        max_g = 255
    return [g / max_g for g in raw]


def brightness_to_die_size(brightness_list, min_size, max_size, available_dies=None):
    """Backward-compatible wrapper."""
    diameters = []
    for b in brightness_list:
        d = min_size + b * (max_size - min_size)
        if available_dies and d > 0:
            d = min(available_dies, key=lambda x: abs(x - d))
        diameters.append(d)
    return diameters
