"""MCP tool: check window area compliance per room (Belgische daglichtnorm)."""

import re
from mcp.server.fastmcp import Context

LIVING_RATIO = 1.0 / 6.0   # leefruimtes: 1/6
BEDROOM_RATIO = 1.0 / 8.0  # slaapkamers: 1/8

FT_TO_M = 0.3048

WIDTH_PARAMS = ["Width", "Breedte", "width", "Rough Width", "Ruwe breedte"]
HEIGHT_PARAMS = ["Height", "Hoogte", "height", "Rough Height", "Ruwe hoogte"]
FROM_ROOM_PARAMS = ["FromRoom", "From Room", "from_room", "Van ruimte"]


def _classify_room(name):
    """Map a Revit room name to a checklist rule key (matches room_checklist_tool)."""
    n = name.lower()
    if any(w in n for w in ["leef", "woon", "zitkamer", "zithoek", "eethoek"]):
        return "leefruimte"
    if "keuken" in n:
        return "keuken"
    if any(w in n for w in ["ouder", "master", "hoofd"]):
        return "slaapkamer_ouders"
    if any(w in n for w in ["kinder", "kind", "slaap", "chambre", "bedroom"]):
        return "slaapkamer_kind"
    if any(w in n for w in ["bad", "douche", "sanitair"]):
        return "badkamer"
    if any(w in n for w in ["inkom", "hal", "gang", "vestiaire", "entree", "entrée"]):
        return "inkomzone"
    if any(w in n for w in ["berg", "opslag", "stock", "stockage"]):
        return "berging"
    if any(w in n for w in ["toilet", "wc"]):
        return "toilet"
    return None


def _is_bedroom(room_type):
    return room_type in ("slaapkamer_kind", "slaapkamer_ouders", "slaapkamer_kind_gedeeld")


def _find_param(params, names):
    """Return the first param dict whose name is in names."""
    for p in params:
        if p.get("name") in names:
            return p
    return None


def _parse_length_m(param):
    """
    Parse a Revit length parameter to meters.
    Tries value_string first (e.g. '0.914 m', '900 mm') then falls back
    to raw value converted from feet (Revit internal unit).
    """
    if param is None:
        return None

    val_str = (param.get("value_string") or "").strip()
    if val_str:
        m = re.match(r"^([\d.,]+)\s*(m|mm|cm|ft)?", val_str)
        if m:
            num = float(m.group(1).replace(",", "."))
            unit = m.group(2)
            if unit == "mm":
                return num / 1000.0
            if unit == "cm":
                return num / 100.0
            if unit == "ft":
                return num * FT_TO_M
            return num  # 'm' or unitless display → already meters

    raw = param.get("value")
    if raw is not None:
        try:
            return float(raw) * FT_TO_M  # Revit internal = feet
        except (TypeError, ValueError):
            pass
    return None


def _match_room(from_room_raw, rooms_by_name, rooms_by_number):
    """Try several formats to resolve a FromRoom value to a room dict."""
    if not from_room_raw or str(from_room_raw).strip() in ("", "None", "null"):
        return None
    text = str(from_room_raw).strip()

    if text in rooms_by_name:
        return rooms_by_name[text]
    if text in rooms_by_number:
        return rooms_by_number[text]

    # "Room Name (Number)" format
    m = re.match(r"^(.+?)\s*\((.+?)\)$", text)
    if m:
        by_name = rooms_by_name.get(m.group(1).strip())
        if by_name:
            return by_name
        by_num = rooms_by_number.get(m.group(2).strip())
        if by_num:
            return by_num

    # "Room Name [ElementId]" format — match by name prefix
    m2 = re.match(r"^(.+?)\s*\[\d+\]$", text)
    if m2:
        return rooms_by_name.get(m2.group(1).strip())

    return None


