---
name: revit-query
description: Efficient Revit model querying via MCP, on any project — with co-pilot behavior. Loads the project profile first (grouping conventions per model), knows the project lifecycle state (profile → program → checks), runs setup interviews and program intake for new projects, and always calls get_model_structure before targeted queries. Use when user asks about buildings/blocks/units ("gebouw 1", "blok A", "unit C104"), room types, levels, area compliance, daylight checks, furnishings inventory, bathroom fixture compliance, PvE/programma-vergelijking, or wants to set up a new project profile or program. Requires Revit-Connector MCP to be connected.
metadata:
  author: Frederik Van Nespen
  version: 3.0.0
  mcp-server: Revit-Connector
---

# Revit Query

## Kernidee: drie kennislagen

| Laag | Leeft | Opslag | Tools |
|---|---|---|---|
| **Rulesets** (normen) | over projecten heen | `rulesets/*.md` (bv. codex-wonen) | checklist-tools |
| **Programma** (PvE) | per project, bestaat vóór het model | `programs/<project>.json` + leesbare `.md` | program-tools |
| **Profiel** (modelconventies) | per Revit-model | `projects/<model>.json` | alle query-tools |

Elk project structureert zijn rooms anders: KSS groepeert op appartementnummer
(`BEEL_C_TX_AppartementNummer`), JGC op ruimtegroep, THELLO op UnitID. Het profiel
legt dat vast; alle query-tools lezen het automatisch. Geen profiel = KSS-fallback.
De `unit_filter` parameter filtert altijd op een **prefix van de grouping-waarde
uit het profiel** — wat dat concreet is, verschilt dus per project.

Alle drie de lagen zijn gewone bestanden in de repo (OneDrive-synced): de gebruiker
kan ze los openen, kopiëren en delen. Elke programma-save schrijft naast de JSON
een leesbare `.md`-samenvatting.

## Workflow

### Step 0: Co-pilot — ken de projectfase en benoem de volgende stap

Bij de eerste model-specifieke vraag van de sessie: roep `get_project_profile` op
en bepaal waar het project staat. **Meld actief wat er is, wat er ontbreekt, en wat
de logische volgende stap is** — de gebruiker hoeft de tools niet te kennen.

```
get_project_profile
│
├─ Geen profiel?
│   → "Dit model ken ik nog niet. Zal ik het project-setup interview doen (±5 min)?"
│     (Gebruiker wil eerst gewoon iets opzoeken? Prima — KSS-fallback, maar meld
│      dat grouping-filters op niet-KSS-modellen leeg zullen zijn.)
│
├─ Profiel, maar program_link.mode = "none"?
│   → "Ik ken de structuur, maar heb geen programma om tegen te toetsen.
│      Is er een PvE / outputspecificatie / ruimtelijst? Wijs me het document,
│      dan extraheer ik het eenmalig (program-intake)."
│     (Niet elk project hééft een programma — eens bevestigd 'geen', niet blijven vragen.)
│
├─ program_link.mode = "key_schedule"?
│   → Programma zit ín het model. Eisen opvragen via get_rooms_overview
│     extra_parameters (bv. JGC_BEEL_C_AR_VerschilOppervlakte) — niet zelf rekenen.
│
└─ program_link.mode = "external_json"?
    → Vergelijking beschikbaar: compare_model_with_program (aantallen + min m²),
      check_program_relations (deur-adjacentie), export_program_comparison (xlsx).
      Stel proactief een gap-rapport voor wanneer de gebruiker over voortgang,
      conformiteit of het programma praat.
```

Verklaarde rulesets (bv. `codex-wonen`) bepalen welke norm-tools van toepassing
zijn; zie `rulesets/README.md`.

### Step 1: Discover — always first for ambiguous queries

If the user's request refers to a specific building, unit, level, room type, or area
scheme, call `get_model_structure` before anything else.

