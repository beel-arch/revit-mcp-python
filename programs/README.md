# Project programs (programma van eisen)

Eén programma per **project** (niet per model — het programma bestaat vóór het model).
Geschreven door `save_project_program`, gelezen door `get_project_program` en
`compare_model_with_program`. Elke save schrijft twee bestanden:

- `<project>.json` — machine-leesbaar, de bron voor alle vergelijkingstools
- `<project>.md` — automatisch gegenereerde, leesbare samenvatting voor mensen

Beide staan in deze map (OneDrive-synced) en zijn vrij te openen/kopiëren.
De koppeling met een Revit-model loopt via het project profile
(`projects/<model>.json` → `program_link`):

```json
"program_link": {
  "mode": "external_json",
  "program": "snor-slod",
  "join_parameter": "BEEL_C_TX_Lokaalcode"
}
```

- `mode: "external_json"` — programma in deze map; vergelijking = join tussen
  model-rooms en programma-rooms.
- `join_parameter` — de room-parameter in het model die de programmacode draagt.
  Ontbreekt die (nog), dan wordt op **genormaliseerde roomnaam** gejoind.
- `mode: "key_schedule"` — programma zit ín het model (zoals JGC); geen extern
  bestand nodig, eisen worden als room-parameters gelezen.

## Schema

```json
{
  "project_name": "snor-slod",
  "title": "Sint-Norbertus & Sint-Lodewijk",
  "source_documents": ["BIJLAGE VI_Programma van Eisen_StLod_StNor_20240502.xlsx"],
  "extracted": "2026-06-11",
  "rooms": [
    {
      "code": "02.03",
      "name": "Theorielokaal 12P (aanpasbaar)",
      "cluster": "II. THEORIELOKALEN EERSTE GRAAD",
      "count": 2,
      "area_m2": 37.0,
      "total_area_m2": 74.0,
      "occupancy": 12,
      "zone": "Semi-publiek",
      "use": "Breed gebruik",
      "requirements": {}
    }
  ],
  "relations": [
    {"a": "02.03", "b": "13.01", "type": "adjacent", "note": "ontsluiting via circulatie"}
  ]
}
```

- `rooms[].code` — de **join key**: numeriek (Scholen van Vlaanderen `02.03`) of
  naam-gebaseerd (JGC `IO-2`). `null` mag; dan joint de vergelijking op naam.
- `rooms[].requirements` — vrije dict voor lokaalfiche-details (vrije hoogte,
  daglicht, sanitair, afwerking, ...). Gevuld tijdens program-intake; de exacte
  velden verschillen per bron.
- `relations` — ruimtelijke relaties (Schema Ruimtelijke Relaties). Gecheckt door
  `check_program_relations` via de deur-adjacentiegraaf.

## Intake (hoe komt een programma hier terecht?)

Zie de `revit-query` skill, sectie "Program-intake". Kort: de AI leest de
brondocumenten (PvE-Excel via openpyxl; lokaalfiches/PDF via Claude zelf),
bouwt de JSON, en roept `save_project_program` aan. **Eenmalig per bron** —
daarna nooit meer de docx/xlsx herlezen.

Beschikbare parsers in de venv: `openpyxl` (xlsx), `python-docx` (docx), `xlrd`
(oude xls). Elke bron is anders — de extractie verschilt per document, de
opslagvorm hier is altijd dezelfde. Bron-specifieke kennis (bv. de tabelstructuur
van Scholen van Vlaanderen-lokaalfiches: Kenmerken / Toepassing / Eisen met
EIS-ID's) hoort in de intake-sessie thuis, niet in code.
