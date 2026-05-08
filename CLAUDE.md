# Project Notes

## pyRevit / IronPython

These rules apply to all code in `revit-mcp-python.extension/`:

- No f-strings — use `.format()` instead
- Always include `# -*- coding: UTF-8 -*-` at the top of every route file
- Wrap all string data from Revit in `safe_string()` from `revit_mcp/utils.py` — IronPython 2.7 fails on non-ASCII characters (common in Belgian/Dutch models)
- Use `get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)` for type names, not `.Name` directly — direct property access often fails in IronPython
- Return statements must be outside for loops — easy mistake that silently returns only the first item
- Use `xlsxwriter` for writing Excel files (openpyxl unavailable in IronPython)
- Use `xlrd` for reading Excel files

## After Changing Routes

A full Revit reload is required — pyRevit tab → Reload. `/mcp` reconnects the MCP client but does not reload Revit-side route code in memory.

## Adding New Functionality

Three steps, always all three:
1. Route module in `revit-mcp-python.extension/revit_mcp/` → register in `startup.py`
2. Tool module in `tools/` → register in `tools/__init__.py`

See `LLM.txt` for complete code templates.

## Lean Queries

Filter at the **route level** (inside Revit/IronPython), not in the tool layer.
Route endpoints should accept filter parameters (URL path segments or POST body) and apply them before building the response array.
This keeps the HTTP payload small and avoids transferring unused data from pyRevit to the MCP server.

- Good: `GET /doors/room/badkamer` → Revit filters before returning
- Bad: fetch all doors in the tool, then filter in Python

When a single filter is most common, use URL path segments (e.g. `/doors/room/<room_name>`).
When two filters are needed together, apply the primary one in the route and the secondary one in the tool.

## Querying the Model

Use discovery-first: call `get_model_structure` before any filtered query to confirm apartment numbers, building segments, and room name spelling. The `apartment_filter` parameter uses prefix matching (e.g. `"1."` matches `1.A` and `1.B` only). See `revit-query/SKILL.md` for the full workflow.

## Universal Element Philosophy

Every query tool must return `element_id` for each element it exposes. This unlocks two universal operations that work on **any** Revit element regardless of category (door, wall, window, room, furniture, …):

- **`override_element_color`** — highlight any element in any view (`element_id` + `view_id`)
- **`write_element_parameter`** — write to Mark or Comments on any element (`element_id` + `param` + `value`)

**Design rule:** Never build category-specific override or write tools. Use the universal ones. When building a new route, always include `element_id` in the response payload.

### Getting a view_id

Use `get_view_id_by_name("<exact view name>")` before calling `override_element_color`. View names are discoverable via `list_revit_views`. Route: `GET /view_id/<view_name>` (in `views.py`).

### Write to Mark / Comments

`write_element_parameter` writes to the Mark (`ALL_MODEL_MARK`) or Comments (`ALL_MODEL_INSTANCE_COMMENTS`) built-in parameter. Both are present on every hosted and non-hosted Revit element. The AI decides what to write and to which element based on context. Route: `POST /element/write_param` (in `element_overrides.py`).

For bulk operations use `write_element_parameters_bulk` — a list of `{ element_id, param, value }` written in one Revit transaction.

**The AI is responsible for computing values before writing.** It queries elements, applies logic (suffix calculation, compliance labels, etc.), then fires one bulk write. No specialized routes per use case.

Example workflows:
- **Door marks from room numbers:** `get_doors_with_rooms` → group by ToRoom number → assign suffixes ("02a", "02b") if multiple doors share a room → `write_element_parameters_bulk`
- **Compliance stamp:** compliance check → filter non-conforming elements → `write_element_parameters_bulk` with `param="comments", value="te klein"`
- **Clear marks:** same bulk call with `value=""`