Triggers that require discovery:
- Mentions a building or block or unit: "gebouw 1", "blok A", "unit C104", "ruimtegroep BW"
- Mentions a level: "niveau 2", "gelijkvloers", "level N01"
- Mentions a room type: "badkamers", "slaapkamers", "chambres"
- Mentions an area scheme: "WO", "BVO", "GBO"

Skip discovery when the request is fully unambiguous:
- "run the full compliance check on everything"
- "list all views"

Let op de placed/unplaced-telling in het resultaat: unplaced rooms (area 0) vallen
buiten de meeste checks — vermeld dit expliciet in rapporten als het aantal groot is.

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
| Alle rooms op een level | `get_rooms_overview` | `level="N01"` |
| Rooms van één unit, met extra params | `get_rooms_overview` | `unit_filter="C104"`, `extra_parameters="..."` |
| Oppervlakte-conformiteit, gebouw 1 (KSS) | `compare_rooms_with_checklist` | `apartment_filter="1."` |
| Alleen badkamers in blok 1.A (KSS) | `compare_rooms_with_checklist` | `apartment_filter="1.A"`, `room_type_filter="badkamer"` |
| Daglicht niveau 2, blok 1.A (KSS) | `check_window_area_compliance` | `apartment_filter="1.A.Niv 2"` |
| Meubels/inventaris in slaapkamers | `get_room_furnishings` | `room_name_filter="slaap"` |
| Keukens en kasten in unit 1.A | `get_room_furnishings` | `unit_filter="1.A"`, `categories="furniture,casework"` |
| Sanitair conformiteit badkamers (KSS) | `check_room_fixtures` | `apartment_filter="1."`, `room_type="badkamer"` |
| Deuren per ruimte / zwenkrichting | `get_doors_with_rooms` | `room_name` en/of `unit_filter` |
| Ruimtes zonder deur | `get_rooms_with_doors` | `unit_filter` |
| WO areas / appartementtype | `get_areas_by_scheme` | `scheme_name="WO"` |
| "Voldoet het model aan het PvE?" | `compare_model_with_program` | evt. `level` / `unit_filter` |
| "Welke lokalen ontbreken nog?" | `compare_model_with_program` | — (gap-rapport) |
| Verificatiematrix voor de opdrachtgever | `export_program_comparison` | → xlsx in `exports/` |

## Project-setup interview (nieuw model zonder profiel)

Doel: in één gesprek de structuurconventies van het model vastleggen in
`projects/<model>.json`. **Inspect first, then confirm** — stel nooit een blanco
vraag waarvan het antwoord in het model staat.

```
1. get_model_structure          → levels, room names, area schemes, placed/unplaced
2. discover_room_parameters     → gevulde tekstparams met fill-rate + voorbeelden
3. Identificeer grouping-kandidaten: hoge fill-rate, herhalende gestructureerde
   waarden (bv. "C104", "1.A.Niv 0.01", "BW-5").
4. Bevestig per bevinding met ÉÉN vraag:
   "Ik zie dat rooms een parameter 'THELLO_C_TX_UnitID' hebben met waarden als
    C104, A112. Is dit hoe units gegroepeerd worden in dit project?"
5. Vraag naar hiërarchie (grof → fijn): zit er een gebouw/blok-niveau in de
   waarden (prefix)? → derive-niveau in het profiel.
6. Occupancy: welk area scheme of welke parameter draagt de bezetting? (mag "none")
7. Programmalink: zit het programma in het model (key schedule met eis-parameters,
   zoals JGC) → "key_schedule"; extern document → "external_json"; anders "none".
8. Classificatie: sample roomnamen, stel keyword-mapping voor ("chambre" → slaapkamer?).
9. save_project_profile(profile_json)
```

Harde regels bij het profiel:
- **Parameternamen letterlijk overnemen** zoals discover_room_parameters ze toont —
  nooit reconstrueren (THELLO bevat bv. de typefout `THELL0_C_TX_UnitTypologie` met
  een nul; die hoort zó in het profiel).
