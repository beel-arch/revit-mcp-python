# Project Profile Architecture — Universal Room Checking on Any Project

> How an interview in Claude Desktop becomes configuration that the MCP code actually uses.

The answer is simpler than it might feel: your MCP server is a local Python process with full disk access. So the missing link is just **one new tool pair on your own server: `save_project_profile` / `get_project_profile`**. The interview's deliverable is a tool call, not a document.

## The mechanism, end to end

```
Claude Desktop                    MCP server (CPython)              Revit (IronPython routes)
─────────────                     ────────────────────              ─────────────────────────
1. Skill: "project-setup"
   triggers the interview
2. Discovery calls  ────────────→ get_revit_model_info,  ─────────→ reads actual model
                                  get_model_structure,
                                  room parameter dump
3. Claude proposes answers,
   user confirms (1 vraag/keer)
4. save_project_profile  ───────→ writes projects/<model>.json
                                  (plain file in the repo)
   ... later sessions ...
5. compare_rooms / doors / ... ─→ loads projects/<model>.json ────→ /rooms/grouped_by/
                                  injects param names into            <param_name>/...
                                  route URLs
```

Three things to notice:

### 1. The profile lives as a JSON file on the MCP server's disk, written *by* an MCP tool.

Claude Desktop itself can't write files into your repo — but it doesn't need to. You add to `tools/`:

- `save_project_profile(profile_json)` — validates and writes `projects/<model_name>.json`
- `get_project_profile()` — returns the profile for the currently open model (or "no profile yet — run project setup")

Keying the filename to the Revit model name (you already have `get_revit_model_info`) means later sessions need zero ceremony: any tool that needs conventions calls `get_project_profile()` internally, matches it to whatever model is open, done. Open KSS → KSS conventions load. Open a school project → its conventions load. Claude never has to remember anything between sessions, and a colleague using the same MCP server gets the same behavior.

### 2. The interview should be discovery-grounded, not a blank questionnaire.

This is where it gets good, and it's pure skill-text, no new code beyond what you have. The skill instructs Claude to *inspect first, then confirm*:

> 1. Call `get_revit_model_info` + `get_model_structure`.
> 2. Pick one room, dump its parameters (`get_element_parameters` — you have it). Identify candidate grouping parameters: text parameters that are filled on rooms and repeat in patterns.
> 3. Ask: *"Ik zie dat rooms een parameter `BEEL_C_TX_AppartementNummer` hebben met waarden als `1.A.Niv 0.01`. Is dit hoe ruimtes gegroepeerd worden in dit project?"*
> 4. List area schemes found. Ask which one (if any) carries occupancy, and how it's encoded.
> 5. Sample 20 room names. Propose a classification mapping ("`Slpk 1` → slaapkamer?"). Confirm.
> 6. Call `save_project_profile`.

So the user experience is exactly what you described — "this is a new project, we need to set out the rules" — but Claude's questions are *"I see X in your model, is that Y?"* instead of *"what is your grouping parameter called?"*. Much faster, and it catches the project where someone forgot to fill the parameter before you build rules on top of it.

### Discovery must be generic — lessons from the JGC and THELLO tests (2026-06)

Live tests on two non-KSS models proved that discovery cannot lean on the hardcoded apartment parameter. `get_model_structure` reported "0 appartementen" on both — while JGC carries a fully filled `Room KEY` key schedule (`JGC_BEEL_C_TX_Functieblok`, `JGC_BEEL_C_TX_Ruimtegroep`) and THELLO/ORSBEV groups its 988 rooms by `THELLO_C_TX_UnitID` (`C104`, `A112`). Three models, three convention families, and the current discovery is blind to two of them. The room-parameter dump in step 2 therefore needs to become a real route: distinct values + **fill-rate** per text parameter on rooms, from which Claude proposes grouping candidates. Hard requirements learned from the tests:

- **Filter on fill-rate.** THELLO rooms carry hundreds of empty shared parameters (IFC/import noise: "Cabin depth", "Nominal flow", …). Without a fill-rate threshold the interview drowns in junk candidates.
- **Store parameter names literally, never reconstruct them.** THELLO has a typo in a production parameter: `THELL0_C_TX_UnitTypologie` (zero instead of O). The profile must copy names exactly as dumped.
- **Report placement status.** THELLO has 366 unplaced rooms out of 988 (area = 0). Discovery and every downstream check must flag or exclude unplaced rooms explicitly.

### 3. The routes stay dumb; the tool layer injects the profile.

The IronPython side never reads profile files. Routes just become parameterized where they're currently hardcoded: `/rooms/grouped_by/<param_name>` instead of a baked-in `LookupParameter("BEEL_C_TX_AppartementNummer")`. The CPython tool layer loads the profile and fills in the URL. This keeps your lean-query principle (filtering still happens inside Revit) and confines the change to string substitution in five route files.

Two route additions the JGC/THELLO tests showed are missing:

