# Program-to-Model Architecture — From Outputspecificaties to BIM Conventions

> The reverse direction of the project profile idea: upload program documentation
> (e.g. Scholen van Vlaanderen outputspecificaties) and let the AI propose how to
> set up the BIM model — then use the same data to verify the model during design.
>
> Companion to `project-profile-architecture.md`.
> Test data: `Programma voorbeeld\C.1. Outputspecificaties` (Sint-Norbertus & Sint-Lodewijk)
> and `Programma voorbeeld\JGC\Room by Room_original.xlsx` (key-schedule case study below).
> Inspection script: `FutureUpdates\_inspect_pve.py` (runs with the MCP venv python, openpyxl is available).

## What's actually in that package (and why it's gold)

This is a Scholen van Vlaanderen-style outputspecificatie, and it's far more structured than typical program documentation:

- **BIJLAGE VI — Programma van Eisen (xlsx):** a clean hierarchy `SYSTEEM → Subsysteem → CLUSTER → LOKAAL`, where every room type has a **lokaalcode** (`02.03`), a name (`Theorielokaal 12P (aanpasbaar)`), an **aantal** (2), a **lokaal-oppervlakte** (37 m²) and totaal (74 m²). This is machine-readable today — a quick openpyxl script already pulls those rows out.
- **Lokaalfiches (docx, ~60 files):** per room type the detailed requirements — and the file names *carry the lokaalcode* (`02.03 - Lokaalfiche Theorielokaal 12P.docx`). Occupancy is encoded right in the room name (`12P`, `16P`, `20P`).
- **Schema Ruimtelijke Relaties (pdf):** adjacency requirements — which rooms must connect.
- **Verificatiematrix (xlsx):** columns `EIS-ID | Eistekst | Bewijsdocument | Voldoet/Voldoet niet | Motivering`. This is literally the report format the client expects back.

## The key insight: both directions meet in the same artifact

Direction A already exists: **live model → discovery → project profile → checks**. Direction B is: **program docs → extraction → program brief → proposed profile**. They're not two systems — the program brief becomes the *reference data* and the *seed* for the same project profile, before a model even exists:

```
Day 0 (no model yet)
  Claude Desktop reads PvE.xlsx + lokaalfiches  →  save_project_program
                                                    → programs/snor-slod.json
  AI proposes model setup conventions           →  save_project_profile (draft)
                                                    → projects/snor-slod.json

During design (model exists)
  rooms route (existing)  +  programs/snor-slod.json
        → join on join key (lokaalcode / Room KEY)
        → "02.03: programma vraagt 2× à 37 m², model heeft 2× (36.8, 37.2) ✓"

During design — key-schedule variant (program already embedded in model)
  rooms route (existing)
        → read JGC_BEEL_C_AR_VerschilOppervlakte etc. directly
        → no external join needed; the model computed the diff itself
```

**The join key is the linchpin** (lokaalcode is one form of it). The AI's "suggestion for how to build the BIM model" is, concretely: *put the join key in a room parameter* (Number, or a `BEEL_C_TX_Lokaalcode`). Once that convention exists, model-vs-program comparison is a trivial join — counts per key, area per room vs lokaalfiche minimum — using the **existing rooms route, zero new Revit tooling**. The key can be a numeric code (`02.03`, Scholen van Vlaanderen style) or name-based: the JGC model joins its Room-by-Room Excel through `Ruimtegroep` + type name (`Room KEY` = `IO-Intakelokaal type 2`), with no numeric codes anywhere. The program-brief format must support both. The hierarchical `grouping` concept from the profile document generalizes cleanly: for KSS it's blok > apartment number, for a school lokaalcode/cluster, for JGC functieblok > ruimtegroep.

## What "AI suggests a way to build a BIM model" means in practice

Not geometry — conventions and a checklist. From this package the AI can generate:

1. **Room program table** (from PvE xlsx): every room instance to place, with code, name, target m², occupancy parsed from `12P` → the model's room schedule, pre-written.
2. **Proposed profile**: grouping parameter = lokaalcode, occupancy source = room name pattern `(\d+)P`, classification = the cluster hierarchy (I./II./III. = buitenruimte, theorielokalen 1e graad, …) — no keyword guessing needed, the program *gives* you the taxonomy.
3. **Parameter/naming conventions**: which BEEL parameters to create and fill so that every later check works automatically.
4. **Later, per lokaalfiche**: fixture/finish requirements per room type — same shape as the current `FIXTURE_RULES`, but sourced from the docx instead of hardcoded.

