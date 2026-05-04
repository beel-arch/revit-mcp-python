---
name: revit-query
description: Efficient Revit model querying via MCP. Always calls get_model_structure first to discover building segments, room names, and levels before running any targeted query. Use when user asks about specific buildings ("gebouw 1", "blok A"), room types ("badkamers", "slaapkamers"), levels ("niveau 2"), area compliance, daylight checks, or furniture. Requires Revit-Connector MCP to be connected.
metadata:
  author: Frederik Van Nespen
  version: 1.0.0
  mcp-server: Revit-Connector
---

# Revit Query

## Workflow

### Step 1: Discover — always first for ambiguous queries

If the user's request refers to a specific building, level, room type, or area
scheme, call `get_model_structure` before anything else.

Triggers that require discovery:
- Mentions a building or block: "gebouw 1", "blok A", "toren 2"
- Mentions a level: "niveau 2", "gelijkvloers", "verdieping 3"
- Mentions a room type: "badkamers", "slaapkamers", "keukens"
- Mentions an area scheme: "WO", "BVO", "GBO"

Skip discovery when the request is fully unambiguous:
- "run the full compliance check on everything"
- "list all views"

### Step 2: Ask ONE clarifying question

After `get_model_structure` returns, present the relevant identifiers and ask
one question. Do not ask multiple questions at once.

Good example:
> "I see apartment blocks **1.A**, **1.B**, and **2.C**. Does 'gebouw 1' mean
> both 1.A and 1.B, or just one of them?"

State your assumption explicitly if you infer a filter:
> "I'll use filter '1.' which matches both 1.A and 1.B — correct?"

Wait for confirmation before running the heavy tool.

### Step 3: Run targeted tool with filters

Use the confirmed identifiers as filter parameters. Never run a heavy tool
without a filter when the user has scoped their request.

| User intent | Tool | Filter parameter(s) |
|---|---|---|
| Compliance check, gebouw 1 | `compare_rooms_with_checklist` | `apartment_filter="1."` |
| Only badkamers in blok 1.A | `compare_rooms_with_checklist` | `apartment_filter="1.A"`, `room_type_filter="badkamer"` |
| Daglicht niveau 2, blok 1.A | `check_window_area_compliance` | `apartment_filter="1.A.Niv 2"` |
| Meubels in slaapkamers | `get_furniture_by_room` | `room_name_filter="slaap"` |
| WO areas | `get_areas_by_scheme` | `scheme_name="WO"` |

## Available Tools

| Tool | Purpose |
|---|---|
| `get_model_structure` | Discovery — levels, apartment segments, room names, area schemes |
| `compare_rooms_with_checklist` | Codex Wonen area compliance per apartment |
| `check_window_area_compliance` | Daylight norm (window/floor ratio) |
| `get_furniture_by_room` | Furniture inventory per room |
| `get_areas_by_scheme` | Area totals by scheme |
| `list_revit_views` | Available views and sheets |
| `get_revit_view` | Export a view as image |
| `list_levels` | Building levels with elevations |
| `get_elements_by_category` | Raw element list by Revit category |

## Rules

- **One question at a time.** Ask the most important clarifying question first.
- **State assumptions.** If you infer a filter value, say so before calling the tool.
- **Prefer filtered calls.** A small report that fits in context beats a full-model
  report saved to a file.
- **Report size matters.** If a result exceeds context, it gets saved to a temp file
  and requires a subagent to read — expensive. Use filters to prevent this.

## Reference Files

Consult these when you need more detail — only load as needed:

- `references/tool-reference.md` — full parameter docs for every tool, including
  all filter options and return shapes
- `references/codex-wonen-rules.md` — room classification keywords, toilet
  detection logic, and minimum area table with examples

## Common Issues

**MCP not connected**
Ask the user to run `/mcp` to reconnect, or check that pyRevit is loaded in Revit.

**Route not found (500 error)**
The pyRevit extension needs a reload inside Revit: pyRevit tab → Reload.
`/mcp` reconnects the client but does not reload the Revit-side routes.

**Filter returns no results**
The filter is a substring match on the apartment number field. Use
`get_model_structure` to confirm the exact segment format before filtering.
