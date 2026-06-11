"""MCP tools: room parameter discovery + lean rooms overview.

discover_room_parameters voedt het project-setup interview (welke parameter draagt
de grouping?); get_rooms_overview is de generieke lean room-query met level- en
grouping-filter, profile-aware.
"""

from mcp.server.fastmcp import Context

from .project_profile_tool import get_grouping

_FULL_LISTING_LIMIT = 150


def register_room_discovery_tools(mcp, revit_get, revit_post):

    @mcp.tool()
    async def discover_room_parameters(ctx: Context) -> str:
        """
        Ontdek welke tekstparameters op rooms gevuld zijn — voor het project-setup interview.

        Geeft per parameter de fill-rate, het aantal distinct values en voorbeelden,
        gesorteerd op fill-rate. Lege import-ruis (honderden lege shared parameters)
        wordt automatisch weggefilterd. Toont ook placed/unplaced room-aantallen.

        Gebruik dit om grouping-kandidaten te vinden (appartementnummer, ruimtegroep,
        UnitID, ...) en stel daarna per kandidaat één bevestigingsvraag aan de gebruiker.
        Neem parameternamen LETTERLIJK over in het profiel — nooit reconstrueren.
        """
        resp = await revit_get("/rooms/parameter_discovery/", ctx)
        if isinstance(resp, str):
            return "Fout bij discovery: {}".format(resp)
        if isinstance(resp, dict) and "error" in resp:
            return "Fout bij discovery: {}".format(resp["error"])

        total = resp.get("total_rooms", 0)
        placed = resp.get("placed_rooms", 0)
        unplaced = resp.get("unplaced_rooms", 0)
        params = resp.get("parameters", [])

        lines = ["# Room parameter discovery", ""]
        lines.append("Rooms: {} totaal — {} placed, {} unplaced".format(total, placed, unplaced))
        if unplaced:
            lines.append("⚠ {} unplaced rooms (area 0) — vermeld dit in checks en rapporten.".format(unplaced))
        lines.append("")

        if not params:
            return "\n".join(lines) + "Geen gevulde tekstparameters gevonden op rooms."

        lines.append("## Gevulde tekstparameters (gesorteerd op fill-rate)")
        lines.append("")
        for p in params:
            capped = "+" if p.get("distinct_capped") else ""
            lines.append("### {}  — fill {:.0%}  ({} gevuld, {}{} distinct)".format(
                p["name"], p["fill_rate"], p["filled"], p["distinct_count"], capped))
            examples = p.get("examples") or []
            if examples:
                lines.append("  voorbeelden: {}".format(", ".join(examples)))
            lines.append("")

        lines.append("Grouping-kandidaten: parameters met hoge fill-rate en herhalende, "
                      "gestructureerde waarden. Bevestig de keuze met de gebruiker "
                      "(één vraag per keer) en sla op via save_project_profile.")
        return "\n".join(lines)

    @mcp.tool()
    async def get_rooms_overview(
        ctx: Context,
        level: str = "",
        unit_filter: str = "",
        extra_parameters: str = "",
        include_unplaced: bool = False,
    ) -> str:
        """
        Lean room overview — naam, nummer, oppervlakte, level per room, gegroepeerd
        op de grouping-parameter uit het project profile.

        Werkt op elk model: KSS groepeert op appartementnummer, JGC op ruimtegroep,
        THELLO op UnitID — automatisch via projects/<model>.json (fallback: KSS-conventie).

        Parameters:
          level:            exacte levelnaam (bv. "100", "N01"). Gefilterd in Revit (lean).
          unit_filter:      prefix op de grouping-waarde (bv. "1.A", "C1", "BW").
                            Roep eerst get_model_structure op voor geldige waarden.
          extra_parameters: comma-separated parameternamen om per room mee te geven
                            (bv. "JGC_BEEL_C_AR_VerschilOppervlakte,Room KEY").
                            Namen letterlijk zoals in het model.
          include_unplaced: ook unplaced rooms (area 0) tonen. Standaard uit.

        Bij grote resultaten (>150 rooms) wordt een samenvatting per groep getoond
        i.p.v. de volledige lijst — verfijn dan met level of unit_filter.
        """
        group_param, group_label, _profile = await get_grouping(revit_get, ctx)

        params = [p.strip() for p in (extra_parameters or "").split(",") if p.strip()]
        body = {
            "level": (level or "").strip(),
            "group_param": group_param,
            "group_prefix": (unit_filter or "").strip(),
            "params": params,
            "include_unplaced": bool(include_unplaced),
        }
        resp = await revit_post("/rooms/overview/", body, ctx)
        if isinstance(resp, str):
            return "Fout bij rooms overview: {}".format(resp)
        if isinstance(resp, dict) and "error" in resp:
            return "Fout bij rooms overview: {}".format(resp["error"])

        rooms = resp.get("rooms", [])
        count = resp.get("count", len(rooms))
        unplaced_skipped = resp.get("unplaced_skipped", 0)

        filter_parts = []
        if body["level"]:
            filter_parts.append("level='{}'".format(body["level"]))
        if body["group_prefix"]:
            filter_parts.append("{}='{}'".format(group_label, body["group_prefix"]))
        filter_str = "  —  filter: {}".format(", ".join(filter_parts)) if filter_parts else ""

        lines = ["ROOMS OVERVIEW  ({} rooms{})".format(count, filter_str)]
        lines.append("Grouping: '{}' ({})".format(group_param, group_label))
        if unplaced_skipped:
            lines.append("⚠ {} unplaced rooms overgeslagen (include_unplaced=True om te tonen)".format(
                unplaced_skipped))
        lines.append("")

        if not rooms:
            return "\n".join(lines) + "Geen rooms gevonden met deze filters."

        # Group rooms by grouping value
        groups = {}
        for r in rooms:
            key = r.get("group") or "(geen {})".format(group_label)
            groups.setdefault(key, []).append(r)

        if count > _FULL_LISTING_LIMIT:
            lines.append("Resultaat te groot voor volledige lijst — samenvatting per {}:".format(
                group_label))
            lines.append("")
            for key in sorted(groups.keys()):
                items = groups[key]
                total_area = sum(r.get("area_m2") or 0 for r in items)
                names = {}
                for r in items:
                    n = r.get("name") or "?"
                    names[n] = names.get(n, 0) + 1
                name_str = ", ".join("{}×{}".format(c, n) if c > 1 else n
                                     for n, c in sorted(names.items(), key=lambda x: x[0]))
                lines.append("## {}  ({} rooms, {:.1f} m²)".format(key, len(items), total_area))
                lines.append("  {}".format(name_str))
            lines.append("")
            lines.append("Verfijn met level of unit_filter voor de volledige lijst per room.")
            return "\n".join(lines)

        for key in sorted(groups.keys()):
            items = groups[key]
            lines.append("## {}  ({} rooms)".format(key, len(items)))
            for r in items:
                area = "{:.2f} m²".format(r["area_m2"]) if r.get("area_m2") else "unplaced"
                row = "  {} | {} | {} | {}  [id:{}]".format(
                    r.get("name") or "?", r.get("number") or "-", area,
                    r.get("level") or "-", r.get("id"))
                pvals = r.get("params") or {}
                extras = ["{}={}".format(k, v) for k, v in pvals.items() if v is not None]
                if extras:
                    row += "  ({})".format(", ".join(extras))
                lines.append(row)
            lines.append("")

        return "\n".join(lines)
