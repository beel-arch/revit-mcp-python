# Ruleset: codex-wonen

Leidraad sociale woningbouw (Codex Wonen / VMSW). Geldt voor elk woonproject dat
`"rulesets": ["codex-wonen"]` in zijn profiel verklaart.

Bezetting per appartement komt uit de WO-areas: area-naam = `slaapkamers/personen`
(bv. `3/5`), area-nummer = appartementnummer.

## Minimumoppervlaktes (per ruimte)

| Ruimtetype | Minimum | Formule |
|---|---|---|
| Leefruimte (zithoek + eethoek) | — | 18 + 2 × personen m² |
| Keuken | — | 4 + 0,5 × personen m² |
| Slaapkamer ouders | 11 m² | vast |
| Slaapkamer kind (1 kind) | 7 m² | vast |
| Slaapkamer kind (2 kinderen, naam bevat "2p") | 12 m² | vast |
| Badkamer zonder toilet | — | 2 + 0,5 × personen m² |
| Badkamer met toilet | — | 3 + 0,5 × personen m² |
| Inkomzone | 1,5 m² | vast |
| Berging (appartement) | — | 3 + 0,5 × personen m² |
| Toilet | geen minimum | — |

Toilet-detectie in badkamer: Plumbing Fixture met "toilet" in de familienaam.

## Roomnaam-classificatie (keywords)

| Categorie | Keywords (substring, case-insensitief) |
|---|---|
| leefruimte | leef, woon, zitkamer, zithoek, eethoek |
| keuken | keuken |
| slaapkamer_ouders | ouder, master, hoofd |
| slaapkamer_kind | kinder, kind, slaap, chambre, bedroom |
| badkamer | bad, douche, sanitair |
| inkomzone | inkom, hal, gang, vestiaire, entree, entrée |
| berging | berg, opslag, stock, stockage |
| toilet | toilet, wc |

Per-project overschrijfbaar via `room_classification` in het profiel.

## Sanitaire uitrusting (badkamer)

| Element | Eis |
|---|---|
| Wastafel / spiegel / tablet | 1 stuks; **2 stuks bij ≥ 5 personen** |
| Sanitair bij < 3 slaapkamers | inloopdouche verplicht, ligbad NIET toegestaan |
| Sanitair bij ≥ 3 slaapkamers | ligbad met douchemogelijkheid verplicht |

Familienaam-detectie (case-insensitief): toilet→"toilet", wastafel→"wastafel",
spiegel→"spiegel", tablet→"tablet", ligbad→"bad"/"ligbad", douche→"douche".

## Daglicht

| Ruimtetype | Raamoppervlak t.o.v. vloeroppervlak |
|---|---|
| Leefruimte | ≥ 1/6 |
| Slaapkamers | ≥ 1/8 |
| Overige | n.v.t. |

## Implementatie

| Regel | Tool | Bestand |
|---|---|---|
| Minimumoppervlaktes + classificatie | `compare_rooms_with_checklist` | `tools/room_checklist_tool.py` (`RULES`, `_classify_room`) |
| Sanitaire uitrusting | `check_room_fixtures` | `tools/bathroom_checklist_tool.py` |
| Daglicht | `check_window_area_compliance` | `tools/window_area_tool.py` |

Bron-checklist: `BEEL_Checklist_Codex_Wonen.xlsx`. Zie ook
`revit-query/references/codex-wonen-rules.md` (skill-referentie met voorbeelden).
