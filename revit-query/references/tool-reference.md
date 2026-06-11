# Tool Reference — Revit-Connector MCP

## Project profile (algemeen)

De grouping-as van alle profile-aware tools komt uit `projects/<modelnaam>.json`
(zie `projects/README.md`). Geen profiel = fallback `BEEL_C_TX_AppartementNummer`.
`unit_filter` parameters zijn altijd een **prefix-match op de grouping-waarde**.

## get_project_profile

**Purpose:** Profiel van het open model tonen. No parameters.
Returns grouping-hiërarchie, filter-as, occupancy, programmalink + raw JSON.
Geen profiel → instructie om het project-setup interview te draaien.

---

## save_project_profile

**Purpose:** Profiel valideren en opslaan als `projects/<modelnaam>.json`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `profile_json` | string | yes | Volledig profiel als JSON-string. `model_name` wordt automatisch gezet. Schema: zie `projects/README.md`. |

Validatie: `grouping` lijst (elk niveau `parameter` of `derive.from`),
`program_link.mode` ∈ key_schedule/external_json/none.

---

## get_project_program / save_project_program

**get_project_program** — programma tonen.
| Parameter | Type | Default | Description |
|---|---|---|---|
| `project_key` | string | `""` | bv. `"snor-slod"`. Leeg = via `program_link` van het open model. |

**save_project_program** — programma opslaan (JSON + leesbare .md in `programs/`).
| Parameter | Type | Required | Description |
|---|---|---|---|
| `program_json` | string | yes | Schema: zie `programs/README.md` (rooms met code/name/count/area_m2/..., relations). |
| `project_key` | string | yes | Korte sleutel, bv. `"snor-slod"`, `"kuurne"`. |

---

## compare_model_with_program / export_program_comparison

PvE-vergelijking: per programma-ruimtetype eis-aantal vs model-aantal en min m²
vs werkelijke oppervlaktes. Join via `program_link.join_parameter` (room-parameter
met de code) of anders genormaliseerde roomnaam. Toont ook model-rooms zonder match.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `project_key` | string | `""` | Leeg = via profiel van het open model. |
| `unit_filter` | string | `""` | Prefix op grouping-waarde (lean, in Revit). |
| `level` | string | `""` | Exacte levelnaam (lean, in Revit). |
| `file_name` | string | `""` | (alleen export) bestandsnaam; default `verificatie_<project>_<datum>.xlsx`. |

Export schrijft xlsx in verificatiematrix-stijl naar `exports/`.

---

## check_program_relations

Toetst `relations` uit het programma tegen de deur-adjacentiegraaf
(twee ruimtes zijn verbonden als ze een deur delen — open verbindingen zonder
deur zijn niet detecteerbaar). Codes worden via het programma naar namen vertaald;
matching op genormaliseerde roomnaam.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `project_key` | string | `""` | Leeg = via profiel. |
| `unit_filter` | string | `""` | Prefix op grouping-waarde. |

---

## get_model_structure
**Purpose:** Lightweight discovery. No parameters. Always fast. Profile-aware.

Returns:
- `levels` — list of `{name, elevation_m}`, sorted low to high
- grouping-waarden van de profiel-parameter (KSS: apartment numbers zoals `1.A.Niv 0.01`;
  THELLO: UnitIDs zoals `C104`) + bij KSS afgeleide `building_segments`
- placed/unplaced room counts
- `room_name_variants` — unique Revit room names in the model
- `area_schemes` — e.g. `WO`, `BVO`, `GBO`, `Brand`
- `views` — count by type (FloorPlan, Section, ThreeD, …)
- `family_categories` — top family categories by count

Use this to populate filter values before calling any heavy tool.

---

## discover_room_parameters

**Purpose:** Discovery voor het project-setup interview. No parameters.

Returns per gevulde tekstparameter op rooms: fill-rate, aantal distinct values
(capped op 200), max 15 voorbeelden. Lege parameters (import-ruis) worden
weggefilterd. Plus placed/unplaced telling.

---

## get_rooms_overview

**Purpose:** Lean room-lijst op elk model — vervangt `get_elements_by_category("Rooms")`
(dat geeft voor rooms geen namen terug). Profile-aware grouping.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `level` | string | `""` | Exacte levelnaam (case-insensitief), bv. `"100"`, `"N01"`. Gefilterd in Revit. |
| `unit_filter` | string | `""` | Prefix op de grouping-waarde (profiel). Gefilterd in Revit. |
| `extra_parameters` | string | `""` | Comma-separated parameternamen om per room mee te geven, letterlijk zoals in het model (bv. `"Room KEY,JGC_BEEL_C_AR_VerschilOppervlakte"`). |
| `include_unplaced` | bool | `false` | Ook unplaced rooms (area 0) tonen. |

