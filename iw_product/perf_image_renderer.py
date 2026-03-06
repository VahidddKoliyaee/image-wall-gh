"""
Module 17: Perf Image Renderer
================================
Renders high-resolution raster images of perforated panels.
Supports all 6 hole shapes, invert, transparency, cutouts.

Usage (GH):    render_image(params)
Usage (standalone): render_image_pillow(params)
"""

import math
import os


def _rotation_matrix(angle_rad):
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return (c, -s, s, c)


def render_image(params):
    """
    Render using System.Drawing (.NET) inside GH/Rhino.
    Supports: circle, slot, rectangle, square, hexagon, triangle.
    Supports: invert, transparency, cutouts, variable die sizes.
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

    bmp = SD.Bitmap(w_px, h_px)
    g = SD.Graphics.FromImage(bmp)
    g.SmoothingMode = SD.Drawing2D.SmoothingMode.AntiAlias

    # Background
    transparent = params.get("transparent", False)
    invert = params.get("invert", False)

    sr, sg, sb = params.get("surf_color", (200, 200, 200))
    hr, hg, hb = params.get("hole_color", (0, 0, 0))

    # If invert: swap surface and hole colors
    if invert:
        sr, sg, sb, hr, hg, hb = hr, hg, hb, sr, sg, sb

    if transparent:
        g.Clear(SD.Color.Transparent)
    else:
        g.Clear(SD.Color.FromArgb(255, sr, sg, sb))

    # Draw panel outlines (filled)
    panels = params.get("panels", [])
    if panels:
        panel_brush = SD.SolidBrush(SD.Color.FromArgb(255, sr, sg, sb))
        for poly in panels:
            if poly and len(poly) >= 3:
                sd_pts = []
                for px_pt, py_pt in poly:
                    sd_pts.append(SD.PointF(
                        float(px_pt * scale),
                        float(h_px - py_pt * scale)))
                if len(sd_pts) >= 3:
                    g.FillPolygon(panel_brush, sd_pts)
        panel_brush.Dispose()

    # Draw cutouts (holes in panel — filled with background)
    cutouts = params.get("cutouts", [])
    if cutouts:
        if transparent:
            cut_brush = SD.SolidBrush(SD.Color.Transparent)
        else:
            cut_brush = SD.SolidBrush(SD.Color.FromArgb(255, hr, hg, hb))
        for poly in cutouts:
            if poly and len(poly) >= 3:
                sd_pts = []
                for px_pt, py_pt in poly:
                    sd_pts.append(SD.PointF(
                        float(px_pt * scale),
                        float(h_px - py_pt * scale)))
                if len(sd_pts) >= 3:
                    g.FillPolygon(cut_brush, sd_pts)
        cut_brush.Dispose()

    # Draw perforations
    brush = SD.SolidBrush(SD.Color.FromArgb(255, hr, hg, hb))
    pts = params.get("pts", [])
    radii = params.get("map", [])
    shape = params.get("shape", "circle").lower()

    for i, (px, py) in enumerate(pts):
        radius = radii[i] if i < len(radii) else 0.1
        sx = px * scale
        sy = h_px - py * scale
        r_px = radius * scale

        if r_px < 0.5:
            continue

        if shape == "circle":
            g.FillEllipse(brush, float(sx - r_px), float(sy - r_px),
                          float(r_px * 2), float(r_px * 2))
        elif shape in ("rectangle", "slot"):
            g.FillRectangle(brush, float(sx - r_px), float(sy - r_px * 0.5),
                            float(r_px * 2), float(r_px))
        elif shape == "square":
            g.FillRectangle(brush, float(sx - r_px), float(sy - r_px),
                            float(r_px * 2), float(r_px * 2))
        elif shape == "hexagon":
            hex_pts = []
            for a in range(6):
                angle = math.pi / 3.0 * a - math.pi / 6.0
                hx = sx + r_px * math.cos(angle)
                hy = sy + r_px * math.sin(angle)
                hex_pts.append(SD.PointF(float(hx), float(hy)))
            g.FillPolygon(brush, hex_pts)
        elif shape == "triangle":
            tri_pts = [
                SD.PointF(float(sx), float(sy - r_px)),
                SD.PointF(float(sx - r_px * 0.866), float(sy + r_px * 0.5)),
                SD.PointF(float(sx + r_px * 0.866), float(sy + r_px * 0.5)),
            ]
            g.FillPolygon(brush, tri_pts)
        else:
            g.FillEllipse(brush, float(sx - r_px), float(sy - r_px),
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
    """Render using Pillow (standalone). Same interface as render_image()."""
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

    invert = params.get("invert", False)
    sr, sg, sb = params.get("surf_color", (200, 200, 200))
    hr, hg, hb = params.get("hole_color", (0, 0, 0))
    if invert:
        sr, sg, sb, hr, hg, hb = hr, hg, hb, sr, sg, sb

    if params.get("transparent", False):
        img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
    else:
        img = Image.new("RGBA", (w_px, h_px), (sr, sg, sb, 255))

    draw = ImageDraw.Draw(img)
    hole_fill = (hr, hg, hb, 255)

    pts = params.get("pts", [])
    radii = params.get("map", [])
    shape = params.get("shape", "circle").lower()

    for i, (px, py) in enumerate(pts):
        radius = radii[i] if i < len(radii) else 0.1
        sx = px * scale
        sy = h_px - py * scale
        r_px = radius * scale
        if r_px < 0.5:
            continue
        if shape == "circle":
            draw.ellipse([sx - r_px, sy - r_px, sx + r_px, sy + r_px], fill=hole_fill)
        else:
            draw.rectangle([sx - r_px, sy - r_px, sx + r_px, sy + r_px], fill=hole_fill)

    file_path = params.get("file_path", "output")
    if not file_path.lower().endswith(".png"):
        file_path += ".png"
    folder = os.path.dirname(file_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
    img.save(file_path)
    return file_path