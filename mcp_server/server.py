"""
server.py — MCP Server for Image Wall generation.

Run: python server.py
Communicates via stdio using the MCP protocol.

Tools exposed:
  - generate_wall: Generate an image wall from a folder of images
  - list_images: List available images
  - update_config: Update wall configuration
"""

import os
import sys
import json
import asyncio

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent
import base64

from rhino_bridge import generate_wall_image, collect_images, load_config

# Resolve repo root (one level up from mcp_server/)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

server = Server("image-wall")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="generate_wall",
            description="Generate a 2D image wall from a folder of images. Returns the output image path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_folder": {
                        "type": "string",
                        "description": "Path to folder with images. Default: repo's images/ folder"
                    },
                    "columns": {
                        "type": "integer",
                        "description": "Number of columns in the grid. Default: from config.json"
                    },
                    "spacing": {
                        "type": "number",
                        "description": "Spacing between cells in mm. Default: from config.json"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output file path. Default: repo's output/wall.png"
                    }
                }
            }
        ),
        Tool(
            name="list_images",
            description="List available images in the input folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_folder": {
                        "type": "string",
                        "description": "Path to folder. Default: repo's images/ folder"
                    }
                }
            }
        ),
        Tool(
            name="update_config",
            description="Update the wall configuration (grid_columns, cell_spacing_mm, cell_width_mm, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "settings": {
                        "type": "object",
                        "description": "Key-value pairs to update in config.json"
                    }
                },
                "required": ["settings"]
            }
        ),
        Tool(
            name="get_wall_preview",
            description="Generate the wall and return it as a base64-encoded image for inline viewing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_folder": {"type": "string"},
                    "columns": {"type": "integer"},
                    "max_width": {
                        "type": "integer",
                        "description": "Max pixel width for preview (default 1200)"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    
    if name == "generate_wall":
        try:
            result_path = generate_wall_image(
                repo_root=REPO_ROOT,
                image_folder=arguments.get("image_folder"),
                columns=arguments.get("columns"),
                spacing=arguments.get("spacing"),
                output_path=arguments.get("output_path")
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "output_path": result_path,
                    "message": f"Wall generated at {result_path}"
                })
            )]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"status": "error", "message": str(e)}))]

    elif name == "list_images":
        folder = arguments.get("image_folder") or os.path.join(REPO_ROOT, "images")
        images = collect_images(folder)
        return [TextContent(
            type="text",
            text=json.dumps({
                "folder": folder,
                "count": len(images),
                "files": [os.path.basename(p) for p in images]
            })
        )]

    elif name == "update_config":
        config_path = os.path.join(REPO_ROOT, "config.json")
        config = load_config(REPO_ROOT)
        config.update(arguments.get("settings", {}))
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return [TextContent(
            type="text",
            text=json.dumps({"status": "success", "config": config})
        )]

    elif name == "get_wall_preview":
        from PIL import Image as PILImage
        import io
        
        try:
            result_path = generate_wall_image(
                repo_root=REPO_ROOT,
                image_folder=arguments.get("image_folder"),
                columns=arguments.get("columns")
            )
            
            # Resize for preview
            max_w = arguments.get("max_width", 1200)
            img = PILImage.open(result_path)
            if img.width > max_w:
                ratio = max_w / img.width
                img = img.resize((max_w, int(img.height * ratio)), PILImage.LANCZOS)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            
            return [ImageContent(
                type="image",
                data=b64,
                mimeType="image/png"
            )]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"status": "error", "message": str(e)}))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())