- **Fill-rate telt**: een parameter die op 10% van de rooms gevuld is, is geen
  grouping-as. Meld de gebruiker als de kandidaat onvolledig gevuld is.
- **Unplaced rooms vermelden** als het aantal significant is.

## Program-intake (programma van eisen verwerken)

Twee use-cases, één resultaat: `programs/<project>.json` (+ leesbare `.md`).

**Use-case 1 — er is een model, en documenten om tegen te toetsen.**
Extraheer het programma, koppel het via het profiel
(`program_link: {"mode": "external_json", "program": "<key>", "join_parameter": ...}`),
en draai `compare_model_with_program`.

**Use-case 2 — er zijn alleen documenten; het model moet nog gebouwd worden.**
Extraheer het programma (kan vóór er een profiel bestaat — het is gekeyed op
project, niet op model) en lever de gebruiker een **modelopzet-voorstel**:
- de room schedule, voorgeschreven uit het programma (code, naam, aantal, min m²)
- de conventie-aanbeveling: zet de programmacode in een room-parameter
  (`join_parameter`), dan werkt elke latere check automatisch
- het draft-profiel (grouping = cluster/code-hiërarchie uit het programma)

**Extractie-werkwijze (eenmalig per bron — daarna nooit meer de bron herlezen):**
```
1. Verken de bron(nen) en zoek de meest gestructureerde eerst (Excel vóór
   docx vóór pdf). openpyxl, python-docx en xlrd zitten in de venv.
2. Haal per ruimtetype minstens op: code (als die bestaat), naam, aantal,
   min m², bezetting. Alles wat verder bruikbaar is → requirements (vrije dict).
3. Relaties (adjacentie-eisen), als de bron ze heeft → relations (a/b-paren).
4. Bouw de JSON volgens programs/README.md en roep save_project_program aan.
5. Koppel in het profiel (save_project_profile → program_link).
```
**Elke bron is anders** — dat is het punt van de intake. De extractie is AI-werk
en verschilt per document; de **opslagvorm is altijd dezelfde JSON**, en dáár
werken alle vergelijkingstools op. Codes mogen numeriek (`02.03`) of
naam-gebaseerd (`IO-2`) zijn; zonder `join_parameter` joint de vergelijking op
genormaliseerde roomnaam. Een programma kan ook dun zijn (bv. enkel een
appartementenmix voor een woonproject) — dat is evengoed geldig.

