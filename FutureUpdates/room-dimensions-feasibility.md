# Plan: Minimale breedtes en lengtes van ruimtes

## Haalbaarheidsanalyse

### Wat de Revit API biedt

`Room.GetBoundarySegments(SpatialElementBoundaryOptions)` geeft alle randcurves terug als `Line` en `Arc` objecten. Elke curve heeft `GetEndPoint(0)` en `GetEndPoint(1)`. Van die punten kunnen we een 2D-polygon opbouwen (Z negeren voor plattegrondruimtes).

Er is geen ingebouwde "minimum breedte" in de Revit API — dat moeten we zelf berekenen.

### De aanpak: Minimum Oriented Bounding Rectangle (OBR)

Het klassieke algoritme:
1. Extraheer alle hoekpunten uit de boundary segments (arcs samplen met ~8 punten)
2. Bereken de convex hull (Graham scan — ~30 regels pure Python, geen libraries)
3. Rotating calipers over de convex hull → smalste omsluitende rechthoek
4. `min_width` = kortere zijde, `max_length` = langere zijde

Dit is volledig implementeerbaar in IronPython met enkel `math`.

---

### Betrouwbaarheid per ruimtetype

| Ruimtevorm | Betrouwbaarheid | Uitleg |
|---|---|---|
| Rechthoek | ✅ Exact | OBR = de rechthoek zelf |
| Licht scheve hoeken / trapezium | ✅ Goed | OBR geeft de smalste buitenmaat |
| Convex (zeshoek, afgeronde kamer) | ✅ Goed | OBR werkt correct voor convexe vormen |
| **L-vorm, T-vorm, U-vorm** | ⚠️ Beperkt | OBR geeft de **totale buitenmaat**, niet de breedte van elke arm |
| Gebogen wanden | ✅ Goed (via sampling) | Arcs worden gesampled → voldoende nauwkeurig |

**L-vormige ruimtes zijn het echte probleem.** Een L-kamer van 3×5 + 3×3 geeft een OBR van 3×8 — dat klopt niet als "minimum breedte". Dit is hetzelfde probleem als in Dynamo: ook daar is de bounding box van een L-kamer misleidend.

**Vormherkenning via reflex hoeken:**

Een L-vormige ruimte heeft precies één hoek > 180° (een "reflex hoek"). Door die te tellen in het boundary polygon kunnen we vormen classificeren:

| Reflex hoeken | Vorm | Betrouwbaarheid dimensies |
|---|---|---|
| 0 | Convex (rechthoek, trapezium, ...) | ✅ Exact |
| 1 | L-vorm | ⚠️ Buitenmaten van de L |
| 2 | U-vorm of T-vorm | ⚠️ Buitenmaten |
| 3+ | Complexe vorm | ❌ Niet bruikbaar |

Het script geeft per ruimte terug:
- `shape: "rectangular"` / `"L-shaped"` / `"U-shaped"` / `"complex"`
- `is_approximate: true/false`
- Een leesbare waarschuwing, bv. `"L-vormige ruimte: afmetingen zijn buitenmaten, niet de breedte van elke arm"`

**Voor badkamers specifiek:**
L-vormige badkamers zijn inderdaad heel gebruikelijk (douche in de "arm"). De OBR geeft dan bv. 1.8 × 3.2m terwijl de badkamer eigenlijk een 1.8 × 2.2m kern heeft met een 0.9 × 1.0m douchehoek. Dat klopt niet als conformiteitscheck.

**Praktische aanbeveling voor L-vormige ruimtes:** gebruik `area_m2` voor conformiteitscheck, niet `min_width_m`. Het script kan dit automatisch aanbevelen wanneer het een L-vorm detecteert.

**Conclusie: betrouwbaar voor ~85-90% van de gebruikelijke ruimtes, met automatische vormdetectie en specifieke waarschuwingen per geval.**

---

## Implementatieplan

### 1. Geometry helper (nieuw, inline in route file)

Pure Python functies (~100 regels):
- `_extract_polygon(segments)` → lijst van 2D punten, handelt Line én Arc (arc = 8 sample punten)
- `_classify_shape(polygon_points)` → telt reflex hoeken → `"rectangular"` / `"L-shaped"` / `"U-shaped"` / `"complex"`
- `_convex_hull(points)` → Graham scan
- `_minimum_bounding_rect(hull)` → rotating calipers → `(width, length)`

### 2. `revit_mcp/room_dimensions.py` (nieuw)

Routes:
- `GET /rooms/dimensions/` — alle ruimtes
- `GET /rooms/dimensions/apartment/<prefix>` — gefilterd

Per ruimte teruggegeven:
```json
{
  "room_id": 123,
  "room_name": "Badkamer",
  "appartement_nr": "1.A.Niv 0.01",
  "area_m2": 5.2,
  "shape": "L-shaped",
  "min_width_m": 1.80,
  "max_length_m": 3.20,
  "is_approximate": true,
  "note": "L-vormige ruimte: afmetingen zijn buitenmaten, gebruik area_m2 voor conformiteit"
}
```

- `shape`: `"rectangular"` / `"L-shaped"` / `"U-shaped"` / `"complex"`
- `is_approximate: true` voor alle niet-convexe vormen
- `note`: leesbare uitleg, alleen aanwezig bij `is_approximate: true`

### 3. `tools/room_dimensions_tool.py` (nieuw)

MCP tool: `get_room_dimensions(apartment_filter=None, room_name_filter=None)`

Output: tabel met ruimtenaam | breedte | lengte | oppervlak | ⚠️ indien approximate

### 4. Registreren

- `startup.py`: `register_room_dimensions_routes(api)`
- `tools/__init__.py`: `register_room_dimensions_tools(mcp_server, revit_get_func)`
- `SKILL.md`: tool toevoegen aan tabel + workflow voor conformiteitscheck

---

## Verhouding tot Codex Wonen

De typische vereiste is "minimale vrije breedte" per ruimtetype. Voor rechthoekige ruimtes = OBR kortste zijde. Voor niet-convexe ruimtes moet een mens naar de tekening kijken — dat is geen zwakte van deze implementatie, dat is gewoon de realiteit van architectuur.

**Praktisch:** de meeste slaapkamers, badkamers en keukens zijn rechthoekig → betrouwbaar. Woonkamers kunnen L-vormig zijn → wordt geflagd als approximate.

## Verificatie

1. pyRevit Reload + MCP reconnect
2. `get_room_dimensions(apartment_filter="1.A")` → check waarden kloppen met een bekende tekening
3. Controleer dat L-vormige ruimte `is_approximate: true` krijgt
4. Controleer dat rechthoekige slaapkamer `is_approximate: false` geeft met correcte waarden
