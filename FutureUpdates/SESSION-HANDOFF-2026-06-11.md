# Sessie-handoff 2026-06-11 — project profile + program architectuur geïmplementeerd

> Voor de volgende Claude-sessie: lees dit + CLAUDE.md. Alles hieronder is gebouwd,
> getest (compile + registratie + functionele mocks) en NOG NIET GECOMMIT.

## Wat er vandaag gebouwd is

**Drie kennislagen (alle data, geen code-specificiteit):**
- `rulesets/` — herbruikbare normen. `codex-wonen.md` = canonieke leidraad sociale
  woningbouw (oppervlaktes, classificatie, sanitair, daglicht). Profielen verklaren
  `"rulesets": ["codex-wonen"]` (gevalideerd tegen de map).
- `programs/<project>.json` + leesbare `.md` — programma van eisen per project.
  Eerste instantie: `snor-slod` (78 ruimtetypes uit de PvE-Excel van de Scholen
  van Vlaanderen outputspecificaties — VOORBEELD, geen sjabloon).
- `projects/<model>.json` — modelconventies (grouping hiërarchisch, room_type_parameter,
  occupancy, program_link, rulesets). Eerste instantie: THELLO (UnitID-grouping,
  let op typefout `THELL0_C_TX_UnitTypologie` met nul — letterlijk zo in het model).

**Nieuwe MCP-tools (totaal 47):** get/save_project_profile, discover_room_parameters,
get_rooms_overview, get/save_project_program, compare_model_with_program,
check_program_relations, export_program_comparison (xlsx → exports/).

**Geparametriseerde routes (pyRevit, vereisen Revit-reload):** rooms.py
(+parameter_discovery, +POST overview), model_structure.py (+groupby/<param>),
rooms_with_doors.py, furnishings_by_room.py, doors.py (elk +groupby-variant).
Bestaande apt/-routes byte-compatibel; KSS-tools ongewijzigd.

**Tool-laag profile-aware:** unit_filter (prefix op profiel-grouping) i.p.v.
apartment_filter bij de generieke tools; modelnaam via lichte /status/ route.

**Skill v3.0.0** (`revit-query/SKILL.md`): co-pilot-toestandsmachine (profiel →
programma → fase-acties), project-setup interview, program-intake (2 use-cases:
model toetsen aan documenten / documenten → modelopzet-voorstel).

**venv:** `python-docx` toegevoegd via `uv add` (pyproject + lock bijgewerkt).

## Kernprincipes (gebruiker is hier expliciet over)

1. **UNIVERSEEL, niet project-specifiek.** SNOR-SLOD/JGC/THELLO zijn voorbeelden/
   testdata. Projectnamen horen alleen in data (programs/, projects/) en
   docstring-voorbeelden — nooit in logica.
2. **Lean queries** — filteren ín Revit, niet erna.
3. **Letterlijke parameternamen** uit discovery, nooit reconstrueren.
4. **Eenmalige extractie** van brondocumenten → JSON; bron nooit herlezen.
5. Codex-wonen blijft als gedeelde ruleset (meerdere sociale woonprojecten).

## Openstaande acties

1. **MCP reconnect faalde met -32000** ondanks gezonde server (initialize-handshake
   getest OK; 4 verweesde main.py-processen opgeruimd; uv-sync na python-docx was
   vermoedelijke timeout-oorzaak). Gebruiker herstart Claude Code — check na
   herstart of de 5 nieuwe program-tools zichtbaar zijn.
2. **pyRevit Reload in Revit** nodig voor de nieuwe routes (groupby/overview/discovery).
3. **Niets is gecommit** — hele changeset staat in de working tree.
4. Eerste echte test: THELLO-model openen → get_project_profile → get_rooms_overview
   (level="N01"); KSS-rapport als regressie; daarna program-intake testen.
5. Verificatiematrix-export gebruikt nog niet de EIS-ID's uit lokaalfiches
   (requirements-veld bestaat, intake vult het later).

## Architectuurdocs (bijgewerkt vandaag)

`FutureUpdates/project-profile-architecture.md` en `program-to-model-architecture.md`
bevatten de JGC/THELLO-casestudies en het volledige ontwerp.
