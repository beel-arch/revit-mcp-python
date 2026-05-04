"""
MCP tool: lightweight model structure discovery.

WHEN TO CALL THIS TOOL
-----------------------
Call get_model_structure FIRST whenever the user's request is ambiguous about which
part of the model to check. Examples that require this tool first:
  - "check gebouw 1"           → need to map "gebouw 1" to apartment number patterns
  - "get all badkamers"        → confirm which room names classify as badkamer
  - "check niveau 2"           → confirm the exact level name in the model
  - "check the WO areas"       → confirm area scheme names

Do NOT call this tool when the user's request is already fully specific
(e.g. "compare_rooms_with_checklist without filter", "get all areas").

HOW TO USE THE RESULT
---------------------
1. Read `building_segments` and `apartment_numbers` to identify building/block structure.
2. Read `room_name_variants` to confirm room name spelling.
3. Read `levels` for exact level names.
4. Present a brief summary to the user and ask ONE clarifying question, e.g.:
   "I see apartment numbers grouped as 1.A, 1.B, 2.C — is '1' what you mean by gebouw 1?"
5. Only after the user confirms, call the targeted heavy tool with the appropriate filter.
"""

from mcp.server.fastmcp import Context


def register_model_structure_tools(mcp, revit_get):

    @mcp.tool()
    async def get_model_structure(ctx: Context) -> str:
        """
        Lightweight discovery tool — call this FIRST before any ambiguous query.

        Returns the model's structural identifiers:
        - Levels with elevations (for level-based filtering)
        - All apartment numbers + derived building/block segments (e.g. "1.A", "2.C")
        - Unique room name variants (to confirm spelling before filtering)
        - Area scheme names (for area queries)
        - View count by type
        - Family count by category

        After calling this, present a brief summary and ask the user ONE clarifying
        question before running any expensive query with a filter.
        """
        resp = await revit_get("/model_structure/", ctx)

        if isinstance(resp, str):
            return "Fout bij ophalen model structuur: {}".format(resp)
        if isinstance(resp, dict) and "error" in resp:
            return "Fout bij ophalen model structuur: {}".format(resp["error"])

        levels = resp.get("levels", [])
        apt_numbers = resp.get("apartment_numbers", [])
        apt_count = resp.get("apartment_count", len(apt_numbers))
        building_segs = resp.get("building_segments", [])
        room_names = resp.get("room_name_variants", [])
        area_schemes = resp.get("area_schemes", [])
        views = resp.get("views", {})
        fam_cats = resp.get("family_categories", {})

        lines = ["# Model Structure", ""]

        # Levels
        lines.append("## Niveaus ({})".format(len(levels)))
        for lvl in levels:
            lines.append("  - {} ({} m)".format(lvl["name"], lvl["elevation_m"]))
        lines.append("")

        # Apartments / buildings
        lines.append("## Appartementen ({} total)".format(apt_count))
        if building_segs:
            lines.append("Gebouw/blok segmenten: {}".format(", ".join(building_segs)))
            lines.append("(gebruik een segment als filter, bijv. '1.A' of '2.C')")
        if apt_numbers:
            preview = apt_numbers[:6]
            more = apt_count - len(preview)
            suffix = " … (+{} more)".format(more) if more > 0 else ""
            lines.append("Voorbeelden: {}{}".format(", ".join(preview), suffix))
        lines.append("")

        # Room name variants
        lines.append("## Kamer types ({} unieke namen)".format(len(room_names)))
        lines.append("  " + ", ".join(room_names))
        lines.append("")

        # Area schemes
        lines.append("## Oppervlakte schema's")
        lines.append("  " + (", ".join(area_schemes) if area_schemes else "geen gevonden"))
        lines.append("")

        # Views
        lines.append("## Views")
        for vtype, count in sorted(views.items()):
            lines.append("  {}: {}".format(vtype, count))
        lines.append("")

        # Family categories (top 10 by count)
        lines.append("## Family categorieën (top 10)")
        top_cats = sorted(fam_cats.items(), key=lambda x: -x[1])[:10]
        for cat, count in top_cats:
            lines.append("  {}: {}".format(cat, count))

        return "\n".join(lines)
