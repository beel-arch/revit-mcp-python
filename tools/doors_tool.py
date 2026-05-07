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

    header = "| Mark | Familie | Type | Van kamer | Naar kamer | Verdieping |"
    sep    = "|------|---------|------|-----------|------------|------------|"
    lines.append(header)
    lines.append(sep)

    for d in doors:
        mark = d.get("mark") or "-"
        family = d.get("family_name") or "-"
        dtype = d.get("type_name") or "-"
        from_r = _format_room(d.get("from_room"))
        to_r = _format_room(d.get("to_room"))
        level = d.get("level") or "-"
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            mark, family, dtype, from_r, to_r, level))

    lines.append("")
    lines.append("Totaal: {} deur(en)".format(len(doors)))
    return "\n".join(lines)


def register_doors_tools(mcp, revit_get):

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
    async def debug_doors(ctx: Context) -> str:
        """Debug: show phases and FromRoom/ToRoom test results for the first door in the model."""
        import json
        resp = await revit_get("/doors/debug", ctx)
        return json.dumps(resp, indent=2)
