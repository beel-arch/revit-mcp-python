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

## Querying the Model

Use discovery-first: call `get_model_structure` before any filtered query to confirm apartment numbers, building segments, and room name spelling. The `apartment_filter` parameter uses prefix matching (e.g. `"1."` matches `1.A` and `1.B` only). See `revit-query/SKILL.md` for the full workflow.
