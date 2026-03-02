# MCP Usage Guide

## Setup

### 1. Install Dependencies
```bash
cd mcp_server
pip install -r requirements.txt
```

### 2. Register with Claude Desktop
Add to your Claude Desktop MCP config (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "image-wall": {
      "command": "python",
      "args": ["C:/Users/You/repos/image-wall-gh/mcp_server/server.py"],
      "env": {}
    }
  }
}
```

### 3. Usage Examples

**Ask Claude:**
- "Generate an image wall from my photos folder"
- "Make a 6-column wall from the images in C:\Photos\vacation"
- "Show me a preview of the image wall"
- "Update the wall config to use 5 columns and 15mm spacing"

### Available Tools

| Tool | Description |
|------|-------------|
| `generate_wall` | Create the full image wall output |
| `list_images` | See what images are available |
| `update_config` | Change grid settings |
| `get_wall_preview` | Get a base64 preview image |

### Example MCP Call
```json
{
  "method": "tools/call",
  "params": {
    "name": "generate_wall",
    "arguments": {
      "image_folder": "C:/Photos/vacation",
      "columns": 5,
      "output_path": "C:/output/my_wall.png"
    }
  }
}
```