Returns per room: id, name, number, area_m2, level, group (+ gevraagde params).
Bij >150 resultaten: samenvatting per groep i.p.v. volledige lijst.

---

## compare_rooms_with_checklist

**Purpose:** Codex Wonen / VMSW area compliance per apartment.

Parameters:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `apartment_filter` | string | `""` | Prefix match on apartment number. `"1."` = all of gebouw 1 (1.A + 1.B). `"1.A"` = block 1.A only. `"1.A.Niv 2"` = level-2 apartments in 1.A. |
| `room_type_filter` | string | `""` | Substring match on room name or rule key. `"badkamer"` = bathrooms only. `"slaap"` = all bedroom types. `"leef"` = living rooms. |

Minimum area rules applied:
| Room type | Rule |
|---|---|
| Leefruimte | 18 + 2 × personen m² |
| Keuken | 4 + 0.5 × personen m² |
| Slaapkamer ouders | 11 m² |
| Slaapkamer kind (1p) | 7 m² |
| Slaapkamer kind (2p, name contains "2p") | 12 m² |
| Badkamer (zonder toilet) | 2 + 0.5 × personen m² |
| Badkamer (met toilet) | 3 + 0.5 × personen m² — detected via Plumbing Fixtures with "Toilet" in family name |
| Inkomzone | 1.5 m² |
| Berging | 3 + 0.5 × personen m² |

Persons and bedroom count come from the WO area linked to the apartment number
via the `BEEL_C_TX_AppartementNummer` parameter on rooms.

---

## check_window_area_compliance

**Purpose:** Belgian daylight norm — window area vs. floor area ratio.

Parameters:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `apartment_filter` | string | `""` | Same substring match as above. |

Norms applied:
- Leefruimte: window area ≥ 1/6 floor area
- Slaapkamers: window area ≥ 1/8 floor area
- Other rooms: not applicable

Note: fetches parameters per window (one API call each) — slow on large models.
Use `apartment_filter` to limit scope.

---

## get_room_furnishings

**Purpose:** Furnishing/equipment inventory grouped by room. Profile-aware.

Parameters:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `unit_filter` | string | `""` | Prefix op de grouping-waarde (profiel). Gefilterd in Revit (lean). |
| `room_name_filter` | string | `""` | Case-insensitive substring match on room name. `"badkamer"`, `"chambre"`. Gefilterd in de tool-laag. |
| `categories` | string | `"all"` | Comma-separated category-aliassen (furniture, casework, plumbing, …). Gefilterd in Revit. |

Returns family name, type name, mark, and element ID per item, grouped by room.

---

## get_doors_with_rooms / get_rooms_with_doors / write_door_marks_from_room

Profile-aware deur-tools.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `room_name` / `room_name_filter` | string | `""` | Substring op kamernaam (route-level filter). |
| `unit_filter` | string | `""` | Prefix op de grouping-waarde (profiel). |

`get_doors_with_rooms`: deur-centrisch (FromRoom/ToRoom, zwenkrichting).
`get_rooms_with_doors`: ruimte-centrisch — toont ook ruimtes zonder deur.
`write_door_marks_from_room`: schrijft marks `<grouping-waarde>-<roomnummer>` met
letter-suffix bij meerdere deuren per ruimte (bulk, één transactie).

---

## get_areas_by_scheme

**Purpose:** Area totals for a specific scheme.

Parameters:
| Parameter | Type | Required | Description |
|---|---|---|---|
| `scheme_name` | string | yes | Exact scheme name, e.g. `"WO"`, `"BVO"`, `"GBO"`. Use `get_model_structure` to list available schemes. |

---

## list_revit_views / get_revit_view

**list_revit_views** — no parameters. Returns all exportable views organised by type.

**get_revit_view**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `view_name` | string | yes | Exact view name as returned by `list_revit_views`. |

Returns base64 PNG image.

---

## get_elements_by_category

**Purpose:** Raw element list for any Revit category.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `category` | string | yes | Revit category name, e.g. `"Doors"`, `"Windows"`, `"Plumbing Fixtures"`. |

Returns ID, family name, type name, level per element.

---

## list_levels

No parameters. Returns all levels with name and elevation in metres.
