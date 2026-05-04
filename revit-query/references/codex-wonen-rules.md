# Codex Wonen / VMSW — Minimum Area Rules

Source: BEEL Checklist Codex Wonen (VMSW)

## How apartments are identified

Each Revit Room must have the parameter `BEEL_C_TX_AppartementNummer` filled in.
This links the room to a WO area whose number matches that value.

The WO area name encodes occupancy as `"slaapkamers/personen"` (e.g. `"3/4"` = 3 bedrooms, 4 persons).

## Room classification keywords

| Rule key | Room name must contain |
|---|---|
| `leefruimte` | leef, woon, zitkamer, zithoek, eethoek |
| `keuken` | keuken |
| `slaapkamer_ouders` | ouder, master, hoofd |
| `slaapkamer_kind` | kinder, kind, slaap, chambre, bedroom |
| `slaapkamer_kind_gedeeld` | same as kind + "2p" in name |
| `badkamer` | bad, douche, sanitair |
| `inkomzone` | inkom, hal, gang, vestiaire, entree, entrée |
| `berging` | berg, opslag, stock, stockage |
| `toilet` | toilet, wc (no minimum applies) |

## Toilet detection in badkamer

When a room is classified as `badkamer`, the tool checks Plumbing Fixtures
in that room for a family name containing `"toilet"` (case-insensitive).

- Found → applies `badkamer_met_toilet` rule: **3 + 0.5 × personen m²**
- Not found → applies `badkamer` rule: **2 + 0.5 × personen m²**

## Minimum areas

| Rule | Formula | Example (4 persons) |
|---|---|---|
| Leefruimte | 18 + 2p | 26 m² |
| Keuken | 4 + 0.5p | 6 m² |
| Slaapkamer ouders | 11 | 11 m² |
| Slaapkamer kind (1p) | 7 | 7 m² |
| Slaapkamer kind (2p) | 12 | 12 m² |
| Badkamer (zonder toilet) | 2 + 0.5p | 4 m² |
| Badkamer (met toilet) | 3 + 0.5p | 5 m² |
| Inkomzone | 1.5 | 1.5 m² |
| Berging | 3 + 0.5p | 5 m² |
| Toilet | geen minimum | — |
