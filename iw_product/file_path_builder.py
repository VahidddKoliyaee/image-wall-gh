"""
Module 16: File Path Builder
==============================
Constructs output file paths with timestamps for image/document exports.

Replaces: "Current Folder" + "Raster Image File Name" groups.

Usage:
    from iw_product.file_path_builder import build_file_path
    path = build_file_path(gh_file_folder, input_name, make_image)
"""

import os
from datetime import datetime


def get_gh_file_folder(gh_file_path):
    """
    Extract the folder from a GH file path.

    Args:
        gh_file_path: str, full path to the .gh file

    Returns:
        str: folder containing the .gh file
    """
    if not gh_file_path:
        return ""
    return os.path.dirname(gh_file_path)


def build_file_path(gh_file_folder, input_name="", make_image=True, subfolder="OUTGOING"):
    """
    Build the output file path with timestamp.

    Args:
        gh_file_folder: str, folder containing the GH file
        input_name: str, base file name
        make_image: bool, whether to generate timestamp
        subfolder: str, output subfolder name

    Returns:
        dict with:
            file_path      - str: full path without extension
            folder         - str: output folder
            filename       - str: filename without extension
            timestamp      - str: timestamp string
    """
    # Output folder
    folder = os.path.join(gh_file_folder, subfolder) if gh_file_folder else ""

    # Timestamp
    if make_image:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    else:
        timestamp = ""

    # Filename
    if input_name and timestamp:
        filename = "{}___{}".format(input_name, timestamp)
    elif input_name:
        filename = input_name
    else:
        filename = timestamp or "output"

    # Full path (without extension — renderer appends .png)
    file_path = os.path.join(folder, filename) if folder else filename

    return {
        "file_path": file_path,
        "folder": folder,
        "filename": filename,
        "timestamp": timestamp,
    }