- **A level filter as universal second axis.** Every room tool today filters on `apartment_filter` only; on a model without that parameter there is no lean way to say "rooms on level 100 / N01". Levels exist in *every* model — the parameterized routes should accept a level name alongside the grouping value.
- **A lean "rooms overview" route.** The JGC test had to fall back on `get_elements_by_category("Rooms")`, which returns only ID + level (rooms have no family/type, so even the name column is empty), and per-room `get_element_parameters` is far too heavy for ~170 rooms. One route returning name, number, area, level plus a caller-supplied list of parameter names per room — filtered inside Revit — covers discovery, overviews, and the program join alike.

## What the profile contains (structure conventions only)

```json
{
  "model_name": "BEEL_KSS_...",
  "project_name": "KSS",
  "grouping": [
    {"derive": {"from": "BEEL_C_TX_AppartementNummer", "rule": "prefix"}, "label": "blok"},
    {"parameter": "BEEL_C_TX_AppartementNummer", "label": "appartement"}
  ],
  "room_type_parameter": null,
  "occupancy": {
    "source": "area_scheme",
    "scheme": "WO",
    "encoding": "name_regex",
    "pattern": "^(?P<slaapkamers>\\d+)/(?P<personen>\\d+)$"
  },
  "program_link": {"mode": "none"},
  "room_classification": {
    "leefruimte": ["leef", "woon", "zithoek"],
    "slaapkamer": ["slaap", "slpk"],
    "badkamer": ["bad", "douche"]
  },
  "family_keywords": {
    "toilet": ["toilet"], "wastafel": ["wastafel"], "spiegel": ["spiegel"]
  }
}
```

Field notes, grounded in the three models tested so far:

- **`grouping` is a hierarchical list** (coarse → fine), not a single parameter. KSS: blok > appartement. JGC: `JGC_BEEL_C_TX_Functieblok` > `JGC_BEEL_C_TX_Ruimtegroep`. THELLO: building letter > `THELLO_C_TX_UnitID`. A level may point at a `parameter` directly or `derive` from another one (`rule: "prefix"` — the building letter lives inside `C104`, the blok inside `1.A.Niv 0.01`); deriving keeps the model free of redundant parameters.
- **`room_type_parameter`** — the normalized room type may live in a parameter rather than in `Name`. JGC: `Name` = "Intakelokaal type 2" (instance variant) while `JGC_BEEL_C_TX_Ruimte` = "Intakelokaal" (program type). `null` means "use `Name`".
- **`program_link.mode`**: `"key_schedule" | "external_json" | "none"`. JGC embeds its program *in the model* via a key schedule — `Room KEY` drives read-only requirement parameters incl. `JGC_BEEL_C_AR_MinimaleOppervlakte` and a live computed `JGC_BEEL_C_AR_VerschilOppervlakte`, so compliance there is a parameter *read*, not a join. `"external_json"` points at `programs/<project>.json` (see `program-to-model-architecture.md`); `"none"` for projects like THELLO with no program data.
- **Optional pointers to in-model computed values**: `unit_area_parameter` (THELLO: `THELLO_C_AR_UnitTotalArea`, the aggregated unit area stored on every room) and `typology_parameter` (THELLO: `THELL0_C_TX_UnitTypologie` — note the literal zero-typo, copied exactly as dumped). The pattern: where the model already computes a value, the engine reads it instead of recomputing.

For a school, the finest `grouping` level might be a lokaalnummer, `occupancy.source` becomes `"room_parameter"` pointing at a capacity parameter, and the classification keywords say "klaslokaal", "refter", "turnzaal". Same shape, same engine. The `occupancy.source` field with a couple of allowed variants (`area_scheme` / `room_parameter` / `none`) and `program_link.mode` are the two places the engine needs branching — everything else is name substitution.

## Where each piece lives

| Piece | Artifact | Lives in |
|---|---|---|
| Interview script + question order | `project-setup` SKILL.md | skill folder (next to `revit-query`) |
| The answers | `projects/<model>.json` | MCP repo, written by `save_project_profile` |
| Read/write of profiles | two small tools in `tools/` | MCP server |
| Convention-free queries | parameterized routes | pyRevit extension |

One thing deliberately *not* in this profile: the norm rules themselves (Codex Wonen formulas etc.). Those stay where they are for now — this step only makes the existing tools work on any project's *structure*. The day you do rulesets, the profile gains one line (`"rulesets": ["codex-wonen"]`), and nothing here changes.

The honest cost of this step: the interview skill is cheap, the profile tools are cheap; the real work is refactoring the five route files plus the tool layer to take parameter names as input instead of constants — a contained, mechanical refactor with three regression projects to check against:

| Project | What it proves |
|---|---|
| **KSS** | the existing woon-conventions and reports keep working (apartment grouping, WO area scheme) |
| **JGC** | a second grouping axis (functieblok/ruimtegroep), the key-schedule program variant, zero apartments |
| **THELLO** | unit-ID grouping with derived building level, French room names, heavy parameter noise, 366 unplaced rooms |
