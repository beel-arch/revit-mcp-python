# -*- coding: UTF-8 -*-
"""
Doors route
GET /doors/                     - all doors with FromRoom / ToRoom data
GET /doors/room/<room_name>     - doors adjacent to rooms whose name contains room_name (case-insensitive substring)
GET /doors/apartment/<prefix>   - doors whose FromRoom or ToRoom apartment number starts with prefix
GET /doors/groupby/<group_param>/<prefix> - zelfde filter, maar op een willekeurige
                                  grouping-parameter (project profile); prefix 'all' = geen filter
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from revit_mcp.utils import safe_string, get_family_name_safe, get_element_name_safe
import logging

logger = logging.getLogger(__name__)

DEFAULT_GROUPING_PARAMETER = "BEEL_C_TX_AppartementNummer"


def _elem_id_int(elem_id):
    try:
        return int(elem_id.IntegerValue)
    except AttributeError:
        return int(elem_id.Value)


def _room_data(room, group_param, is_default_param):
    if room is None:
        return None
    try:
        name = safe_string(room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or "")
    except Exception:
        name = ""
    try:
        number = safe_string(room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or "")
    except Exception:
        number = ""
    group_val = None
    try:
        p = room.LookupParameter(group_param)
        if p and p.HasValue:
            group_val = safe_string(p.AsString())
    except Exception:
        pass
    return {
        "name": name,
        "number": number,
        "group": group_val,
        "appartement_nr": group_val if is_default_param else None,
        "element_id": _elem_id_int(room.Id),
    }


def _collect_doors(doc, room_name_filter=None, apartment_filter=None, group_param=None):
    try:
        group_param = group_param or DEFAULT_GROUPING_PARAMETER
        is_default_param = group_param == DEFAULT_GROUPING_PARAMETER

        phases = list(DB.FilteredElementCollector(doc).OfClass(DB.Phase))
        last_phase = phases[-1] if phases else None

        collector = (
            DB.FilteredElementCollector(doc)
            .OfCategory(DB.BuiltInCategory.OST_Doors)
            .WhereElementIsNotElementType()
        )

        results = []
        for door in collector:
            try:
                from_room = door.FromRoom[last_phase] if last_phase else None
                to_room = door.ToRoom[last_phase] if last_phase else None

                from_room_data = _room_data(from_room, group_param, is_default_param)
                to_room_data = _room_data(to_room, group_param, is_default_param)

                # Lean filter: room name substring match
                if room_name_filter:
                    rn = room_name_filter.lower()
                    from_name = (from_room_data["name"] if from_room_data else "").lower()
                    to_name = (to_room_data["name"] if to_room_data else "").lower()
                    if rn not in from_name and rn not in to_name:
                        continue

                # Lean filter: prefix match op de grouping-parameter
                if apartment_filter:
                    from_apt = (from_room_data["group"] if from_room_data else "") or ""
                    to_apt = (to_room_data["group"] if to_room_data else "") or ""
                    if not from_apt.startswith(apartment_filter) and not to_apt.startswith(apartment_filter):
                        continue

                try:
                    level_elem = doc.GetElement(door.LevelId)
                    level_name = safe_string(level_elem.Name) if level_elem else ""
                except Exception:
                    level_name = ""

                try:
                    mark_param = door.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                    mark = safe_string(mark_param.AsString() or "") if mark_param else ""
                except Exception:
                    mark = ""

                try:
                    sym = doc.GetElement(door.GetTypeId())
                    family_name = safe_string(get_family_name_safe(sym)) if sym else ""
                    type_name = safe_string(get_element_name_safe(sym)) if sym else ""
                except Exception:
                    family_name = ""
                    type_name = ""

                # Width & Height from type parameters (internal units = feet → mm)
                width_mm = None
                height_mm = None
                try:
                    sym = doc.GetElement(door.GetTypeId())
                    if sym:
                        w = sym.get_Parameter(DB.BuiltInParameter.DOOR_WIDTH)
                        if w and w.HasValue:
                            width_mm = int(round(w.AsDouble() * 304.8))
                        h = sym.get_Parameter(DB.BuiltInParameter.DOOR_HEIGHT)
                        if h and h.HasValue:
                            height_mm = int(round(h.AsDouble() * 304.8))
                except Exception:
                    pass

                results.append({
                    "element_id": _elem_id_int(door.Id),
                    "mark": mark,
                    "family_name": family_name,
                    "type_name": type_name,
                    "width_mm": width_mm,
                    "height_mm": height_mm,
                    "level": level_name,
                    "from_room": from_room_data,
                    "to_room": to_room_data,
                })
            except Exception:
                pass

        results.sort(key=lambda x: (x["level"], x["mark"] or ""))

        return routes.make_response(data={
            "count": len(results),
            "filters": {
                "room_name": room_name_filter or "",
                "apartment": apartment_filter or "",
                "group_parameter": group_param,
            },
            "doors": results,
        })

    except Exception as e:
        msg = "{}: {}".format(type(e).__name__, str(e))
        logger.error("Error in _collect_doors: {}".format(msg))
        return routes.make_response(data={"error": msg}, status=500)


def register_doors_routes(api):

    @api.route('/doors/debug', methods=["GET"])
    def debug_doors(doc, request=None):
        """Debug: show phases and FromRoom/ToRoom for first door."""
        try:
            phases = list(DB.FilteredElementCollector(doc).OfClass(DB.Phase))
            phase_names = []
            for p in phases:
                try:
                    phase_names.append(safe_string(p.Name))
                except Exception:
                    phase_names.append("?")

            collector = (
                DB.FilteredElementCollector(doc)
                .OfCategory(DB.BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
            )
            door = None
            for d in collector:
                door = d
                break

            door_info = None
            if door:
                door_info = {"element_id": _elem_id_int(door.Id)}
                last_phase = phases[-1] if phases else None
                # Test indexer syntax: door.FromRoom[phase]
                for i, phase in enumerate(phases):
                    try:
                        fr = door.FromRoom[phase]
                        tr = door.ToRoom[phase]
                        fr_name = fr.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() if fr else None
                        to_name = tr.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() if tr else None
                        door_info["indexer_phase_{}_from".format(i)] = safe_string(fr_name) if fr_name else None
                        door_info["indexer_phase_{}_to".format(i)] = safe_string(to_name) if to_name else None
                    except Exception as e:
                        door_info["indexer_phase_{}_error".format(i)] = str(e)

            return routes.make_response(data={
                "phase_count": len(phases),
                "phases": phase_names,
                "first_door": door_info,
            })
        except Exception as e:
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route('/doors/', methods=["GET"])
    def get_all_doors(doc, request=None):
        """Return all doors with FromRoom and ToRoom data."""
        return _collect_doors(doc)

    @api.route('/doors/room/<room_name>', methods=["GET"])
    def get_doors_by_room(doc, room_name):
        """Return doors adjacent to rooms whose name contains room_name (case-insensitive substring)."""
        return _collect_doors(doc, room_name_filter=room_name)

    @api.route('/doors/apartment/<apartment_prefix>', methods=["GET"])
    def get_doors_by_apartment(doc, apartment_prefix):
        """Return doors whose FromRoom or ToRoom is in apartments starting with apartment_prefix."""
        return _collect_doors(doc, apartment_filter=apartment_prefix)

    @api.route('/doors/groupby/<group_param>/<group_prefix>', methods=["GET"])
    def get_doors_by_group(doc, group_param, group_prefix):
        """Doors gefilterd op prefix van een willekeurige grouping-parameter
        (project profile). group_prefix 'all' = geen filter."""
        prefix = None if (group_prefix or "").lower() == "all" else group_prefix
        return _collect_doors(doc, apartment_filter=prefix, group_param=group_param)
