"""MCP tool: query doors with FromRoom / ToRoom data from the Revit model."""

from mcp.server.fastmcp import Context


def _format_room(room_data):
    if not room_data:
        return "(geen kamer)"
    name = room_data.get("name") or ""
    number = room_data.get("number") or ""
    if name and number:
        return "{} ({})".format(name, number)
    return name or number or "(geen kamer)"


def _format_report(doors, room_name_filter, apartment_filter):
    lines = [
        "## Deuren met kamerinformatie",
        "",
        "**Zwenkrichting:** ToRoom = de kamer waar de deur *naartoe* zwenkt (het paneel gaat die ruimte in).",
        "'Naar buiten draaien' vanuit kamer X betekent: X is de **FromRoom** (niet de ToRoom).",
        "",
    ]

    active_filters = []
    if room_name_filter:
        active_filters.append("kamer: '{}'".format(room_name_filter))
    if apartment_filter:
        active_filters.append("appartement: '{}'".format(apartment_filter))
    if active_filters:
        lines.append("*Filter: {}*".format(", ".join(active_filters)))
        lines.append("")

    if not doors:
        lines.append("Geen deuren gevonden.")
        return "\n".join(lines)

    header = "| Element ID | Mark | Familie | Type | B×H (mm) | Van kamer | Naar kamer | Verdieping |"
    sep    = "|------------|------|---------|------|----------|-----------|------------|------------|"
    lines.append(header)
    lines.append(sep)

    for d in doors:
        eid = d.get("element_id") or "-"
        mark = d.get("mark") or "-"
        family = d.get("family_name") or "-"
        dtype = d.get("type_name") or "-"
        w = d.get("width_mm")
        h = d.get("height_mm")
        dims = "{}×{}".format(w, h) if (w and h) else "-"
        from_r = _format_room(d.get("from_room"))
        to_r = _format_room(d.get("to_room"))
        level = d.get("level") or "-"
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
            eid, mark, family, dtype, dims, from_r, to_r, level))

    lines.append("")
    lines.append("Totaal: {} deur(en)".format(len(doors)))
    return "\n".join(lines)