## How it lands in code — one addition to the existing pattern

Same mechanism as the profile document, extended with one sibling:

| Piece | Artifact | Notes |
|---|---|---|
| Extraction workflow | `program-intake` SKILL.md | "read PvE xlsx first (structured), lokaalfiches second (detail), confirm lokaalcode scheme with user" |
| The extracted brief | `programs/<project>.json` | written via a new `save_project_program` tool; **keyed by project name, not model name** — it exists before the model does |
| The link | the profile's `program_link` field (see `project-profile-architecture.md`): `{"mode": "external_json", "program": "snor-slod"}` | when the model is born, profile binds model_name → project → program; `mode: "key_schedule"` means the program lives in the model itself and the join is skipped |
| Comparison | existing rooms route + join in tool layer | the "PvE vergelijking" idea, landing for free |

## Case study: JGC — the key-schedule variant, found in the wild (2026-06)

A live test on the JGC model (gesloten centrum, 285 rooms) showed the whole program-to-model idea already executed *manually* by the project team — which both validates the architecture and adds a second `program_link` mode:

- **The program source** is `Programma voorbeeld\JGC\Room by Room_original.xlsx`. Blad1: rows = room types with BHP-aantal, min m² per room and total m², against ~90 requirement columns grouped ARCHITECTURAAL / SANITAIR-KEUKEN / BEVEILIGING / ELEKTRICITEIT / HVAC / AFWERKINGSGRAAD. Blad3: the same matrix transposed, grouped per FUNCTIEBLOK. Blad2: loose requirements (door swing directions, lock types). Parses cleanly with openpyxl from the existing venv — second proof alongside the Scholen van Vlaanderen PvE.
- **The embedding**: a Revit key schedule. `Room KEY` (e.g. `IO-Intakelokaal type 2`) drives read-only `JGC_BEEL_C_*` parameters that mirror the Excel columns one-to-one: `_TX_Functieblok`, `_TX_Ruimtegroep`/`_TX_Fiche` (`IO-2`), `_TX_Ruimte` (normalized type name), `_IN_Aantal`, `_AR_MinimaleOppervlakte`, `_LE_MinimaleVrijeHoogte`, `_TX_Afwerkingsgraad`, `_TX_Veiligheidsniveau`, `_YN_NatuurlijkDaglicht` — plus a computed **`JGC_BEEL_C_AR_VerschilOppervlakte`** (observed filled, e.g. −0,10 m² on an intakelokaal — the model carries its own area diff; note the observed value is *not* simply `Area − MinimaleOppervlakte`, so verify the formula/source before building on it).
- **The consequence**: when `program_link.mode = "key_schedule"`, compliance is a parameter read through the rooms route — no external join, no `programs/*.json` required. The external-JSON join remains the path for programs that are *not* (yet) embedded; the AI's "model setup proposal" on day 0 can in fact propose exactly this key-schedule setup, since JGC proves the BEEL workflow supports it.

**THELLO/ORSBEV as the contrast case**: a French coliving model (988 rooms) with *no* program document at all → `program_link.mode = "none"`. Telling detail: the BEEL template already ships PvE fields on rooms (`BEEL_C_AR_PVEOppervlakte`, `BEEL_C_TX_PVEOpmerking`) — present but empty there. A future program-intake should fill those existing parameters rather than invent new ones.

## Practical notes from poking at the files

- The PvE xlsx parses cleanly with `openpyxl` (already in the MCP venv — that's what `_inspect_pve.py` uses). The 60 lokaalfiches are the heavy part — extract **once**, persist as JSON, version it. Never re-read docx per session.
- The Verificatiematrix is the long-term prize: compliance runs eventually *fill in* `Voldoet/Voldoet niet + Motivering` per EIS-ID, with colored view exports as bewijsdocument. And the Schema Ruimtelijke Relaties maps onto the door-adjacency graph already available via `get_doors_with_rooms`. Both are later phases — but the program package already defines both the input *and* the expected output format of the whole pipeline.
