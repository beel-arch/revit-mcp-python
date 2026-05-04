# Hoe werkt het? — Van Claude Desktop naar Revit

## Het grote plaatje

```
Claude Desktop
     │  MCP protocol (stdio)
     ▼
main.py  ←──── FastMCP server (Python, draait op jouw PC)
     │  HTTP GET/POST
     ▼
pyRevit Routes  ←──── HTTP server binnen Revit (port 48884)
     │  Revit API (.NET)
     ▼
Revit model
```

Twee aparte processen, twee aparte talen, gekoppeld via HTTP.

---

## Stap 1 — Claude Desktop weet welke tools bestaan (MCP)

Claude Desktop laadt `main.py` op via **stdio** (standaardinvoer/uitvoer).  
`main.py` declareert een `FastMCP`-server met alle beschikbare tools.

```python
# main.py
mcp = FastMCP("Revit MCP Server")
```

Elke functie met `@mcp.tool()` wordt een **MCP tool** — Claude ziet die automatisch,
inclusief de naam, parameters en de docstring als beschrijving.

```python
@mcp.tool()
async def compare_rooms_with_checklist(ctx: Context) -> str:
    """
    Vergelijk de oppervlaktes van Revit rooms met de BEEL Checklist Codex Wonen (VMSW).
    ...
    """
```

Die lange docstring is wat Claude leest om te begrijpen **wanneer** en **hoe** hij de tool
moet gebruiken. Claude kiest zelf welke tool hij aanroept op basis van wat de gebruiker vraagt.

---

## Stap 2 — Claude roept een tool aan

Als jij typt: *"Controleer of de kamers voldoen aan Codex Wonen"*, herkent Claude dat
`compare_rooms_with_checklist` de juiste tool is en roept die aan.

De MCP-server in `main.py` voert dan de Python-functie uit in `tools/room_checklist_tool.py`.

---

## Stap 3 — De tool haalt data op uit Revit via HTTP

`main.py` definieert een hulpfunctie:

```python
BASE_URL = "http://localhost:48884/revit_mcp"

async def revit_get(endpoint, ctx):
    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL + endpoint)
        return response.json()
```

De tool doet twee HTTP-calls:

```python
rooms_resp = await revit_get("/rooms/", ctx)       # alle kamers uit Revit
areas_resp = await revit_get("/areas/WO", ctx)     # WO-areas met personen/slaapkamers
```

---

## Stap 4 — pyRevit Routes ontvangt het verzoek in Revit

Binnen Revit draait **pyRevit** als een add-in. pyRevit heeft een ingebouwde HTTP-server
(`pyrevit.routes`) die luistert op poort **48884**.

`rooms.py` registreert een route op dat systeem:

```python
# revit_mcp/rooms.py
@api.route('/rooms/', methods=["GET"])
def get_all_rooms(doc, request=None):
    ...
```

`doc` is het geopende Revit-document — dat geeft pyRevit automatisch mee.  
Geen aparte server nodig, geen Flask, geen FastAPI: pyRevit doet dat ingebouwd.

---

## Stap 5 — De Revit API levert de data

Binnen `get_all_rooms` wordt de Revit API (.NET, via IronPython) aangesproken:

```python
import Autodesk.Revit.DB as DB

collector = (
    DB.FilteredElementCollector(doc)
    .OfCategory(DB.BuiltInCategory.OST_Rooms)
    .WhereElementIsNotElementType()
)
```

Per kamer wordt opgezocht:
- **Naam** en **nummer** — ingebouwde Revit-parameters (`ROOM_NAME`, `ROOM_NUMBER`)
- **Oppervlakte** — `room.Area` (in vierkante voet) × 0.092903 = m²
- **`BEEL_C_TX_AppartementNummer`** — een projectspecifieke custom parameter

Het resultaat wordt als JSON teruggestuurd naar de MCP-server.

---

## Stap 6 — De checklist-logica in Python

`room_checklist_tool.py` bevat de Codex Wonen-regels:

```python
RULES = {
    "leefruimte": ("Leefruimte", lambda p, k: 18.0 + 2.0 * p, "18 + 2 × personen"),
    "keuken":     ("Keuken",     lambda p, k: 4.0 + 0.5 * p,  "4 + 0.5 × personen"),
    ...
}
```

De logica werkt in drie stappen:

1. **Koppelen** — rooms worden gegroepeerd op `BEEL_C_TX_AppartementNummer`.
2. **Classifiëren** — de naam van de kamer bepaalt de regel (`_classify_room`).
3. **Vergelijken** — oppervlakte vs. minimum; resultaat is `ok: True/False` en `diff`.

Het eindresultaat is een leesbaar tekstrapport dat Claude teruggeeft aan de gebruiker.

---

## Overzicht van de bestanden

| Bestand | Laag | Wat doet het? |
|---|---|---|
| `main.py` | MCP server | FastMCP-instantie, HTTP-helpers, tools registreren |
| `tools/room_checklist_tool.py` | MCP tool | Checklist-logica, Codex Wonen-regels, rapportage |
| `revit_mcp/rooms.py` | pyRevit Routes | HTTP-endpoint `/rooms/`, leest Revit-model uit |
| `revit_mcp/__init__.py` | pyRevit extension | Logger, module-initialisatie |

---

## Waarom weet Claude wat hij moet doen?

Claude leest de **docstring** van elke tool. Die legt in mensentaal uit wat de tool doet,
welke data hij nodig heeft en wat hij teruggeeft. Claude hoeft de implementatie niet te kennen —
alleen de beschrijving en de parameters. Op basis daarvan beslist het model zelf welke tool
hij wanneer aanroept, en in welke volgorde.

```
Gebruiker vraagt iets
    → Claude matcht op docstrings
        → Claude roept tool aan (MCP)
            → Tool doet HTTP naar Revit
                → Revit geeft JSON terug
                    → Tool verwerkt, formatteert
                        → Claude toont resultaat aan gebruiker
```
