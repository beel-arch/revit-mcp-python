# Tool Reference — Revit-Connector MCP

## get_model_structure
**Purpose:** Lightweight discovery. No parameters. Always fast.

Returns:
- `levels` — list of `{name, elevation_m}`, sorted low to high
- `apartment_numbers` — all unique apartment numbers (e.g. `1.A.Niv 0.01`)
- `building_segments` — derived leading parts before "Niv" (e.g. `1.A`, `1.B`, `2.C`)
- `room_name_variants` — unique Revit room names in the model
- `area_schemes` — e.g. `WO`, `BVO`, `GBO`, `Brand`
- `views` — count by type (FloorPlan, Section, ThreeD, …)
- `family_categories` — top family categories by count

Use this to populate filter values before calling any heavy tool.

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

## get_furniture_by_room

**Purpose:** Furniture inventory grouped by room.

Parameters:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `room_name_filter` | string | `""` | Case-insensitive substring match on room name. `"badkamer"` = bathrooms. `"slaap"` = bedrooms. |

Returns family name, type name, mark, and element ID per item.

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
