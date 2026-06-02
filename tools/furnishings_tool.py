"""MCP tool: get room furnishings inventory (all categories, lean queries)."""

from mcp.server.fastmcp import Context


def register_furnishings_tools(mcp, revit_get):

    @mcp.tool()
    async def get_room_furnishings(
        ctx: Context,
        apartment_filter: str = "",
        room_name_filter: str = "",
        categories: str = "all",
    ) -> str:
        """
        Inventaris van geplaatst meubilair en uitrusting per ruimte.

        Geeft een leesbare lijst van alle geplaatste familie-instanties, gegroepeerd per ruimte.
        Doet GEEN conformiteitscheck — gebruik check_room_fixtures voor BEEL-sanitairnormen.

        Beschikbare category-aliassen (comma-separated):
          furniture    kasten, bedden, stoelen, tafels (Furniture)
          systems      systeemmeubilair, werkstations (Furniture Systems)
          casework     inbouwmeubelen, keukens, badkamermeubels (Casework)
          plumbing     wastafel, douche, ligbad, toilet (Plumbing Fixtures)
          plumbingeq   sanitaire toestellen (Plumbing Equipment)
          specialty    keukenapparaten, postbussen, speciale uitrusting
          lighting     verlichtingsarmaturen (Lighting Fixtures)
          lightingdev  verlichtingstoestellen (Lighting Devices)
          electrical   stopcontacten, schakelaars (Electrical Fixtures)
          electricaleq wasmachine, droogkast, kookfornuis, warmtepomp
          mechanical   radiatoren, ventilatieunits, HVAC
          firealarm    rookmelders, noodknoppen
          all          alle bovenstaande (standaard)

        Parameters:
          apartment_filter: Prefix voor appartementsnummers (bv. "1." voor blok 1, "1.A").
                            Leeg = alle appartementen. Gefilterd in Revit (lean query).
                            Roep eerst get_model_structure op voor geldige waarden.
          room_name_filter: Substring match op ruimtenaam (bv. "badkamer", "slaap").
                            Leeg = alle ruimten. Gefilterd na de route (tool-laag).
          categories:       Comma-separated aliassen. Standaard "all".
                            Gefilterd in Revit per category-collector (lean query).
        """
        apt_f = apartment_filter.strip() if apartment_filter else ""
        cat_f = categories.strip() if categories else "all"

        # Build URL — push both apt and cat filters to route level (lean)
        if cat_f and cat_f != "all" and apt_f:
            url = "/furnishings/byroom/cat/{}/apt/{}".format(cat_f, apt_f)
        elif apt_f:
            url = "/furnishings/byroom/apt/{}".format(apt_f)
        elif cat_f and cat_f != "all":
            url = "/furnishings/byroom/cat/{}".format(cat_f)
        else:
            url = "/furnishings/byroom/"

        resp = await revit_get(url, ctx)
        if isinstance(resp, str):
            return resp
        if isinstance(resp, dict) and "error" in resp:
            return "Fout: {}".format(resp["error"])

        all_rooms = resp.get("rooms") or []

        # Tool-level filter: room name substring (secondary filter)
        room_f = room_name_filter.strip().lower() if room_name_filter else ""
        if room_f:
            all_rooms = [r for r in all_rooms if room_f in (r.get("room_name") or "").lower()]

        if not all_rooms:
            parts = []
            if apt_f:
                parts.append("appartement '{}'".format(apt_f))
            if room_f:
                parts.append("ruimte '{}'".format(room_f))
            if cat_f != "all":
                parts.append("categorie '{}'".format(cat_f))
            suffix = " voor " + " + ".join(parts) if parts else ""
            return "Geen meubilair gevonden{}.".format(suffix)

        total_items = sum(len(r.get("items") or []) for r in all_rooms)

        filter_parts = []
        if apt_f:
            filter_parts.append("apt='{}'".format(apt_f))
        if room_f:
            filter_parts.append("kamer='{}'".format(room_f))
        if cat_f != "all":
            filter_parts.append("cat='{}'".format(cat_f))
        filter_str = "  —  filter: {}".format(" | ".join(filter_parts)) if filter_parts else ""

        lines = [
            "MEUBILAIR PER RUIMTE  ({} ruimten, {} items{})".format(
                len(all_rooms), total_items, filter_str),
            "",
        ]

        for room in all_rooms:
            rnum = room.get("room_number") or ""
            rname = room.get("room_name") or ""
            apt_nr = room.get("appartement_nr") or ""
            items = room.get("items") or []

            header = "{} — {}".format(rnum, rname) if rnum and rname else (rnum or rname or "Geen ruimte")
            if apt_nr:
                header += "  [{}]".format(apt_nr)
            lines.append("## {}  ({} items)".format(header, len(items)))

            for item in items:
                cat = item.get("category") or ""
                fam = item.get("family") or ""
                typ = item.get("type") or ""
                mark = item.get("mark") or ""
                eid = item.get("element_id") or ""
                row = "  [{cat}]  {fam} – {typ}".format(cat=cat, fam=fam, typ=typ)
                if mark:
                    row += "  (Mark: {})".format(mark)
                if eid:
                    row += "  [ID: {}]".format(eid)
                lines.append(row)

            lines.append("")

        return "\n".join(lines)
