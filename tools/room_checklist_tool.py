"""MCP tool: compare Revit room areas against BEEL Checklist Codex Wonen / VMSW requirements."""

from mcp.server.fastmcp import Context

# ---------------------------------------------------------------------------
# Checklist rules derived from BEEL_Checklist_Codex_Wonen.xlsx
# Each entry: (display_label, min_m2_func, formula_string)
# ---------------------------------------------------------------------------

RULES = {
    "leefruimte": (
        "Leefruimte (zithoek + eethoek)",
        lambda p, k: 18.0 + 2.0 * p,
        "18 + 2 × personen",
    ),
    "keuken": (
        "Keuken",
        lambda p, k: 4.0 + 0.5 * p,
        "4 + 0.5 × personen",
    ),
    "slaapkamer_ouders": (
        "Slaapkamer ouders",
        lambda p, k: 11.0,
        "11 m²",
    ),
    "slaapkamer_kind": (
        "Slaapkamer kind",
        lambda p, k: 7.0,
        "7 m² (1 kind)",
    ),
    "slaapkamer_kind_gedeeld": (
        "Slaapkamer (2 kinderen gedeeld)",
        lambda p, k: 12.0,
        "12 m² (2 kinderen)",
    ),
    "badkamer": (
        "Badkamer (zonder toilet)",
        lambda p, k: 3.0 + 0.5 * p,
        "3 + 0.5 × personen",
    ),
    "inkomzone": (
        "Inkomzone",
        lambda p, k: 1.5,
        "1.5 m²",
    ),
    "berging": (
        "Berging (appartement)",
        lambda p, k: 3.0 + 0.5 * p,
        "3 + 0.5 × personen",
    ),
}


def _classify_room(name):
    """Map a Revit room name to a checklist rule key."""
    n = name.lower()
    if any(w in n for w in ["leef", "woon", "zitkamer", "zithoek", "eethoek"]):
        return "leefruimte"
    if "keuken" in n:
        return "keuken"
    if any(w in n for w in ["ouder", "master", "hoofd"]):
        return "slaapkamer_ouders"
    if any(w in n for w in ["kinder", "kind", "slaap", "chambre", "bedroom"]):
        return "slaapkamer_kind"  # refined below based on occupancy
    if any(w in n for w in ["bad", "douche", "sanitair"]):
        return "badkamer"
    if any(w in n for w in ["inkom", "hal", "gang", "vestiaire", "entree", "entrée"]):
        return "inkomzone"
    if any(w in n for w in ["berg", "opslag", "stock", "stockage"]):
        return "berging"
    if any(w in n for w in ["toilet", "wc", "sanitair"]):
        return "toilet"  # no minimum area rule in Codex Wonen
    return None


def _check_rooms_for_apartment(apt_nr, rooms, wo_area):
    """
    Compare the rooms for one apartment against Codex Wonen minimums.

    Returns a list of result dicts:
      {room_name, area_m2, rule, min_m2, ok, diff}
    """
    persons = wo_area.get("aantal_personen") or 0
    bedrooms = wo_area.get("aantal_slaapkamers") or 0

    # Count how many kids' bedrooms we have (non-parent)
    # If (persons - 2) > (bedrooms - 1) some kids share → 12 m²
    parent_kids = max(0, persons - 2)
    kids_rooms = max(0, bedrooms - 1)
    shared_rooms = max(0, parent_kids - kids_rooms)  # rooms that hold 2 kids

    kids_room_count = 0
    results = []

    for room in rooms:
        name = room["name"]
        area = room["area_m2"] or 0.0
        rule_key = _classify_room(name)

        if rule_key is None:
            results.append({
                "room_name": name,
                "area_m2": area,
                "rule": "—",
                "min_m2": None,
                "ok": None,
                "diff": None,
                "note": "Geen minimumoppervlakte in Codex Wonen",
            })
            continue

        if rule_key == "toilet":
            results.append({
                "room_name": name,
                "area_m2": area,
                "rule": "Toilet",
                "formula": "geen minimum",
                "min_m2": None,
                "ok": True,
                "diff": None,
                "note": "Geen minimumoppervlakte in Codex Wonen",
            })
            continue

        # Refine kids bedroom: could be shared
        if rule_key == "slaapkamer_kind":
            kids_room_count += 1
            if shared_rooms > 0 and kids_room_count <= shared_rooms:
                rule_key = "slaapkamer_kind_gedeeld"

        label, min_func, formula = RULES[rule_key]
        min_m2 = round(min_func(persons, bedrooms), 2)
        ok = area >= min_m2
        diff = round(area - min_m2, 2)

        results.append({
            "room_name": name,
            "area_m2": area,
            "rule": label,
            "formula": formula,
            "min_m2": min_m2,
            "ok": ok,
            "diff": diff,
            "note": "",
        })

    return results