def register_doors_tools(mcp, revit_get, revit_post):

    @mcp.tool()
    async def get_doors_with_rooms(
        ctx: Context,
        room_name: str = "",
        apartment_filter: str = "",
    ) -> str:
        """
        Geeft een overzicht van alle deuren met de aangrenzende kamers (FromRoom en ToRoom).

        Zwenkrichting:
          ToRoom  = de kamer waar het deurpaneel naartoe zwenkt (de deur 'gaat open in' die ruimte).
          FromRoom = de kamer aan de andere kant.

          "Deuren draaien naar buiten" vanuit kamer X  →  X is de FromRoom (niet de ToRoom).
          "Deuren draaien naar binnen" in kamer X       →  X is de ToRoom.

          Voorbeeld: badkamerdeuren die naar buiten draaien = badkamer is FromRoom voor al die deuren.

        Parameters:
          room_name:        Optionele substring van een kamernaam om te filteren (hoofdletterongevoelig).
                            Geeft alleen deuren terug die grenzen aan kamers waarvan de naam dit
                            bevat. Bv. "badkamer", "toilet", "leefruimte".
                            Leeg = alle deuren.
          apartment_filter: Optioneel prefix op het appartementsnummer van de aangrenzende kamer.
                            Bv. "1." geeft deuren in appartementen 1.A, 1.B, enz.
                            Leeg = alle appartementen.
                            Roep eerst get_model_structure op om geldige prefixes te ontdekken.

        Gebruik:
          - "Welke deurtypes geven toegang tot de leefruimte?"
              → room_name="leefruimte"
          - "Welke deur zit tussen de inkom en de leefruimte?"
              → room_name="" en redeneer op basis van FromRoom/ToRoom combinaties
          - "Draaien de badkamerdeuren naar buiten?"
              → room_name="badkamer", controleer of badkamer altijd FromRoom is (nooit ToRoom)
          - "Welke deurtypen zitten er in appartement 2.A?"
              → apartment_filter="2.A"
        """
        room_name = room_name.strip()
        apartment_filter = apartment_filter.strip()

        # Choose the lean endpoint
        if room_name:
            endpoint = "/doors/room/{}".format(room_name)
        elif apartment_filter:
            endpoint = "/doors/apartment/{}".format(apartment_filter)
        else:
            endpoint = "/doors/"

        resp = await revit_get(endpoint, ctx)

        if isinstance(resp, str):
            return "Fout bij ophalen deuren: {}".format(resp)
        if isinstance(resp, dict) and "error" in resp:
            return "Fout bij ophalen deuren: {}".format(resp["error"])

        doors = resp.get("doors") or []

        # Secondary in-tool filter: apartment on room_name results (or vice versa)
        if room_name and apartment_filter:
            def matches_apt(door):
                for side in ("from_room", "to_room"):
                    rd = door.get(side)
                    if rd:
                        apt = rd.get("appartement_nr") or ""
                        if apt.startswith(apartment_filter):
                            return True
                return False
            doors = [d for d in doors if matches_apt(d)]

        return _format_report(doors, room_name, apartment_filter)

    @mcp.tool()
    async def write_door_marks_from_room(
        apartment_filter: str = "",
        room_name_filter: str = "",
        ctx: Context = None,
    ) -> str:
        """
        Write door marks using apartment number + room number of the primary room.

        ## Primary room selection — weight system

        Every door connects two rooms. The "primary room" is the one that gives the
        door its identity (its destination). Selection uses weights:

          weight 0 — no apartment number (circulatie, gemeenschappelijk deel)
          weight 1 — Inkom
          weight 2 — all other rooms (Leefruimte, Badkamer, Berging, Slaapkamer, …)

        Pick the room with the HIGHEST weight.
        Tie (both weight 2) → use ToRoom as tiebreaker.

        ## Mark format

          "<appartement_nr>-<room_number>"   e.g. "1.A.Niv 0.12-02"

        When multiple doors share the same primary room within the same apartment,
        a letter suffix is appended: "…-02a", "…-02b", "…-02c", …

        ## Parameters

        - apartment_filter: prefix on apartment number (e.g. "1.A", "1.A.Niv 0.12")
        - room_name_filter: optional room name substring to further limit scope
        """
        apartment_filter = apartment_filter.strip()
        room_name_filter = room_name_filter.strip()

        # Fetch doors
        if room_name_filter:
            endpoint = "/doors/room/{}".format(room_name_filter)
        elif apartment_filter:
            endpoint = "/doors/apartment/{}".format(apartment_filter)
        else:
            endpoint = "/doors/"

        resp = await revit_get(endpoint, ctx)
        if isinstance(resp, str):
            return "Fout bij ophalen deuren: {}".format(resp)
        if isinstance(resp, dict) and "error" in resp:
            return "Fout bij ophalen deuren: {}".format(resp["error"])

        doors = resp.get("doors") or []

        # Secondary filter when both params given
        if room_name_filter and apartment_filter:
            def _matches(door):
                for side in ("from_room", "to_room"):
                    rd = door.get(side)
                    if rd and (rd.get("appartement_nr") or "").startswith(apartment_filter):
                        return True
                return False
            doors = [d for d in doors if _matches(d)]

        # Weight function
        def _weight(room):
            if not room:
                return -1
            if not (room.get("appartement_nr") or ""):
                return 0   # circulatie / gemeenschappelijk
            name = (room.get("name") or "").lower()
            if "inkom" in name:
                return 1
            return 2

        # Pick primary room per door
        assignments = []  # (element_id, apt_nr, room_nr)
        for door in doors:
            eid = door.get("element_id")
            if not eid:
                continue
            fr = door.get("from_room")
            tr = door.get("to_room")
            wf = _weight(fr)
            wt = _weight(tr)
            primary = tr if wt >= wf else fr  # ToRoom wins on tie
            if not primary:
                continue
            apt_nr = primary.get("appartement_nr") or ""
            room_nr = primary.get("number") or ""
            assignments.append((eid, apt_nr, room_nr))

        # Count occurrences of (apt_nr, room_nr) to detect duplicates
        from collections import Counter
        key_counts = Counter((a, r) for _, a, r in assignments)

        # Assign suffix where needed
        key_seen = Counter()
        writes = []
        for eid, apt_nr, room_nr in assignments:
            key = (apt_nr, room_nr)
            base = "{}-{}".format(apt_nr, room_nr) if apt_nr else room_nr
            if key_counts[key] > 1:
                idx = key_seen[key]
                suffix = chr(ord("a") + idx)
                mark = "{}{}".format(base, suffix)
            else:
                mark = base
            key_seen[key] += 1
            writes.append({"element_id": eid, "param": "mark", "value": mark})

        if not writes:
            return "Geen deuren gevonden om te schrijven."

        # Bulk write
        write_resp = await revit_post("/element/write_params_bulk", {"writes": writes}, ctx)
        if isinstance(write_resp, str):
            return "Fout bij schrijven: {}".format(write_resp)
        if isinstance(write_resp, dict) and "error" in write_resp:
            return "Fout bij schrijven: {}".format(write_resp["error"])

        written = write_resp.get("written", 0)
        errors = write_resp.get("errors", 0)

        # Preview first 10 for confirmation
        preview = "\n".join(
            "  element {} → mark='{}'".format(w["element_id"], w["value"])
            for w in writes[:10]
        )
        if len(writes) > 10:
            preview += "\n  ... en {} meer".format(len(writes) - 10)

        return "{} deuren geschreven, {} fouten.\n\nVoorbeeld:\n{}".format(
            written, errors, preview)

    @mcp.tool()
    async def debug_doors(ctx: Context) -> str:
        """Debug: show phases and FromRoom/ToRoom test results for the first door in the model."""
        import json
        resp = await revit_get("/doors/debug", ctx)
        return json.dumps(resp, indent=2)
