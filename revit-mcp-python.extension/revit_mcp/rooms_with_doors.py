# -*- coding: UTF-8 -*-
"""
Rooms with Doors route  (Room -> Door direction)
GET /rooms/with_doors/                                - all rooms with their doors
GET /rooms/with_doors/apartment/<prefix>              - filtered by appartement_nr prefix (KSS-default)
GET /rooms/with_doors/groupby/<group_param>/<prefix>  - filtered op een willekeurige
                                                        grouping-parameter (project profile);
                                                        prefix "all" = geen filter
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


def _get_group_value(room, group_param):
    try:
        p = room.LookupParameter(group_param)
        if p and p.HasValue:
            return safe_string(p.AsString())
    except Exception:
        pass
    return None


def _collect_rooms_with_doors(doc, apartment_filter=None, group_param=None):
    try:
        group_param = group_param or DEFAULT_GROUPING_PARAMETER
        is_default_param = group_param == DEFAULT_GROUPING_PARAMETER

        # --- collect rooms ---
        room_collector = (
            DB.FilteredElementCollector(doc)
            .OfCategory(DB.BuiltInCategory.OST_Rooms)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        # Build room lookup dict and apply grouping filter
        rooms_by_id = {}
        for room in room_collector:
            try:
                apt_nr = _get_group_value(room, group_param)
                if apartment_filter and not (apt_nr or "").startswith(apartment_filter):
                    continue
                try:
                    name = safe_string(
                        room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or ""
                    )
                except Exception:
                    name = ""
                try:
                    number = safe_string(
                        room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or ""
                    )
                except Exception:
                    number = ""
                try:
                    area_param = room.get_Parameter(DB.BuiltInParameter.ROOM_AREA)
                    area_m2 = round(area_param.AsDouble() * 0.092903, 2) if area_param and area_param.HasValue else None
                except Exception:
                    area_m2 = None
                try:
                    level_elem = doc.GetElement(room.LevelId)
                    level_name = safe_string(level_elem.Name) if level_elem else ""
                except Exception:
                    level_name = ""

                room_id = _elem_id_int(room.Id)
                rooms_by_id[room_id] = {
                    "room_id": room_id,
                    "room_name": name,
                    "room_number": number,
                    "group": apt_nr,
                    "appartement_nr": apt_nr if is_default_param else None,
                    "level": level_name,
                    "area_m2": area_m2,
                    "doors": [],
                }
            except Exception:
                pass

        if not rooms_by_id:
            return routes.make_response(data={
                "total_rooms": 0,
                "rooms_without_doors": 0,
                "group_parameter": group_param,
                "apartment_filter": apartment_filter or "",
                "rooms": [],
            })

        # --- collect all doors, build room_id -> [door_info] mapping ---
        phases = list(DB.FilteredElementCollector(doc).OfClass(DB.Phase))
        last_phase = phases[-1] if phases else None

        door_collector = (
            DB.FilteredElementCollector(doc)
            .OfCategory(DB.BuiltInCategory.OST_Doors)
            .WhereElementIsNotElementType()
        )

        for door in door_collector:
            try:
                from_room = door.FromRoom[last_phase] if last_phase else None
                to_room = door.ToRoom[last_phase] if last_phase else None

                from_id = _elem_id_int(from_room.Id) if from_room else None
                to_id = _elem_id_int(to_room.Id) if to_room else None

                # Only care about doors that touch at least one of our filtered rooms
                if from_id not in rooms_by_id and to_id not in rooms_by_id:
                    continue

                try:
                    mark_param = door.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                    mark = safe_string(mark_param.AsString() or "") if mark_param else ""
                except Exception:
                    mark = ""

                sym = None
                family_name = ""
                type_name = ""
                width_mm = None
                try:
                    sym = doc.GetElement(door.GetTypeId())
                    if sym:
                        family_name = safe_string(get_family_name_safe(sym))
                        type_name = safe_string(get_element_name_safe(sym))
                        w = sym.get_Parameter(DB.BuiltInParameter.DOOR_WIDTH)
                        if w and w.HasValue:
                            width_mm = int(round(w.AsDouble() * 304.8))
                except Exception:
                    pass

                door_id = _elem_id_int(door.Id)

                # Add to from_room if it's in our set
                if from_id in rooms_by_id:
                    rooms_by_id[from_id]["doors"].append({
                        "element_id": door_id,
                        "mark": mark,
                        "family_name": family_name,
                        "type_name": type_name,
                        "width_mm": width_mm,
                        "side": "from_room",
                    })

                # Add to to_room if it's in our set (and not the same as from_room)
                if to_id in rooms_by_id and to_id != from_id:
                    rooms_by_id[to_id]["doors"].append({
                        "element_id": door_id,
                        "mark": mark,
                        "family_name": family_name,
                        "type_name": type_name,
                        "width_mm": width_mm,
                        "side": "to_room",
                    })

            except Exception:
                pass

        # --- assemble result ---
        room_list = sorted(
            rooms_by_id.values(),
            key=lambda r: (r["group"] or "", r["room_name"])
        )

        for room in room_list:
            room["door_count"] = len(room["doors"])

        rooms_without_doors = sum(1 for r in room_list if r["door_count"] == 0)

        return routes.make_response(data={
            "total_rooms": len(room_list),
            "rooms_without_doors": rooms_without_doors,
            "group_parameter": group_param,
            "apartment_filter": apartment_filter or "",
            "rooms": room_list,
        })

    except Exception as e:
        msg = "{}: {}".format(type(e).__name__, str(e))
        logger.error("Error in _collect_rooms_with_doors: {}".format(msg))
        return routes.make_response(data={"error": msg}, status=500)


def register_rooms_with_doors_routes(api):

    @api.route('/rooms/with_doors/', methods=["GET"])
    def get_rooms_with_doors_all(doc, request=None):
        """Return all rooms with their associated doors."""
        return _collect_rooms_with_doors(doc)

    @api.route('/rooms/with_doors/apartment/<apartment_prefix>', methods=["GET"])
    def get_rooms_with_doors_by_apartment(doc, apartment_prefix):
        """Return rooms filtered by apartment number prefix, each with their doors."""
        return _collect_rooms_with_doors(doc, apartment_filter=apartment_prefix)

    @api.route('/rooms/with_doors/groupby/<group_param>/<group_prefix>', methods=["GET"])
    def get_rooms_with_doors_by_group(doc, group_param, group_prefix):
        """Rooms gefilterd op prefix van een willekeurige grouping-parameter
        (uit het project profile). group_prefix 'all' = geen filter."""
        prefix = None if (group_prefix or "").lower() == "all" else group_prefix
        return _collect_rooms_with_doors(doc, apartment_filter=prefix, group_param=group_param)

    logger.info("Rooms with doors routes registered successfully")