def _format_report(grouped):
    """Format comparison results as a readable text report."""
    lines = ["# Codex Wonen – Oppervlaktecheck", ""]

    all_ok = True
    for apt_nr, data in sorted(grouped.items()):
        wo = data["wo_area"]
        rooms_results = data["results"]

        persons = wo.get("aantal_personen", "?")
        bedrooms = wo.get("aantal_slaapkamers", "?")
        wo_area_m2 = wo.get("area_m2", "?")

        lines.append("## Appartement {}".format(apt_nr))
        lines.append("WO area: {} m²  |  {} personen  |  {} slaapkamers".format(
            wo_area_m2, persons, bedrooms))
        lines.append("")
        lines.append("{:<30} {:>8}  {:>8}  {:>8}  {}".format(
            "Ruimte", "Opp.", "Min.", "Diff", "Status"))
        lines.append("-" * 70)

        for r in rooms_results:
            if r["ok"] is None:
                status = "⚠ onbekend"
                lines.append("{:<30} {:>7.2f}m²  {:>8}  {:>8}  {}  {}".format(
                    r["room_name"], r["area_m2"], "—", "—", status, r.get("note", "")))
            elif r["min_m2"] is None:
                # e.g. toilet: no minimum
                status = "– n.v.t."
                lines.append("{:<30} {:>7.2f}m²  {:>8}  {:>8}  {}".format(
                    r["room_name"], r["area_m2"], "—", "—", status))
            else:
                status = "✓ OK" if r["ok"] else "✗ TE KLEIN"
                if not r["ok"]:
                    all_ok = False
                diff_str = "{:+.2f}m²".format(r["diff"])
                lines.append("{:<30} {:>7.2f}m²  {:>7.2f}m²  {:>8}  {}  [{}]".format(
                    r["room_name"], r["area_m2"], r["min_m2"], diff_str, status,
                    r.get("formula", "")))

        lines.append("")

    lines.append("─" * 70)
    lines.append("Eindoordeel: {}".format("ALLES OK ✓" if all_ok else "TEKORTKOMINGEN GEVONDEN ✗"))
    return "\n".join(lines)


def register_room_checklist_tools(mcp, revit_get):

    @mcp.tool()
    async def compare_rooms_with_checklist(ctx: Context) -> str:
        """
        Vergelijk de oppervlaktes van Revit rooms met de BEEL Checklist Codex Wonen (VMSW).

        Werking:
        1. Leest alle Rooms uit Revit (naam, oppervlakte, BEEL_C_TX_AppartementNummer).
        2. Leest WO-areas op (Aantal Personen, Aantal Slaapkamers).
        3. Koppelt rooms aan het juiste appartement via het appartementssnummer.
        4. Controleert per ruimte of de oppervlakte voldoet aan de Codex Wonen minimums:
           - Leefruimte:       18 + 2 × personen m²
           - Keuken:           4 + 0.5 × personen m²
           - Slaapkamer ouders: 11 m²
           - Slaapkamer kind:  7 m² (1 kind) / 12 m² (gedeeld)
           - Badkamer:         3 + 0.5 × personen m²
           - Inkomzone:        1.5 m²
           - Berging:          3 + 0.5 × personen m²
        5. Geeft een leesbaar rapport terug met ✓ / ✗ per ruimte.
        """
        # 1. Fetch rooms
        rooms_resp = await revit_get("/rooms/", ctx)
        if isinstance(rooms_resp, str):
            return "Fout bij ophalen rooms: {}".format(rooms_resp)
        if "error" in rooms_resp:
            return "Fout bij ophalen rooms: {}".format(rooms_resp["error"])

        rooms = rooms_resp.get("rooms", [])
        if not rooms:
            return "Geen rooms gevonden in het model."

        # 2. Fetch WO areas (with Aantal Personen / Slaapkamers)
        areas_resp = await revit_get("/areas/WO", ctx)
        if isinstance(areas_resp, str):
            return "Fout bij ophalen WO areas: {}".format(areas_resp)
        if "error" in areas_resp:
            return "Fout bij ophalen WO areas: {}".format(areas_resp["error"])

        wo_areas = {}
        for a in areas_resp.get("areas", []):
            # Parse "Aantal Slaapkamers/Aantal Personen" from area name (e.g. "3/4")
            import re
            m = re.match(r'^(\d+)/(\d+)$', (a.get("name") or "").strip())
            if m:
                a["aantal_slaapkamers"] = int(m.group(1))
                a["aantal_personen"] = int(m.group(2))
            else:
                a.setdefault("aantal_slaapkamers", None)
                a.setdefault("aantal_personen", None)
            wo_areas[a["number"]] = a

        # 3. Group rooms by appartement_nr
        grouped = {}
        unlinked = []
        for room in rooms:
            apt_nr = room.get("appartement_nr")
            if not apt_nr:
                unlinked.append(room)
                continue
            if apt_nr not in grouped:
                wo = wo_areas.get(apt_nr, {})
                grouped[apt_nr] = {"wo_area": wo, "rooms": [], "results": []}
            grouped[apt_nr]["rooms"].append(room)

        if not grouped:
            msg = "Geen rooms hebben een BEEL_C_TX_AppartementNummer ingevuld."
            if unlinked:
                msg += "\n\nRooms zonder koppeling: {}".format(
                    ", ".join(r["name"] for r in unlinked))
            return msg

        # 4. Compare each apartment
        for apt_nr, data in grouped.items():
            wo = data["wo_area"]
            if not wo:
                data["results"] = [{
                    "room_name": r["name"],
                    "area_m2": r["area_m2"],
                    "rule": "—",
                    "min_m2": None,
                    "ok": None,
                    "diff": None,
                    "note": "WO area '{}' niet gevonden".format(apt_nr),
                } for r in data["rooms"]]
            else:
                data["results"] = _check_rooms_for_apartment(
                    apt_nr, data["rooms"], wo)

        # 5. Format report
        report = _format_report(grouped)

        if unlinked:
            report += "\n\n### Rooms zonder appartementslink\n"
            for r in unlinked:
                report += "  - {} ({} m²)\n".format(r["name"], r["area_m2"])

        return report