Reeds verwerkte voorbeelden (ter referentie, géén sjabloon):
- `programs/snor-slod.json` — Scholen van Vlaanderen outputspecificaties:
  PvE-Excel (hiërarchie + m²), lokaalfiches met tabellen Kenmerken/Toepassing/
  Eisen (EIS-ID's!), verificatiematrix als verwacht eindformaat.
- JGC Room-by-Room matrix — programma als eisenmatrix; in dat model bovendien
  al ingebed als key schedule (`program_link.mode = "key_schedule"`).

`export_program_comparison` schrijft de vergelijking als xlsx
(Code | Eistekst | Voldoet/Voldoet niet | Motivering) naar `exports/` —
bruikbaar voor elk project dat een toetsbaar programma heeft.

## Available Tools

| Tool | Purpose |
|---|---|
| `get_project_profile` | Profiel van het open model — grouping-as, classificatie, programmalink, rulesets |
| `save_project_profile` | Profiel valideren + opslaan (deliverable van het setup-interview) |
| `get_project_program` | Programma van eisen tonen (via profiel of project_key) |
| `save_project_program` | Programma valideren + opslaan als JSON + leesbare .md (deliverable van de intake) |
| `compare_model_with_program` | PvE-vergelijking: aantallen + min m² per ruimtetype, join op code of naam |
| `check_program_relations` | Ruimtelijke relaties uit het programma toetsen via de deur-adjacentiegraaf |
| `export_program_comparison` | Vergelijking als xlsx in verificatiematrix-stijl → `exports/` |
| `get_model_structure` | Discovery — levels, grouping-waarden (profile-aware), room names, area schemes, placed/unplaced |
| `discover_room_parameters` | Discovery — gevulde tekstparams op rooms met fill-rate (voor het interview) |
| `get_rooms_overview` | Lean room-lijst — naam/nummer/area/level + extra params, filter op level en unit (profile-aware) |
| `compare_rooms_with_checklist` | **KSS** — Codex Wonen oppervlakte-conformiteit per appartement |
| `check_window_area_compliance` | **KSS** — daglichtnorm (raam/vloer verhouding) |
| `get_room_furnishings` | Meubilair- en uitrusting**inventaris** per ruimte — lean query met unit + category filters (profile-aware) |
| `check_room_fixtures` | **KSS** — sanitair conformiteit per badkamer tegen BEEL-regels (WO-bezetting) |
| `get_doors_with_rooms` | Deuren met FromRoom/ToRoom en element_id — filter op ruimtenaam of unit (profile-aware) |
| `get_rooms_with_doors` | Ruimtes met hun deuren (omgekeerde richting) — toont ook ruimtes zonder deur (profile-aware) |
| `write_door_marks_from_room` | Deur-marks schrijven: `<grouping-waarde>-<roomnummer>` + suffix (profile-aware) |
| `get_areas_by_scheme` | Oppervlakte-totalen per schema |
| `list_revit_views` | Beschikbare views en sheets |
| `get_view_id_by_name` | view_id opzoeken op exacte viewnaam (nodig voor overrides) |
| `get_revit_view` | View exporteren als afbeelding |
| `list_levels` | Bouwlagen met hoogtes |
| `get_elements_by_category` | Ruwe elementlijst per Revit-categorie (rooms: gebruik `get_rooms_overview`) |

Tools gemarkeerd **KSS** voeren de ruleset `codex-wonen` uit (zie
`rulesets/codex-wonen.md`) en zijn zinvol op elk woonproject dat die ruleset in
zijn profiel verklaart — niet alleen KSS. De overige tools zijn profile-aware en
werken op elk model.

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

**Gebruik `check_room_fixtures`** (KSS) als de vraag gaat over *conformiteit* van sanitair:
- "Voldoet de badkamer van appartement 1.A aan de BEEL-normen?"
- "Heeft dit appartement een ligbad of een douche, en klopt dat?"

### Universal write / override tools (work on any element)

| Tool | Purpose |
|---|---|
| `override_element_color` | Highlight any element in any view — needs `element_id` + `view_id` |
| `write_element_parameter` | Write Mark or Comments on a single element |
| `write_element_parameters_bulk` | Write Mark or Comments on many elements in one transaction |
| `swap_family_type` | Change the family type of one or more elements — works for all categories |

**Pattern:** query tool → `element_id` list → AI computes values → bulk write. Element category does not matter.

### Rooms overview workflow (example — werkt op elk model)

```
get_rooms_overview(level="N01")
  → rooms gegroepeerd op de profiel-grouping (bv. UnitID)
  → >150 rooms: samenvatting per groep — verfijn met unit_filter

get_rooms_overview(unit_filter="C104",
                   extra_parameters="THELL0_C_TX_UnitTypologie,THELLO_C_AR_UnitTotalArea")
  → rooms van unit C104 met typologie en unit-oppervlakte erbij
```

Bij `program_link.mode = "key_schedule"` (bv. JGC): de eis- en verschilparameters
zitten al op de rooms — vraag ze op via `extra_parameters`
(bv. `"JGC_BEEL_C_AR_MinimaleOppervlakte,JGC_BEEL_C_AR_VerschilOppervlakte"`)
in plaats van zelf te rekenen. Het model rekent het verschil al uit.

### Programma-vergelijking workflow (example)

```
get_project_profile
  → program_link: {"mode": "external_json", "program": "snor-slod",
                   "join_parameter": "BEEL_C_TX_Lokaalcode"}

compare_model_with_program()
  → per programmacode: eis-aantal vs model-aantal, min m² vs werkelijke m²
  → "02.03  Theorielokaal 12P (aanpasbaar)   eis 2 | model 2 | min 37  ✓"
  → "02.05  Theorielokaal 16P                eis 4 | model 3 | ✗ aantal: 3 i.p.v. 4"
  → + model-rooms zonder programma-match (circulatie, techniek)

export_program_comparison()
  → exports/verificatie_snor-slod_<datum>.xlsx (verificatiematrix-stijl)

check_program_relations()
  → per relatie a↔b: ✓ gedeelde deur / ✗ geen / ? ruimte niet gevonden
```

### Rooms with doors workflow (example)

```
get_rooms_with_doors(unit_filter="1.A")
  → rooms_without_doors > 0 → welke ruimtes missen een deur (direct bovenaan getoond)
  → per ruimte met deur: family type, breedte, side (from_room/to_room)
  → side="from_room" = deur draait weg van de ruimte
  → side="to_room"   = deur draait de ruimte in
```

### Door mark workflow (example)

```
get_doors_with_rooms(unit_filter="1.A")
  → group by ToRoom room number
  → 1 door per room: value = "02"
  → N doors per room: value = "02a", "02b", ...
  → write_element_parameters_bulk([...])
```

### Compliance stamp workflow (example, KSS)

```
compare_rooms_with_checklist(apartment_filter="1.")
  → filter non-compliant rooms with their element_ids
  → write_element_parameters_bulk([
        { element_id: X, param: "comments", value: "te klein" },
    ])
```

## Appartementtype altijd meenemen (KSS)

De WO-areas bevatten het appartementtype in de naam, formaat `slaapkamers/personen`
(bv. `3/5`, `2/3`, `1/2`). Het **area number** = het appartementnummer (bv. `1.A.Niv 0.01`).

**Regel:** Elk rapport, tabel of CSV over appartementen bevat altijd de kolom
`Appartement_Type` (bv. `3/5`). Workflow: `get_areas_by_scheme(scheme_name="WO")` →
join op appartement_nr.

Het type bepaalt ook de conformiteitsregels:
- `personen >= 5` → 2 wastafels/spiegels/tablets vereist (anders 1)
- `slaapkamers >= 3` → ligbad verplicht — `slaapkamers < 3` → douche verplicht

Op niet-KSS-projecten: check het profiel (`occupancy` en `typology_parameter`) voor
het equivalent (bv. THELLO `THELL0_C_TX_UnitTypologie` = T1/T2/...).

## Rules

- **One question at a time.** Ask the most important clarifying question first.
- **"Opnieuw" = nieuwe query.** Als de gebruiker "opnieuw", "nogmaals" of "check again"
  zegt, altijd een nieuwe tool-call uitvoeren. Nooit eerder in de sessie verkregen data
  hergebruiken — het model kan gewijzigd zijn.
- **Profiel = waarheid.** Parameternamen komen uit het profiel, letterlijk. Bij twijfel
  of het profiel nog klopt (model gewijzigd?): discover_room_parameters opnieuw.
- **State assumptions.** If you infer a filter value, say so before calling the tool.
- **Prefer filtered calls.** A small report that fits in context beats a full-model
  report saved to a file.
- **Report size matters.** If a result exceeds context, it gets saved to a temp file
  and requires a subagent to read — expensive. Use filters to prevent this.
- **Unplaced rooms benoemen.** Bij modellen met veel unplaced rooms (zie
  get_model_structure): vermeld dit in elk rapport — area-checks slaan ze over.

## Reference Files

Consult these when you need more detail — only load as needed:

- `references/tool-reference.md` — full parameter docs for every tool, including
  all filter options and return shapes
- `references/codex-wonen-rules.md` — room classification keywords, toilet
  detection logic, and minimum area table with examples
- `../projects/README.md` — profile-schema met alle velden
- `../programs/README.md` — programma-schema + intake-afspraken
- `../rulesets/README.md` + `../rulesets/codex-wonen.md` — canonieke normbeschrijvingen

## Resultaten visualiseren — voorkeursstijl

Bij compliance-checks en stapelchecks worden resultaten **altijd** weergegeven als een interactieve HTML-widget via `show_widget`, niet als platte tekst of markdown-tabel. Dit is de voorkeursstijl voor alle Revit-rapportages.

### Stapelcheck per positie (kaartindeling)

Gebruik één kaart per appartementpositie. Elke kaart bevat:
- **Header:** positienaam (bv. `2.C.Niv ×.03`), type, personen, slaapkamers, WO-oppervlakte + badge `Identiek & conform` (groen) of afwijking (rood)
- **Tabel:** ruimtenaam | Niv 1 | Niv 2 | Niv 3 | Min. | Identiek (✓/✗ + delta)
- Niet-conforme cellen rood kleuren via `var(--color-text-danger)`

```html
<!-- Kaartstructuur per positie -->
<div class="pos-card"> <!-- border 0.5px, border-radius-lg -->
  <div class="pos-header"> <!-- bg-secondary, flex space-between -->
    <span class="pos-title">2.C.Niv ×.03</span>
    <span class="badge badge-ok">Identiek & conform</span>
  </div>
  <table> <!-- table-layout: fixed, font-size 12px -->
    <thead>Ruimte | Niv 1 | Niv 2 | Niv 3 | Min. | Identiek</thead>
    <tbody><!-- rijen met kleurcodering --></tbody>
  </table>
</div>
```

**Identiteitsdrempel:** verschil ≤ 0.015 m² geldt als identiek (afrondingsartefacten Revit).

**Statusbadge logica:**
- Alles OK → `badge-ok` "Identiek & conform"
- Niet identiek → `badge-nok` "niet identiek"
- Niet conform → `badge-nok` "niet conform"
- Beide → `badge-nok` "niet identiek + niet conform"

### Samenvattende metric cards (boven de kaarten)

Altijd 4 metric cards tonen vóór de detailkaarten:
- Totaal appartementen/units
- Aantal posities
- Identieke posities (groen)
- Posities met afwijkingen (rood)

### Conformiteitscheck per appartement

Bij `compare_rooms_with_checklist`-resultaten: toon per appartement een kaart met ruimtetabel. Niet-conforme oppervlaktes rood, conforme groen of neutraal. Toiletten markeren als `n.v.t.` (cursief, tertiary kleur).

### Kleurconventie

| Situatie | CSS variable |
|---|---|
| Conform / identiek | `var(--color-text-success)` / `var(--color-background-success)` |
| Niet conform / niet identiek | `var(--color-text-danger)` / `var(--color-background-danger)` |
| N.v.t. (toilet, geen min.) | `var(--color-text-tertiary)`, italic |
| Secundaire info (type, meta) | `var(--color-text-secondary)` |

### Loading messages

Gebruik nederlandstalige loading messages bij `show_widget`:
- `"Ruimtes per positie opstapelen..."`
- `"Conformiteit berekenen..."`
- `"Tabellen opmaken..."`

## Common Issues

**MCP not connected**
Ask the user to run `/mcp` to reconnect, or check that pyRevit is loaded in Revit.

**Route not found (500 error)**
The pyRevit extension needs a reload inside Revit: pyRevit tab → Reload.
`/mcp` reconnects the client but does not reload the Revit-side routes.
Geldt ook na updates aan de route-files (nieuwe groupby/overview/discovery routes).

**Filter returns no results**
The filter is a prefix match on the grouping value from the project profile. Use
`get_model_structure` to confirm the exact value format before filtering.
Geen profiel + geen KSS-conventie in het model = grouping-waarden zijn leeg —
run het project-setup interview.

**Category not found in response**
Some Revit categories (e.g. `plumbingeq`, `lightingdev`) may not exist in older
Revit versions. The route silently skips unavailable categories and logs a warning.
Use `get_room_furnishings(categories="all")` to see which categories have data.
