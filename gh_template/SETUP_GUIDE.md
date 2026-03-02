# Grasshopper Definition Setup Guide

## Overview
You will create 5 GhPython components wired in sequence. Each component
loads its logic from an external .py file in the `scripts/` folder.
When anyone does `git pull`, the scripts update and GH picks up changes
on the next recompute.

## Prerequisites
- Rhino 8
- Clone the repo somewhere, e.g. `C:\Users\You\repos\image-wall-gh`

## Step-by-Step

### STEP 1: Create the REPO_ROOT Panel
1. Drop a **Panel** onto the canvas
2. Type your local repo path: `C:\Users\You\repos\image-wall-gh`
3. Name it `REPO_ROOT` (right-click → name)

### STEP 2: Create Component 01 — Load Images
1. Drop a **GhPython Script** component (Rhino 8 has this built in)
2. Right-click → **Open Script Editor** (or double click)
3. In the editor, use **Script Sync** (Rhino 8 feature):
   - Click the chain icon → Browse → Select `scripts/01_load_images.py`
   - OR paste this bootstrap code:
```python
     import os, sys
     _repo = str(repo_root).strip().strip('"')
     _s = os.path.join(_repo, "scripts")
     if _s not in sys.path: sys.path.insert(0, _s)
     exec(open(os.path.join(_s, "01_load_images.py")).read())
```
4. Set inputs (zoom into component, click `+`):
   - `repo_root` (str) ← connect from REPO_ROOT panel
   - `img_folder` (str) ← optional Panel, leave empty for default
5. Set outputs:
   - `image_paths` (list)
   - `count` (int)
   - `status` (str)

### STEP 3: Create Component 02 — Analyze Images
Same process with `scripts/02_analyze_images.py`
- Inputs: `repo_root`, `image_paths` (from component 01)
- Outputs: `widths`, `heights`, `aspects`, `orientations`, `status`

### STEP 4: Create Component 03 — Grid Layout
Same process with `scripts/03_grid_layout.py`
- Inputs: `repo_root`, `aspects` (from 02), `count` (from 01), `columns_override` (optional Panel, 0=config default)
- Outputs: `origins_x`, `origins_y`, `cell_widths`, `cell_heights`, `wall_width`, `wall_height`, `status`

### STEP 5: Create Component 04 — Build Wall
Same process with `scripts/04_build_wall.py`
- Inputs: `repo_root`, `image_paths` (01), `origins_x`, `origins_y`, `cell_widths`, `cell_heights` (03), `wall_width`, `wall_height` (03)
- Outputs: `frames`, `bg_surface`, `picture_frames`, `labels`, `status`

### STEP 6: Create Component 05 — Export
Same process with `scripts/05_export_wall.py`
- Inputs: `repo_root`, `wall_width`, `wall_height` (03), `export_name` (Panel), `do_export` (Boolean Toggle)
- Outputs: `output_path`, `status`

### STEP 7: Wire It Up
```
[REPO_ROOT panel] ──→ repo_root on ALL components (01-05)

[01 Load] ──image_paths──→ [02 Analyze] ──aspects──→ [03 Grid]
    │                                                    │
    │──image_paths──→ [04 Build] ←── origins, sizes ─────┘
    │──count──→ [03 Grid]            │
                                     ↓
                              [05 Export]
```

## Script Sync (Recommended for Rhino 8)
Instead of the `exec()` bootstrap, Rhino 8's Script Editor supports
**Script Sync** which directly links a .py file to a GhPython component.
When the file changes on disk, the component auto-reloads.

1. Double-click GhPython component → opens Script Editor
2. Click the link/chain icon in the toolbar
3. Browse to the .py file in `scripts/`
4. Done — file changes are auto-detected

## Pulling Updates
```bash
cd C:\Users\You\repos\image-wall-gh
git pull
```
Then recompute Grasshopper (F5 or press the recompute button).
Script-synced components reload automatically.