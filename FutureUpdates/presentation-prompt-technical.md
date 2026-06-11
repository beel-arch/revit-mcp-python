# Presentatie-prompt — Technische slides voor BIM-professionals

> Aanvulling op `presentation-prompt.md`: extra slides voor het technische deel van het publiek.
> Te gebruiken in dezelfde Claude Desktop-sessie als de hoofddeck (zelfde stijl/template),
> met dezelfde bijlagen: `project-profile-architecture.md` en `program-to-model-architecture.md`.

## De prompt

Voeg aan de presentatie 6 à 8 extra technische slides toe (als apart hoofdstuk "Onder de motorkap — voor BIM-professionals", na de publieksslides). Doelpubliek: BIM-managers en BIM-coördinatoren met expertkennis van Revit en/of IFC-schema's. Technische termen zijn hier net gewenst — geen versimpeling. Het doel: dit publiek moet na afloop weten hoe ze zelf zoiets kunnen opzetten.

Taal: Nederlands (Engelse vaktermen behouden). Stijl: dicht bij de inhoud, schema's boven bullets, max één concept per slide.

Behandel deze onderwerpen, in deze volgorde:

1. **De stack** — één architectuurslide met de drie lagen en wat waar draait:
   Claude (Desktop/Code) ↔ MCP-server (CPython, FastMCP, tools) ↔ pyRevit Routes API (IronPython, REST-endpoints ín Revit) ↔ Revit API.
   Kernboodschap: pyRevit Routes maakt van een draaiende Revit-sessie een lokale REST-server; de MCP-server vertaalt die endpoints naar tools die het AI-model zelf kan aanroepen. Geen export, geen tussenbestand — het AI bevraagt het live model.

2. **Lean queries** — het belangrijkste ontwerpprincipe: filter ín Revit (route-laag), niet erna. Voorbeeld: `GET /doors/room/badkamer` geeft enkel badkamerdeuren terug i.p.v. alle deuren ophalen en filteren in Python. Waarom: contextvensters van LLM's zijn schaars; kleine payloads = snellere, goedkopere, betrouwbaardere antwoorden.

3. **Universal element philosophy** — elke query-tool geeft altijd `element_id` terug. Daardoor volstaan twee generieke schrijf-tools voor álle categorieën: kleur-override per view en parameter-write (Mark/Comments, bulk in één transactie). Het AI-model berekent de waarden (suffixen, compliance-labels), de tool schrijft enkel. Ontwerpregel: nooit categorie-specifieke schrijftools bouwen.

4. **De skill-laag** — domeinkennis zit in tekst (SKILL.md), niet in code: discovery-first workflow (`get_model_structure` vóór elke gefilterde query), één verduidelijkende vraag, dan pas de zware tool met filter. Toon een verkort voorbeeld uit de echte SKILL.md. Kernboodschap: gedrag stuur je met documentatie die het model leest, regels die vaak wijzigen horen niet in code.

5. **Project profile: conventies als data** — waarom de tools vandaag aan één projectstructuur hangen (hardcoded grouping-parameter, area scheme, naamgeving) en hoe een `projects/<model>.json` dat oplost: grouping parameter, occupancy-bron + encoding, classificatie-keywords. Het AI stelt dit profiel zelf voor via een discovery-interview op het live model en bewaart het via een tool-call. Routes worden geparametriseerd (`/rooms/grouped_by/<param>`), de profielresolutie zit in de tool-laag.

6. **Programma als referentiedata** — gestructureerde briefdocumenten (PvE-xlsx met lokaalcodes, lokaalfiches, verificatiematrix) één keer extraheren naar JSON; de lokaalcode als room-parameter in het model = de join-sleutel voor model-versus-programma-verificatie met bestaande tooling.

7. **Zelf beginnen** — concrete startlijst: Revit + pyRevit (Routes API), Python + MCP SDK (FastMCP), Claude met MCP-ondersteuning; open-source revit-mcp-projecten als vertrekpunt. Eerlijke valkuilen: IronPython 2.7-beperkingen (geen f-strings, unicode), Revit-transacties, route-wijzigingen vereisen Revit-reload, payload-discipline.

8. **De IFC-blik** (afsluiter voor dit hoofdstuk) — hetzelfde patroon is niet Revit-exclusief: vervang de route-laag door IfcOpenShell op een IFC-bestand en de MCP/skill/profiel-lagen blijven identiek. Voor open-BIM-workflows is dit dezelfde architectuur zonder draaiende Revit-sessie.

Voeg waar nuttig placeholder-kaders toe voor eigen beeldmateriaal, bv. [SCREENSHOT: tool-call in Claude Desktop met live antwoord], [SCREENSHOT: route-code naast tool-code], [DIAGRAM: drie-lagen-architectuur].

## Screenshots/diagrammen om zelf klaar te leggen

- Drie-lagen-architectuurdiagram (Claude ↔ MCP ↔ pyRevit Routes ↔ Revit)
- Een echte tool-call in Claude Desktop met het antwoord erbij
- Fragment route-code (IronPython) naast bijhorende tool-code (CPython)
- Fragment van een SKILL.md-workflowtabel
