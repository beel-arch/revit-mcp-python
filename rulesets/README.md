# Rulesets — herbruikbare normen

Normen die over projecten heen gelden (in tegenstelling tot `programs/` = per project
en `projects/` = per model). Eén bestand per norm; een project verklaart welke
rulesets gelden via het profiel:

```json
"rulesets": ["codex-wonen"]
```

| Ruleset | Domein | Uitvoerende tools |
|---|---|---|
| `codex-wonen` | Sociale woningbouw (VMSW / Leidraad) | `compare_rooms_with_checklist`, `check_room_fixtures`, `check_window_area_compliance` |

De `.md`-bestanden hier zijn de **canonieke beschrijving** van elke norm (formules,
classificatie, detectielogica). De uitvoerbare implementatie leeft in `tools/` —
bij een normwijziging: eerst het ruleset-bestand aanpassen, dan de tool gelijktrekken.

Een norm toevoegen = hier een `.md` (en later evt. machine-leesbare regels)
plus een tool of toolaanpassing die ernaar verwijst. Projecten verwijzen alleen
naar de naam — meerdere sociale woonprojecten delen zo één codex-wonen-definitie.
