# Project profiles

Eén JSON-bestand per Revit-model, gekeyed op de modelnaam (`doc.Title`).
Geschreven door de MCP-tool `save_project_profile`, gelezen door `get_project_profile`
en intern door alle profile-aware query-tools.

Zie `FutureUpdates/project-profile-architecture.md` voor het ontwerp.

## Schema

```json
{
  "model_name": "<doc.Title — wordt automatisch gezet bij save>",
  "project_name": "KSS",
  "grouping": [
    {"derive": {"from": "BEEL_C_TX_AppartementNummer", "rule": "prefix"}, "label": "blok"},
    {"parameter": "BEEL_C_TX_AppartementNummer", "label": "appartement"}
  ],
  "room_type_parameter": null,
  "occupancy": {"source": "area_scheme", "scheme": "WO", "encoding": "name_regex",
                "pattern": "^(?P<slaapkamers>\\d+)/(?P<personen>\\d+)$"},
  "program_link": {"mode": "external_json", "program": "kuurne",
                   "join_parameter": null},
  "rulesets": ["codex-wonen"],
  "room_classification": {"badkamer": ["bad", "douche"]},
  "family_keywords": {"toilet": ["toilet"]}
}
```

- `grouping`: hiërarchische lijst, grof → fijn. Het **laatste niveau met een `parameter`**
  is de filter-as die de query-tools gebruiken. `derive`-niveaus zijn afgeleid (prefix)
  en hebben geen eigen Revit-parameter.
- Parameternamen **letterlijk** overnemen zoals gedumpt (THELLO bevat bv. de typefout
  `THELL0_C_TX_UnitTypologie` met een nul — die hoort zo in het profiel).
- `program_link.mode`: `key_schedule` (programma zit in het model als key schedule),
  `external_json` (join met `programs/<project>.json`, optioneel `join_parameter` =
  room-parameter met de programmacode) of `none`.
- `rulesets`: namen van herbruikbare normen uit `rulesets/` (bv. `codex-wonen` voor
  sociale woningbouw — gedeeld over meerdere projecten).
- Geen profiel aanwezig = fallback naar de KSS-conventie (`BEEL_C_TX_AppartementNummer`).
