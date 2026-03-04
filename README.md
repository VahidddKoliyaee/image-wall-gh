# IMAGE-WALL-GH

Python replacement for the `IW-Product-v1.3.5.gh` Grasshopper definition.

## Repo Structure

```
IMAGE-WALL-GH/
├── iw_product/                  # Python package (the logic)
│   ├── __init__.py
│   └── config_loader.py         # Module 01 ✅
├── gh_wrappers/                 # Thin GH scripts (paste into GhPython)
│   └── gh_01_config_loader.py   # Wrapper 01 ✅
├── README.md
├── PROGRESS.md
└── .gitignore
```

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/IMAGE-WALL-GH.git
pip install openpyxl Pillow
```

## Usage in Grasshopper

Each GhPython component is a thin wrapper that imports from this repo:

```python
import sys
sys.path.insert(0, r"C:\Users\vkoliyaee\repos\IMAGE-WALL-GH")
from iw_product.config_loader import load_config
Config = load_config(ExcelPath)
```

## Git Quick Start

```bash
cd IMAGE-WALL-GH
git init
git add .
git commit -m "Module 01: config_loader"
git remote add origin https://github.com/YOUR_USERNAME/IMAGE-WALL-GH.git
git push -u origin main
```
