---
name: revit-query
description: Efficient Revit model querying via MCP. Always calls get_model_structure first to discover building segments, room names, and levels before running any targeted query. Use when user asks about specific buildings ("gebouw 1", "blok A"), room types ("badkamers", "slaapkamers"), levels ("niveau 2"), area compliance, daylight checks, furnishings inventory, or bathroom fixture compliance. Requires Revit-Connector MCP to be connected.
metadata:
  author: Frederik Van Nespen
  version: 1.2.0
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
| Oppervlakte-conformiteit, gebouw 1 | `compare_rooms_with_checklist` | `apartment_filter="1."` |
| Alleen badkamers in blok 1.A | `compare_rooms_with_checklist` | `apartment_filter="1.A"`, `room_type_filter="badkamer"` |
| Daglicht niveau 2, blok 1.A | `check_window_area_compliance` | `apartment_filter="1.A.Niv 2"` |
| Meubels/inventaris in slaapkamers | `get_room_furnishings` | `room_name_filter="slaap"` |
| Keukens en kasten in appartement 1.A | `get_room_furnishings` | `apartment_filter="1.A"`, `categories="furniture,casework"` |
| Sanitair inventaris badkamers | `get_room_furnishings` | `apartment_filter="1.A"`, `categories="plumbing,plumbingeq"` |
| Sanitair conformiteit badkamers | `check_room_fixtures` | `apartment_filter="1."`, `room_type="badkamer"` |
| WO areas | `get_areas_by_scheme` | `scheme_name="WO"` |

## Available Tools

| Tool | Purpose |
|---|---|
| `get_model_structure` | Discovery — levels, apartment segments, room names, area schemes |
| `compare_rooms_with_checklist` | Codex Wonen **oppervlakte**-conformiteit per appartement (vloeroppervlak vs norm) |
| `check_window_area_compliance` | Daglicht norm (raam/vloer verhouding) |
| `get_room_furnishings` | Meubilair- en uitrusting**inventaris** per ruimte — alle categorieën, lean query met apartment + category filters. Geen compliance-check. |
| `check_room_fixtures` | Sanitair **conformiteit** per badkamer — wastafel/spiegel/tablet/douche/ligbad tegen BEEL-regels, gegroepeerd per appartement op basis van WO-bezetting. |
| `get_doors_with_rooms` | Deuren met FromRoom/ToRoom en element_id — filter op ruimtenaam of appartement |
| `get_areas_by_scheme` | Oppervlakte-totalen per schema |
| `list_revit_views` | Beschikbare views en sheets |
| `get_view_id_by_name` | view_id opzoeken op exacte viewnaam (nodig voor overrides) |
| `get_revit_view` | View exporteren als afbeelding |
| `list_levels` | Bouwlagen met hoogtes |
| `get_elements_by_category` | Ruwe elementlijst per Revit-categorie |

### `get_room_furnishings` — beschikbare category-aliassen

| Alias | Revit-categorie | Typische inhoud |
|---|---|---|
| `furniture` | Furniture | Kasten, bedden, stoelen, tafels |
| `systems` | Furniture Systems | Systeemmeubilair, werkstations |
| `casework` | Casework | Inbouwmeubelen, keukens, badkamermeubels |
| `plumbing` | Plumbing Fixtures | Wastafel, douche, ligbad, toilet |
| `plumbingeq` | Plumbing Equipment | Sanitaire toestellen |
| `specialty` | Specialty Equipment | Keukenapparaten, postbussen, speciale uitrusting |
| `lighting` | Lighting Fixtures | Verlichtingsarmaturen |
| `lightingdev` | Lighting Devices | Verlichtingstoestellen |
| `electrical` | Electrical Fixtures | Stopcontacten, schakelaars |
| `electricaleq` | Electrical Equipment | Wasmachine, droogkast, kookfornuis, warmtepomp |
| `mechanical` | Mechanical Equipment | Radiatoren, ventilatieunits, HVAC |
| `firealarm` | Fire Alarm Devices | Rookmelders, noodknoppen |
| `all` | *(alle bovenstaande)* | Standaard indien weggelaten |

Multiple aliases: `categories="furniture,casework,plumbing"`

### `get_room_furnishings` vs `check_room_fixtures` — wanneer welke?

**Gebruik `get_room_furnishings`** als de vraag gaat over *wat* er staat:
- "Welke meubels staan er in de slaapkamers?"
- "Geef me een inventaris van alle badkameruitrusting."
- "Hoeveel stopcontacten zijn er per ruimte?"
- "Zijn er HVAC-toestellen aanwezig in het appartement?"

**Gebruik `check_room_fixtures`** als de vraag gaat over *conformiteit* van sanitair:
- "Voldoet de badkamer van appartement 1.A aan de BEEL-normen?"
- "Heeft dit appartement een ligbad of een douche, en klopt dat?"
- "Zijn er genoeg wastafels voor het aantal personen?"

**Technisch verschil:**

| | `get_room_furnishings` | `check_room_fixtures` |
|---|---|---|
| Revit route | `/furnishings/byroom/cat/<c>/apt/<a>` | zelfde route + `/areas/WO` + `/rooms/` |
| Lean filters | category + apartment in Revit | category + apartment in Revit |
| Room filter | tool-laag (substring) | via rooms-route + appartement_nr |
| Output | Inventarislijst per ruimte | Conformiteitsrapport per appartement |
| Compliance | Nee | Ja — slaapkamers ≥ 3 → ligbad; < 3 → douche |

### Universal write / override tools (work on any element)

| Tool | Purpose |
|---|---|
| `override_element_color` | Highlight any element in any view — needs `element_id` + `view_id` |
| `write_element_parameter` | Write Mark or Comments on a single element |
| `write_element_parameters_bulk` | Write Mark or Comments on many elements in one transaction |

**Pattern:** query tool → `element_id` list → AI computes values → bulk write. Element category does not matter.

### Door mark workflow (example)

```
get_doors_with_rooms(apartment_filter="1.A")
  → group by ToRoom room number
  → 1 door per room: value = "02"
  → N doors per room: value = "02a", "02b", ...
  → write_element_parameters_bulk([
        { element_id: X, param: "mark", value: "02a" },
        { element_id: Y, param: "mark", value: "02b" },
    ])
```

### Compliance stamp workflow (example)

```
compare_rooms_with_checklist(apartment_filter="1.")
  → filter non-compliant rooms with their element_ids
  → write_element_parameters_bulk([
        { element_id: X, param: "comments", value: "te klein" },
    ])
```

### Sanitair conformiteit workflow (example)

```
check_room_fixtures(apartment_filter="1.A", room_type="badkamer")
  → haalt plumbing/plumbingeq op via /furnishings/byroom/cat/plumbing,plumbingeq/apt/1.A
  → rapport per appartement met slaapkamer- en personentelling uit WO-areas
  → per badkamer: wastafel / spiegel / tablet / douche / ligbad  OK of ONTBREEKT
  → totaaloordeel: CONFORM of TEKORTKOMINGEN GEVONDEN
```

### Furnishings inventaris workflow (example)

```
get_room_furnishings(apartment_filter="1.A", categories="furniture,casework")
  → roept /furnishings/byroom/cat/furniture,casework/apt/1.A aan
  → geeft gegroepeerde lijst per ruimte terug
  → elk item heeft element_id → kan worden gehighlight of beschreven via bulk write
```

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

**Category not found in response**
Some Revit categories (e.g. `plumbingeq`, `lightingdev`) may not exist in older
Revit versions. The route silently skips unavailable categories and logs a warning.
Use `get_room_furnishings(categories="all")` to see which categories have data.
