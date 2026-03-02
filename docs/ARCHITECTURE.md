# Architecture

## Two Modes of Operation

### Mode A: Grasshopper (Interactive)
```
User opens Rhino 8 + Grasshopper
          │
          ▼
    ┌─────────────┐
    │ REPO_ROOT   │ ← Panel with local clone path
    │   Panel     │
    └──────┬──────┘
           │ (feeds all components)
           ▼
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ 01_load      │────▶│ 02_analyze   │────▶│ 03_grid      │
    │ images.py    │     │ images.py    │     │ layout.py    │
    └──────────────┘     └──────────────┘     └──────┬───────┘
           │                                          │
           │              ┌──────────────┐            │
           └─────────────▶│ 04_build     │◀───────────┘
                          │ wall.py      │
                          └──────┬───────┘
                                 │
                          ┌──────▼───────┐
                          │ 05_export    │──▶ output/wall.png
                          │ wall.py      │
                          └──────────────┘
```
Each GhPython component uses **Script Sync** (Rhino 8) to link
directly to the .py file. On `git pull`, files update, and
Grasshopper reloads on recompute.

### Mode B: MCP Server (Headless)
```
Claude / MCP Client
       │
       │ (MCP protocol over stdio)
       ▼
┌──────────────┐     ┌──────────────┐
│ server.py    │────▶│ rhino_bridge │──▶ output/wall.png
│ (MCP tools)  │     │ .py (Pillow) │
└──────────────┘     └──────────────┘
```
No Rhino needed. Uses Pillow for image compositing.
Same config.json, same image folder.

## Git Workflow
- `scripts/` — full Git workflow (diff, merge, PR, review)
- `.gh` file — committed but seldom changed
- `config.json` — shared settings, version controlled
- `images/` — either tracked or .gitignored (Git LFS for large sets)