def _format_report(room_results, unassigned_windows):
    lines = ["# Daglichtcheck – Raamoppervlaktes per Ruimte", ""]

    failures = []
    for r in sorted(room_results, key=lambda x: (x.get("appartement_nr") or "", x["room_name"])):
        room_type = r["room_type"]
        ratio = r["ratio"]
        compliant = r["compliant"]

        if room_type == "leefruimte":
            min_ratio_str = "1/6 ({:.4f})".format(LIVING_RATIO)
        elif _is_bedroom(room_type):
            min_ratio_str = "1/8 ({:.4f})".format(BEDROOM_RATIO)
        else:
            min_ratio_str = "n.v.t."

        ratio_str = "{:.4f}".format(ratio) if ratio is not None else "—"

        if compliant is True:
            status = "✓ OK"
        elif compliant is False:
            status = "✗ TE WEINIG DAGLICHT"
            failures.append("{} – {}".format(r.get("appartement_nr") or "?", r["room_name"]))
        else:
            status = "– n.v.t."

        apt = r.get("appartement_nr") or ""
        apt_str = "  [{}]".format(apt) if apt else ""
        lines.append("### {} ({}){}".format(r["room_name"], r["room_number"] or "?", apt_str))
        lines.append("  Ruimteoppervlakte : {:.2f} m²".format(r["room_area"]))
        lines.append("  Ramen             : {}  |  Totaal raamoppervlak: {:.3f} m²".format(
            r["window_count"], r["total_window_area"]))
        lines.append("  Ratio             : {}  |  Minimum: {}".format(ratio_str, min_ratio_str))
        lines.append("  Status            : {}".format(status))
        lines.append("")

    lines.append("─" * 60)
    if failures:
        lines.append("TEKORTKOMINGEN ({})".format(len(failures)))
        for f in failures:
            lines.append("  - {}".format(f))
    else:
        lines.append("Alle gecontroleerde ruimtes voldoen aan de daglichtnorm ✓")

    if unassigned_windows:
        lines.append("")
        lines.append("## Ramen zonder ruimtekoppeling ({})".format(len(unassigned_windows)))
        lines.append("Controleer of deze ramen correct zijn geplaatst (geen 'From Room'):")
        for w in unassigned_windows:
            w_area = w.get("area_m2")
            area_str = "{:.3f} m²".format(w_area) if w_area else "onbekend"
            lines.append("  - ID {:>10}  {}  opp: {}  [from_room: {}]".format(
                w["id"], w.get("type", "?"), area_str, w.get("from_room_raw") or "—"))

    return "\n".join(lines)


