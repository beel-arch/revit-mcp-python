    # Revit MCP Python - BEEL Fork

MCP (Model Context Protocol) bridge between Autodesk Revit and LLM clients like Claude Desktop and Claude Code. Based on [revit-mcp](https://github.com/mcp-servers-for-revit/revit-mcp.git) by JotaDeRodriguez.

## How It Works

```
LLM Client  <--MCP (stdio)-->  MCP Server (main.py)  <--HTTP-->  pyRevit Routes (inside Revit)
```

- **pyRevit Routes** runs an HTTP server inside Revit on port `48884`, exposing API endpoints with access to the Revit document context
- **MCP Server** (`main.py`) translates MCP tool calls into HTTP requests to those endpoints
- Any MCP-compatible client (Claude Desktop, Claude Code, MCP Inspector) can then read and interact with the live Revit model

## Available Tools

### Status & Model Info
| Tool | Description |
|------|-------------|
| `get_revit_status` | Check if Revit API is active and responding |
| `get_revit_model_info` | Model title, path, element counts |
| `list_levels` | All levels with elevations |

### Views & Images
| Tool | Description |
|------|-------------|
| `list_revit_views` | All exportable views by type |
| `get_revit_view` | Export a specific view as PNG image |
| `get_current_view_info` | Active view details |
| `get_current_view_elements` | All elements visible in the current view |

### Families & Placement
| Tool | Description |
|------|-------------|
| `list_family_categories` | All family categories in the model |
| `list_families` | Available family types (with text filter and limit) |
| `place_family` | Place a family instance at x,y,z with rotation and properties |
| `create_point_based_element` | Create point-based elements (doors, windows, furniture) |

## Setup

### Prerequisites
- Revit 2025+ with pyRevit installed
- [uv](https://docs.astral.sh/uv/) package manager
- Routes server enabled in pyRevit Settings

### 1. Install the pyRevit Extension
1. In Revit, go to pyRevit tab > Settings
2. Under "Custom Extensions", add the path to the `revit-mcp-python.extension/` folder
3. Enable the Routes server in pyRevit Settings
4. Restart Revit

### 2. Verify the Connection
Open a browser and navigate to:
```
http://localhost:48884/revit_mcp/status/
```
You should see:
```json
{"status": "active", "health": "healthy", "revit_available": true}
```

### 3. Connect an MCP Client

**Claude Desktop** - add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "Revit Connector": {
      "command": "uv",
      "args": [
        "run", "--with", "mcp[cli]", "mcp", "run",
        "C:/absolute/path/to/main.py"
      ]
    }
  }
}
```

**Claude Code** - add a `.mcp.json` to your project root:
```json
{
  "mcpServers": {
    "Revit-Connector": {
      "command": "uv",
      "args": [
        "run", "--with", "mcp[cli]", "mcp", "run",
        "C:/absolute/path/to/main.py"
      ]
    }
  }
}
```

**MCP Inspector** (for debugging):
```bash
mcp dev main.py
```

## Project Structure

```
revit-mcp-python/
├── main.py                          # MCP server - HTTP bridge to Revit
├── tools/                           # MCP tool definitions
│   ├── __init__.py                  # Central tool registration
│   ├── status_tools.py              # Status & connectivity
│   ├── model_tools.py               # Model info & levels
│   ├── view_tools.py                # View export & images
│   ├── family_tools.py              # Family listing & placement
│   └── furniture_tools.py           # Furniture-specific tools
├── revit-mcp-python.extension/      # pyRevit extension (runs inside Revit)
│   ├── startup.py                   # Route registration entry point
│   └── revit_mcp/                   # Route endpoint modules
│       ├── status.py
│       ├── model_info.py
│       ├── views.py
│       ├── placement.py
│       └── utils.py                 # IronPython encoding & safety helpers
├── LLM.txt                         # Context document for LLM-assisted development
├── LESSONS_LEARNED.md               # Gotchas and solutions
└── TOOL_USAGE_GUIDE.md              # Detailed tool usage reference
```

## Adding New Tools

Three steps to add a new capability:

### 1. Route (Revit side)
Create `revit-mcp-python.extension/revit_mcp/your_module.py`:
```python
# -*- coding: UTF-8 -*-
from pyrevit import routes, DB

def register_your_routes(api):
    @api.route('/your_endpoint/', methods=["GET"])
    def your_handler(doc):
        # Access Revit API here
        return routes.make_response(data={"result": "..."})
```

### 2. Tool (MCP side)
Create `tools/your_tools.py`:
```python
def register_your_tools(mcp, revit_get, revit_post, revit_image=None):
    @mcp.tool()
    async def your_tool(ctx=None):
        """Description for the LLM."""
        return await revit_get("/your_endpoint/", ctx)
```

### 3. Register both
- Add `register_your_routes(api)` in `startup.py`
- Add `register_your_tools(...)` in `tools/__init__.py`

## Key Lessons Learned

- **Encoding**: IronPython 2.7 chokes on non-ASCII characters (common in Belgian/Dutch models). Always use `safe_string()` from `utils.py` on all Revit string data.
- **No f-strings**: The pyRevit extension runs in IronPython 2.7. Use `.format()` only.
- **Property access**: Use `element.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)` instead of `element.Name` - direct property access often fails in IronPython.
- **Return placement**: Make sure `return` statements are outside `for` loops (easy mistake that returns only the first item).
- **Dutch fuzzy matching**: Category resolution supports Dutch synonyms via `revit_nl_synonyms.json` with Levenshtein distance matching.

See `LESSONS_LEARNED.md` for the full write-up.

## Credits

Based on [simple_revit_mcp](https://github.com/JotaDeRodriguez/simple_revit_mcp) by JotaDeRodriguez, adapted for BEEL Architecture workflows.
