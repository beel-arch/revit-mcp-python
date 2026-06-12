"""MCP tool: check required fixtures in bathrooms (and future room types) per BEEL rules."""

import re
from urllib.parse import quote
from mcp.server.fastmcp import Context

from .project_profile_tool import get_grouping, DEFAULT_GROUPING_PARAMETER

# ---------------------------------------------------------------------------
# Rules per room type
# Each entry in "checks": (label, ok_func(detected, personen, slaapkamers), req_func(personen, slaapkamers))
# ---------------------------------------------------------------------------

FIXTURE_RULES = {
    "badkamer": {
        "room_keywords": ["bad", "douche", "sanitair"],
        "checks": [
            (
                "Wastafel",
                lambda d, p, k: d["wastafel"] >= (2 if p >= 5 else 1),
                lambda p, k: "{} vereist".format(2 if p >= 5 else 1),
            ),
            (
                "Spiegel",
                lambda d, p, k: d["spiegel"] >= (2 if p >= 5 else 1),
                lambda p, k: "{} vereist".format(2 if p >= 5 else 1),
            ),
            (
                "Tablet",
                lambda d, p, k: d["tablet"] >= (2 if p >= 5 else 1),
                lambda p, k: "{} vereist".format(2 if p >= 5 else 1),
            ),
            (
                "Douche",
                lambda d, p, k: d["douche"] if k < 3 else True,
                lambda p, k: "vereist (< 3 slaapkamers)" if k < 3 else "n.v.t.",
            ),
            (
                "Ligbad",
                lambda d, p, k: d["ligbad"] if k >= 3 else not d["ligbad"],
                lambda p, k: "vereist (>= 3 slaapkamers)" if k >= 3 else "NIET toegestaan (< 3 slaapkamers)",
            ),
        ],
    },
}


def _is_room_type(room_name, room_type):
    """Return True if room_name matches any keyword for room_type."""
    rules = FIXTURE_RULES.get(room_type)
    if not rules:
        return False
    n = room_name.lower()
    return any(kw in n for kw in rules["room_keywords"])


def _detect_fixtures(families):
    """Count/detect fixture types from a list of lowercased family names."""
    return {
        "toilet":   sum(1 for f in families if "toilet"   in f),
        "wastafel": sum(1 for f in families if "wastafel" in f),
        "spiegel":  sum(1 for f in families if "spiegel"  in f),
        "tablet":   sum(1 for f in families if "tablet"   in f),
        "ligbad":   any("ligbad" in f for f in families),
        "douche":   any("douche" in f for f in families),
    }


def _format_present(detected, key):
    """Return 'ja' / count string for a detected fixture."""
    val = detected[key]
    if isinstance(val, bool):
        return "ja" if val else "nee"
    return str(val)


def _format_report(grouped, apartment_filter, room_type):
    sanitair_label = "ligbad met douchemogelijkheid" if room_type == "badkamer" else room_type
    title = "# Fixture Check – {}".format(sanitair_label)
    if apartment_filter:
        title += "  (filter: '{}')".format(apartment_filter)
    lines = [title, ""]

    all_ok = True
    checks = FIXTURE_RULES[room_type]["checks"]

    for apt_nr in sorted(grouped.keys()):
        data = grouped[apt_nr]
        p = data["personen"]
        k = data["slaapkamers"]
        sanitair_type = "ligbad met douchemogelijkheid" if k >= 3 else "inloopdouche"

        lines.append("## Appartement {}  ({} personen | {} slaapkamers → {})".format(
            apt_nr, p, k, sanitair_type))
        lines.append("")

        apt_ok = True
        for room in data["rooms"]:
            rnum = room["number"]
            rname = room["name"]
            detected = _detect_fixtures(data["fixtures"].get(room["id"], []))

            lines.append("**{} ({})**".format(rname, rnum))
            room_ok = True
            for label, ok_fn, req_fn in checks:
                ok = ok_fn(detected, p, k)
                req_str = req_fn(p, k)
                status = "OK" if ok else "ONTBREEKT"
                mark = "v" if ok else "x"
                present = _format_present(detected, label.lower().split()[0])
                lines.append("  [{mark}] {label:<20} aanwezig: {present:<5}  {req}  {status}".format(
                    mark=mark, label=label, present=present, req=req_str, status=status))
                if not ok:
                    room_ok = False
                    apt_ok = False
                    all_ok = False

            room_verdict = "CONFORM" if room_ok else "TEKORTKOMINGEN"
            lines.append("  Eindoordeel: {} {}".format("v" if room_ok else "x", room_verdict))
            lines.append("")

        apt_verdict = "ALLES CONFORM" if apt_ok else "TEKORTKOMINGEN GEVONDEN"
        lines.append("Eindoordeel appartement: {} {}".format("v" if apt_ok else "x", apt_verdict))
        lines.append("")

    lines.append("-" * 60)
    lines.append("Totaaloordeel: {}".format("ALLES CONFORM" if all_ok else "TEKORTKOMINGEN GEVONDEN"))
    return "\n".join(lines)


