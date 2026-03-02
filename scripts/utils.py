"""
utils.py — Shared helpers for Image Wall GH project.
This file is loaded by other scripts via exec() inside Grasshopper
or imported directly in MCP/headless mode.
"""

import os
import json

def get_repo_root(repo_root_input=None):
    """Resolve the repo root path. Works in GH and standalone."""
    if repo_root_input:
        return str(repo_root_input).strip().strip('"').replace("\\", "/")
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_config(repo_root):
    """Load config.json from repo root."""
    config_path = os.path.join(repo_root, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    # Defaults
    return {
        "grid_columns": 4,
        "cell_spacing_mm": 10,
        "cell_width_mm": 200,
        "maintain_aspect_ratio": True,
        "background_color": [255, 255, 255],
        "border_width_mm": 2,
        "border_color": [30, 30, 30],
        "output_dpi": 300,
        "output_format": "png",
        "wall_padding_mm": 20
    }

def get_image_extensions():
    return {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}

def safe_path(*parts):
    """Join path parts and normalize."""
    return os.path.normpath(os.path.join(*parts))