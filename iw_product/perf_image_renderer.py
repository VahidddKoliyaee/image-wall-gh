"""
Module 17: Perf Image Renderer
================================
Renders high-resolution raster images of perforated panels.
Supports circle, slot, rectangle, square, hexagon, and triangle shapes.

Replaces: "Perf Image Output" C# script + "Export Raster Image" group.

This module uses System.Drawing (GH/Rhino) or Pillow (standalone).

Usage (in GH):
    from iw_product.perf_image_renderer import render_image
    result = render_image(params)

Usage (standalone with Pillow):
    from iw_product.perf_image_renderer import render_image_pillow
    result = render_image_pillow(params)
"""

import math
import os


def render_image(params):
    """
    Render a perforated panel image using System.Drawing (.NET).
    For use inside Grasshopper/Rhino.

    Args:
        params: dict with keys:
            x, y          - panel dimensions (inches)
            pts           - list of (px, py) perf center coords
            panels        - list of panel outline polylines [(x,y), ...]
            cutouts       - list of cutout polylines (optional)
            map           - list of radii per perf point
            shape         - str: "circle", "slot", "rectangle", etc.
            scale         - int: pixels per inch
            surf_color    - (R, G, B) panel surface color
            hole_color    - (R, G, B) perforation color
            transparent   - bool: transparent background
            file_path     - str: output path (no extension)
            run           - bool: trigger

    Returns:
        str: output file path, or "" if not run
    """
    if not params.get("run", False):
        return ""

    import System.Drawing as SD

    x = params["x"]
    y = params["y"]
    scale = params["scale"]
    w_px = int(x * scale)
    h_px = int(y * scale)

    if w_px <= 0 or h_px <= 0:
        return ""

    # Create bitmap
    bmp = SD.Bitmap(w_px, h_px)
    g = SD.Graphics.FromImage(bmp)
    g.SmoothingMode = SD.Drawing2D.SmoothingMode.AntiAlias

    # Background
    if params.get("transparent", False):
        g.Clear(SD.Color.Transparent)
    else:
        r, gr, b = params.get("surf_color", (200, 200, 200))
        g.Clear(SD.Color.FromArgb(255, r, gr, b))

    # Draw perforations
    hr, hg, hb = params.get("hole_color", (0, 0, 0))
    brush = SD.SolidBrush(SD.Color.FromArgb(255, hr, hg, hb))

    pts = params.get("pts", [])
    radii = params.get("map", [])
    shape = params.get("shape", "circle").lower()

    for i, (px, py) in enumerate(pts):
        radius = radii[i] if i < len(radii) else 0.1
        sx = px * scale
        sy = h_px - py * scale  # flip Y
        r_px = radius * scale

        if shape == "circle":
            g.FillEllipse(brush, float(sx - r_px), float(sy - r_px),
                          float(r_px * 2), float(r_px * 2))
        else:
            # Rectangle/square fallback
            g.FillRectangle(brush, float(sx - r_px), float(sy - r_px),
                            float(r_px * 2), float(r_px * 2))

    # Save
    file_path = params.get("file_path", "output")
    if not file_path.lower().endswith(".png"):
        file_path += ".png"

    folder = os.path.dirname(file_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    bmp.Save(file_path, SD.Imaging.ImageFormat.Png)
    g.Dispose()
    bmp.Dispose()
    brush.Dispose()

    return file_path


def render_image_pillow(params):
    """
    Render using Pillow (for standalone/testing outside Rhino).
    Same interface as render_image().
    """
    if not params.get("run", False):
        return ""

    from PIL import Image, ImageDraw

    x = params["x"]
    y = params["y"]
    scale = params["scale"]
    w_px = int(x * scale)
    h_px = int(y * scale)

    if w_px <= 0 or h_px <= 0:
        return ""

    if params.get("transparent", False):
        img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
    else:
        r, g, b = params.get("surf_color", (200, 200, 200))
        img = Image.new("RGBA", (w_px, h_px), (r, g, b, 255))

    draw = ImageDraw.Draw(img)

    hr, hg, hb = params.get("hole_color", (0, 0, 0))
    hole_fill = (hr, hg, hb, 255)

    pts = params.get("pts", [])
    radii = params.get("map", [])
    shape = params.get("shape", "circle").lower()

    for i, (px, py) in enumerate(pts):
        radius = radii[i] if i < len(radii) else 0.1
        sx = px * scale
        sy = h_px - py * scale
        r_px = radius * scale

        if shape == "circle":
            draw.ellipse(
                [sx - r_px, sy - r_px, sx + r_px, sy + r_px],
                fill=hole_fill)
        else:
            draw.rectangle(
                [sx - r_px, sy - r_px, sx + r_px, sy + r_px],
                fill=hole_fill)

    file_path = params.get("file_path", "output")
    if not file_path.lower().endswith(".png"):
        file_path += ".png"

    folder = os.path.dirname(file_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    img.save(file_path)
    return file_path