def register_window_area_tools(mcp, revit_get):

    @mcp.tool()
    async def check_window_area_compliance(ctx: Context, apartment_filter: str = "") -> str:
        """
        Controleer of de raamoppervlaktes per ruimte voldoen aan de daglichtnorm.

        Parameters:
          apartment_filter: Optional substring to limit the check to matching apartment numbers
                            (e.g. "1.A" for block 1.A only).
                            Leave empty to check all apartments.
                            Call get_model_structure first to discover valid values.

        Regels:
        - Leefruimtes (woon-, zitkamer …): raamoppervlak ≥ 1/6 vloeroppervlak
        - Slaapkamers:                     raamoppervlak ≥ 1/8 vloeroppervlak
        - Overige ruimtes:                 geen norm van toepassing

        Werking:
        1. Haalt alle Rooms op uit Revit (filtered by apartment_filter if given).
        2. Haalt alle Windows op en leest per raam de breedte, hoogte en
           FromRoom-parameter.
        3. Groepeert ramen per ruimte en berekent de ratio
           (totaal raamoppervlak / vloeroppervlak).
        4. Rapporteert naleving per ruimte; ramen zonder FromRoom worden apart
           vermeld voor controle.
        """
        # 1. Fetch all rooms
        rooms_resp = await revit_get("/rooms/", ctx)
        if isinstance(rooms_resp, str):
            return "Fout bij ophalen rooms: {}".format(rooms_resp)
        if isinstance(rooms_resp, dict) and "error" in rooms_resp:
            return "Fout bij ophalen rooms: {}".format(rooms_resp["error"])

        rooms_list = (rooms_resp or {}).get("rooms", [])
        if not rooms_list:
            return "Geen rooms gevonden in het model."

        f = apartment_filter.strip() if apartment_filter else ""
        if f:
            rooms_list = [r for r in rooms_list if (r.get("appartement_nr") or "").startswith(f)]
        if not rooms_list:
            return "Geen rooms gevonden voor filter '{}'.".format(f)

        rooms_by_id = {}
        rooms_by_name = {}
        rooms_by_number = {}
        for room in rooms_list:
            room_id = room.get("id")
            if room_id is not None:
                rooms_by_id[int(room_id)] = room
            name = (room.get("name") or "").strip()
            number = (room.get("number") or "").strip()
            if name and name not in rooms_by_name:
                rooms_by_name[name] = room
            if number and number not in rooms_by_number:
                rooms_by_number[number] = room

        # 2. Fetch all windows
        windows_resp = await revit_get("/elements_by_category/Windows", ctx)
        if isinstance(windows_resp, str):
            return "Fout bij ophalen ramen: {}".format(windows_resp)
        if isinstance(windows_resp, dict) and "error" in windows_resp:
            return "Fout bij ophalen ramen: {}".format(windows_resp["error"])

        window_elements = (windows_resp or {}).get("elements", [])
        if not window_elements:
            return "Geen ramen gevonden in het model."

        # 3. Fetch parameters per window and group by room
        # Note: one API call per window – may be slow for large models.
        windows_by_room = {}   # room_id (int) -> {room, windows:[]}
        unassigned_windows = []

        for el in window_elements:
            el_id = el.get("id")
            if el_id is None:
                continue
            el_id = int(el_id)

            params_resp = await revit_get("/element_parameters/{}".format(el_id), ctx)

            width_m = None
            height_m = None
            from_room_raw = None
            matched_room = None

            if isinstance(params_resp, dict) and "error" not in params_resp:
                inst = params_resp.get("instance_parameters", [])
                type_p = params_resp.get("type_parameters", [])
                all_params = inst + type_p

                width_m = _parse_length_m(_find_param(all_params, WIDTH_PARAMS))
                height_m = _parse_length_m(_find_param(all_params, HEIGHT_PARAMS))

                fr_param = _find_param(inst, FROM_ROOM_PARAMS)  # FromRoom is instance-only
                if fr_param:
                    # Try ElementId match first (value = integer room ID)
                    room_id_val = fr_param.get("value")
                    if room_id_val is not None:
                        try:
                            matched_room = rooms_by_id.get(int(room_id_val))
                        except (TypeError, ValueError):
                            pass
                    # Fallback: string matching on name/number
                    if matched_room is None:
                        from_room_raw = fr_param.get("value_string") or str(room_id_val or "")
                        matched_room = _match_room(from_room_raw, rooms_by_name, rooms_by_number)

            area_m2 = (width_m * height_m) if (width_m and height_m) else 0.0

            window_data = {
                "id": el_id,
                "type": "{} - {}".format(
                    el.get("family_name", ""), el.get("type_name", "")),
                "width_m": width_m,
                "height_m": height_m,
                "area_m2": area_m2,
            }

            if matched_room:
                key = int(matched_room.get("id", 0))
                if key not in windows_by_room:
                    windows_by_room[key] = {"room": matched_room, "windows": []}
                windows_by_room[key]["windows"].append(window_data)
            else:
                window_data["from_room_raw"] = from_room_raw
                unassigned_windows.append(window_data)

        # 4. Build per-room results
        room_results = []
        rooms_with_windows = set(windows_by_room.keys())  # set of room IDs

        for room_id_key, data in windows_by_room.items():
            room = data["room"]
            windows = data["windows"]

            total_window_area = sum(w["area_m2"] for w in windows)
            room_area = room.get("area_m2") or 0.0
            room_type = _classify_room(room.get("name", ""))

            ratio = (total_window_area / room_area) if room_area > 0 else None

            if room_type == "leefruimte":
                compliant = (ratio >= LIVING_RATIO) if ratio is not None else None
            elif _is_bedroom(room_type):
                compliant = (ratio >= BEDROOM_RATIO) if ratio is not None else None
            else:
                compliant = None  # not applicable

            room_results.append({
                "room_name": room.get("name", "?"),
                "room_number": room.get("number"),
                "appartement_nr": room.get("appartement_nr"),
                "room_area": room_area,
                "window_count": len(windows),
                "total_window_area": total_window_area,
                "ratio": ratio,
                "room_type": room_type,
                "compliant": compliant,
            })

        # Add rooms without windows that still require a check (keyed by room ID now)
        for room in rooms_list:
            room_id = room.get("id")
            if room_id is not None and int(room_id) in rooms_with_windows:
                continue
            name = room.get("name", "")
            room_type = _classify_room(name)
            if room_type not in ("leefruimte", "slaapkamer_kind",
                                  "slaapkamer_ouders", "slaapkamer_kind_gedeeld"):
                continue
            room_results.append({
                "room_name": name,
                "room_number": room.get("number"),
                "appartement_nr": room.get("appartement_nr"),
                "room_area": room.get("area_m2") or 0.0,
                "window_count": 0,
                "total_window_area": 0.0,
                "ratio": 0.0,
                "room_type": room_type,
                "compliant": False,
            })

        return _format_report(room_results, unassigned_windows)
