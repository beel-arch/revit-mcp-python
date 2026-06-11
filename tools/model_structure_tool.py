"""
MCP tool: lightweight model structure discovery (profile-aware).

WHEN TO CALL THIS TOOL
-----------------------
Call get_model_structure FIRST whenever the user's request is ambiguous about which
part of the model to check. Examples that require this tool first:
  - "check gebouw 1"           → need to map "gebouw 1" to grouping value patterns
  - "get all badkamers"        → confirm which room names classify as badkamer
  - "check niveau 2"           → confirm the exact level name in the model
  - "check the WO areas"       → confirm area scheme names

Do NOT call this tool when the user's request is already fully specific
(e.g. "compare_rooms_with_checklist without filter", "get all areas").

HOW TO USE THE RESULT
---------------------
1. Read the grouping values to identify the unit/building structure.
2. Read `room_name_variants` to confirm room name spelling.
3. Read `levels` for exact level names.
4. Present a brief summary to the user and ask ONE clarifying question.
5. Only after the user confirms, call the targeted heavy tool with the filter.

The grouping parameter comes from the project profile (projects/<model>.json);
without a profile the KSS default (BEEL_C_TX_AppartementNummer) is used.
"""

from urllib.parse import quote

from mcp.server.fastmcp import Context

from .project_profile_tool import get_grouping, DEFAULT_GROUPING_PARAMETER


def register_model_structure_tools(mcp, revit_get):

    @mcp.tool()
    async def get_model_structure(ctx: Context) -> str:
        """
        Lightweight discovery tool — call this FIRST before any ambiguous query.

        Returns the model's structural identifiers:
        - Levels with elevations (for level-based filtering)
        - Grouping values van de profile-parameter (appartementen bij KSS,
          ruimtegroepen bij JGC, UnitID's bij THELLO) + afgeleide segmenten
        - Placed/unplaced room counts
        - Unique room name variants (to confirm spelling before filtering)
        - Area scheme names (for area queries)
        - View count by type / family count by category

        After calling this, present a brief summary and ask the user ONE clarifying
        question before running any expensive query with a filter.
        Geen grouping-waarden gevonden? Run discover_room_parameters en daarna het
        project-setup interview (save_project_profile).
        """
        group_param, group_label, profile = await get_grouping(revit_get, ctx)

        if group_param == DEFAULT_GROUPING_PARAMETER:
            resp = await revit_get("/model_structure/", ctx)
        else:
            resp = await revit_get(
                "/model_structure/groupby/{}".format(quote(group_param, safe="")), ctx)

        if isinstance(resp, str):
            return "Fout bij ophalen model structuur: {}".format(resp)
        if isinstance(resp, dict) and "error" in resp:
            return "Fout bij ophalen model structuur: {}".format(resp["error"])

        levels = resp.get("levels", [])
        grouping_values = resp.get("grouping_values", resp.get("apartment_numbers", []))
        grouping_count = resp.get("grouping_count", len(grouping_values))
        building_segs = resp.get("building_segments", [])
        room_names = resp.get("room_name_variants", [])
        total_rooms = resp.get("total_rooms")
        placed = resp.get("placed_rooms")
        unplaced = resp.get("unplaced_rooms")
        area_schemes = resp.get("area_schemes", [])
        views = resp.get("views", {})
        fam_cats = resp.get("family_categories", {})

        lines = ["# Model Structure", ""]
        if profile:
            lines.append("Project profile: {} — grouping op '{}' ({})".format(
                profile.get("project_name") or "?", group_param, group_label))
        else:
            lines.append("Geen project profile — KSS-fallback: grouping op '{}'".format(
                group_param))
        lines.append("")

        # Levels
        lines.append("## Niveaus ({})".format(len(levels)))
        for lvl in levels:
            lines.append("  - {} ({} m)".format(lvl["name"], lvl["elevation_m"]))
        lines.append("")

        # Rooms / placement
        if total_rooms is not None:
            lines.append("## Rooms: {} totaal — {} placed, {} unplaced".format(
                total_rooms, placed, unplaced))
            if unplaced:
                lines.append("⚠ unplaced rooms hebben area 0 en vallen buiten de meeste checks")
            lines.append("")

        # Grouping values
        lines.append("## {} ({} total)".format(group_label.capitalize(), grouping_count))
        if building_segs:
            lines.append("Gebouw/blok segmenten: {}".format(", ".join(building_segs)))
            lines.append("(gebruik een segment als filter, bijv. '1.A' of '2.C')")
        if grouping_values:
            preview = grouping_values[:12]
            more = grouping_count - len(preview)
            suffix = " … (+{} more)".format(more) if more > 0 else ""
            lines.append("Voorbeelden: {}{}".format(", ".join(preview), suffix))
        elif not profile:
            lines.append("Geen waarden voor '{}' — dit model volgt de KSS-conventie niet.".format(
                group_param))
            lines.append("Run discover_room_parameters + het project-setup interview.")
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