def register_bathroom_checklist_tools(mcp, revit_get):

    @mcp.tool()
    async def check_room_fixtures(
        ctx: Context,
        apartment_filter: str = "",
        room_type: str = "badkamer",
    ) -> str:
        """
        Controleer of de vereiste inrichtingselementen aanwezig zijn in badkamers per appartement.

        Vereisten badkamer (BEEL regels):
          - Wastafel:    1 stuks (2 stuks als Aantal personen >= 5)
          - Spiegel:     1 stuks (2 stuks als Aantal personen >= 5)
          - Tablet:      1 stuks (2 stuks als Aantal personen >= 5)
          - Sanitair:    inloopdouche als Aantal slaapkamers < 3
                         ligbad met douchemogelijkheid als Aantal slaapkamers >= 3
                         Ligbad is NIET toegestaan bij < 3 slaapkamers

        Familienamen (case-insensitief):
          - Toilet    → bevat "toilet"
          - Wastafel  → bevat "wastafel"
          - Spiegel   → bevat "spiegel"
          - Tablet    → bevat "tablet"
          - Ligbad    → bevat "bad" of "ligbad"
          - Douche    → bevat "douche"

        Parameters:
          apartment_filter: Prefix voor appartementsnummers (bv. "1." voor blok 1,
                            "1.A" voor enkel appartement 1.A).
                            Leeg = alle appartementen.
                            Roep eerst get_model_structure op om geldige waarden te ontdekken.
          room_type:        Ruimtetype om te controleren. Standaard "badkamer".
                            Toekomstige types worden hier toegevoegd.
        """
        if room_type not in FIXTURE_RULES:
            return "Onbekend ruimtetype '{}'. Beschikbare types: {}".format(
                room_type, ", ".join(FIXTURE_RULES.keys()))

        # 1. Profile-aware grouping
        group_param, _group_label, _profile = await get_grouping(revit_get, ctx)

        # 2. WO areas -> occupancy per apartment
        areas_resp = await revit_get("/areas/WO", ctx)
        if isinstance(areas_resp, str):
            return "Fout bij ophalen WO areas: {}".format(areas_resp)
        if isinstance(areas_resp, dict) and "error" in areas_resp:
            return "Fout bij ophalen WO areas: {}".format(areas_resp["error"])

        wo_map = {}
        for a in (areas_resp.get("areas") or []):
            m = re.match(r"^(\d+)/(\d+)$", (a.get("name") or "").strip())
            if m:
                wo_map[a["number"]] = {
                    "slaapkamers": int(m.group(1)),
                    "personen": int(m.group(2)),
                }

        # 3. Rooms -> identify target rooms
        rooms_resp = await revit_get("/rooms/", ctx)
        if isinstance(rooms_resp, str):
            return "Fout bij ophalen rooms: {}".format(rooms_resp)
        if isinstance(rooms_resp, dict) and "error" in rooms_resp:
            return "Fout bij ophalen rooms: {}".format(rooms_resp["error"])

        all_rooms = rooms_resp.get("rooms") or []
        f = apartment_filter.strip() if apartment_filter else ""

        # Build per-apartment groups of target rooms
        grouped = {}
        for room in all_rooms:
            apt_nr = room.get("appartement_nr")
            if not apt_nr:
                continue
            if f and not apt_nr.startswith(f):
                continue
            if not _is_room_type(room.get("name", ""), room_type):
                continue
            if apt_nr not in grouped:
                occ = wo_map.get(apt_nr, {})
                grouped[apt_nr] = {
                    "slaapkamers": occ.get("slaapkamers", 0),
                    "personen": occ.get("personen", 0),
                    "rooms": [],
                    "fixtures": {},
                }
            grouped[apt_nr]["rooms"].append(room)

        if not grouped:
            msg = "Geen {} gevonden".format(room_type)
            if f:
                msg += " voor appartement filter '{}'".format(f)
            msg += "."
            return msg

        # 4. Furnishings — profile-aware URL, URL-safe prefix (strip at first space)
        #    Room-ID matching handles precise apartment filtering client-side.
        cat_str = "plumbing,plumbingeq,furniture"
        url_prefix = f.split(" ")[0] if " " in f else f  # "2.C.Niv" from "2.C.Niv 2.05"

        if group_param == DEFAULT_GROUPING_PARAMETER:
            if url_prefix:
                plumb_url = "/furnishings/byroom/cat/{}/apt/{}".format(
                    cat_str, quote(url_prefix, safe=""))
            else:
                plumb_url = "/furnishings/byroom/cat/{}".format(cat_str)
        else:
            param_seg = quote(group_param, safe="")
            prefix_seg = quote(url_prefix, safe="") if url_prefix else "all"
            plumb_url = "/furnishings/byroom/cat/{}/groupby/{}/{}".format(
                cat_str, param_seg, prefix_seg)

        plumb_resp = await revit_get(plumb_url, ctx)
        if isinstance(plumb_resp, dict) and "rooms" in plumb_resp:
            for room_data in plumb_resp["rooms"]:
                rid = room_data.get("room_id")
                if rid is None:
                    continue
                for item in (room_data.get("items") or []):
                    family = (item.get("family") or "").lower()
                    for apt_data in grouped.values():
                        if any(r["id"] == rid for r in apt_data["rooms"]):
                            apt_data["fixtures"].setdefault(rid, []).append(family)

        # 5. Format report
        return _format_report(grouped, f, room_type)
