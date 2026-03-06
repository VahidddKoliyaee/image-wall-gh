"""
GH Wrapper: Config Loader (ALL inputs)
Paste into a GhPython 3 component.

INPUTS:
    RepoPath          : str   - Path to IMAGE-WALL-GH repo
    ExcelPath         : str   - Path to IW-Product.xlsx
    RunImport         : bool  - Trigger
    ImageFilepath     : str   - Path to source image (e.g. bluebonnet.jpg)
    MakeImage         : bool  - Trigger image rendering
    UserResolution    : float - Px/in (0 = auto)
    InvertImage       : bool  - Flip dark/light (overrides Excel)
    TransparentHoles  : bool  - Transparent background (overrides Excel)
    BlurOn            : bool  - Apply blur to source image
    BlurRadius        : int   - Blur radius (default 2)
    ThresholdOverrule : bool  - Override auto threshold
    ThresholdValue    : int   - Threshold value 0-255
    PunchMaximizer    : bool  - Optimize die usage
    DropLockBlockPath : str   - Path to block file
    ShopTemplatePath  : str   - Path to shop template .3dm
    LineWeight        : float - Bake line weight (default 2)

OUTPUTS:
    Done : bool
"""

import sys
import os

Done = False

if not RunImport:
    print("Standing by")
elif not RepoPath or not os.path.isdir(str(RepoPath)):
    print("ERROR: Set RepoPath to your IMAGE-WALL-GH folder")
elif not ExcelPath:
    print("ERROR: Set ExcelPath to your IW-Product.xlsx")
else:
    rp = str(RepoPath)
    if rp not in sys.path:
        sys.path.insert(0, rp)

    for mod in list(sys.modules):
        if mod.startswith("iw_product"):
            del sys.modules[mod]

    from iw_product.config_loader import load_config
    from iw_product import shared

    # Build overrides from GH inputs
    overrides = {}

    # Image filepath
    try:
        if ImageFilepath:
            overrides["image_filepath"] = str(ImageFilepath)
    except:
        pass

    # Make image
    try:
        overrides["make_image"] = bool(MakeImage)
    except:
        pass

    # Resolution
    try:
        if UserResolution is not None:
            overrides["user_resolution"] = float(UserResolution)
    except:
        pass

    # Invert (override Excel if set)
    try:
        if InvertImage is not None:
            overrides["invert_image"] = bool(InvertImage)
    except:
        pass

    # Transparency override
    try:
        if TransparentHoles is not None:
            overrides["transparency"] = bool(TransparentHoles)
    except:
        pass

    # Blur
    try:
        overrides["blur_on"] = bool(BlurOn) if BlurOn is not None else False
    except:
        pass
    try:
        overrides["blur_radius"] = int(BlurRadius) if BlurRadius else 2
    except:
        pass

    # Threshold
    try:
        overrides["threshold_overrule"] = bool(ThresholdOverrule) if ThresholdOverrule is not None else False
    except:
        pass
    try:
        overrides["threshold_value"] = int(ThresholdValue) if ThresholdValue else 128
    except:
        pass

    # Punch maximizer
    try:
        overrides["punch_use_maximizer"] = bool(PunchMaximizer) if PunchMaximizer is not None else False
    except:
        pass

    # File paths
    try:
        if DropLockBlockPath:
            overrides["drop_lock_block_path"] = str(DropLockBlockPath)
    except:
        pass
    try:
        if ShopTemplatePath:
            overrides["shop_template_path"] = str(ShopTemplatePath)
    except:
        pass

    # Line weight
    try:
        if LineWeight is not None:
            overrides["line_weight"] = float(LineWeight)
    except:
        pass

    config = load_config(str(ExcelPath), **overrides)
    shared.put("config", config)
    Done = True

    print("Loaded: {} - {}".format(config["product_number"], config["scope_name"]))
    print("Material: {} | Style: {}".format(config["material"], config["style"]))
    print("Grid: {}x{} panels, {}x{} in".format(
        config["qty_columns"], config["qty_rows"],
        config["panel_col_width"], config["panel_row_height"]))
    if config.get("image_filepath"):
        print("Image: {}".format(config["image_filepath"]))
    print("Config: {} keys".format(len(config)))