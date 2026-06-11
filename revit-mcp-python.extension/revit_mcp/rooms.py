# -*- coding: UTF-8 -*-
"""
Rooms routes
GET  /rooms/                     - list all placed rooms with name, number, area, level,
                                   and the custom BEEL_C_TX_AppartementNummer parameter.
GET  /rooms/parameter_discovery/ - fill-rate + distinct values per tekstparameter op rooms
                                   (discovery voor het project-setup interview).
POST /rooms/overview/            - lean room overview met level/grouping/param-filters.
                                   Body: {"level": "", "group_param": "", "group_prefix": "",
                                          "params": [], "include_unplaced": false}
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from revit_mcp.utils import safe_string
import json
import logging
logger = logging.getLogger(__name__)


def _elem_id_int(elem_id):
    """Return integer value of an ElementId (IronPython / CPython-safe)."""
    try:
        return int(elem_id.IntegerValue)
    except AttributeError:
        return int(elem_id.Value)


def register_rooms_routes(api):

    @api.route('/rooms/debug_params', methods=["GET"])
    def debug_room_params(doc, request=None):
        """Return all parameter names and values for the first placed room — for debugging."""
        try:
            collector = (
                DB.FilteredElementCollector(doc)
                .OfCategory(DB.BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
            )
            for room in collector:
                try:
                    area_m2 = round(room.Area * 0.092903, 2)
                except Exception:
                    area_m2 = 0
                if not area_m2:
                    continue
                params = []
                for p in room.Parameters:
                    try:
                        val = None
                        st = p.StorageType
                        if st == DB.StorageType.String:
                            val = p.AsString()
                        elif st == DB.StorageType.Integer:
                            val = p.AsInteger()
                        elif st == DB.StorageType.Double:
                            val = p.AsValueString() or p.AsDouble()
                        elif st == DB.StorageType.ElementId:
                            eid = p.AsElementId()
                            val = _elem_id_int(eid) if eid else None
                        params.append({"name": p.Definition.Name, "value": val})
                    except Exception:
                        continue
                params.sort(key=lambda x: x["name"])
                try:
                    room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
                except Exception:
                    room_name = "?"
                return routes.make_response(data={
                    "room_id": _elem_id_int(room.Id),
                    "room_name": room_name,
                    "parameters": params,
                })
            return routes.make_response(data={"error": "No placed rooms found"}, status=404)
        except Exception as e:
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route('/rooms/', methods=["GET"])
    def get_all_rooms(doc, request=None):
        """Return all placed Room instances with name, number, area, level
        and the BEEL_C_TX_AppartementNummer custom parameter."""
        try:
            collector = (
                DB.FilteredElementCollector(doc)
                .OfCategory(DB.BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
            )

            results = []
            for room in collector:
                try:
                    # Skip unplaced / zero-area rooms
                    try:
                        area_m2 = round(room.Area * 0.092903, 2)
                    except Exception:
                        area_m2 = None
                    if not area_m2:
                        continue

                    try:
                        name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or ""
                    except Exception:
                        name = ""

                    try:
                        number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or ""
                    except Exception:
                        number = ""

                    try:
                        level_name = room.Level.Name if room.Level else ""
                    except Exception:
                        level_name = ""

                    appartement_nr = None
                    try:
                        p = room.LookupParameter("BEEL_C_TX_AppartementNummer")
                        if p and p.HasValue:
                            appartement_nr = p.AsString()
                    except Exception:
                        pass

                    results.append({
                        "id": _elem_id_int(room.Id),
                        "name": name,
                        "number": number,
                        "area_m2": area_m2,
                        "level": level_name,
                        "appartement_nr": appartement_nr,
                    })
                except Exception:
                    pass

            results.sort(key=lambda x: (x["appartement_nr"] or "", x["name"]))

            return routes.make_response(data={
                "count": len(results),
                "rooms": results,
            })

        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, str(e))
            logger.error("Error in get_all_rooms: {}".format(msg))
            return routes.make_response(data={"error": msg}, status=500)

    @api.route('/rooms/parameter_discovery/', methods=["GET"])
    def discover_room_parameters(doc, request=None):
        """Fill-rate en distinct values per tekstparameter op alle rooms.

        Discovery voor het project-setup interview: welke parameters dragen de
        grouping van dit project? Filtert op fill-rate zodat lege import-ruis
        (honderden lege shared parameters) niet meekomt.
        """
        try:
            MAX_DISTINCT = 200
            MAX_EXAMPLES = 15

            collector = (
                DB.FilteredElementCollector(doc)
                .OfCategory(DB.BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
            )

            total = 0
            placed = 0
            param_stats = {}

            for room in collector:
                total += 1
                try:
                    if room.Area > 0:
                        placed += 1
                except Exception:
                    pass

                for p in room.Parameters:
                    try:
                        if p.StorageType != DB.StorageType.String:
                            continue
                        name = p.Definition.Name
                        stats = param_stats.get(name)
                        if stats is None:
                            stats = {"filled": 0, "values": set()}
                            param_stats[name] = stats
                        val = p.AsString() if p.HasValue else None
                        if val:
                            stats["filled"] += 1
                            if len(stats["values"]) < MAX_DISTINCT:
                                stats["values"].add(safe_string(val))
                    except Exception:
                        continue

            parameters = []
            for name, stats in param_stats.items():
                if not stats["filled"]:
                    continue
                values = sorted(stats["values"])
                parameters.append({
                    "name": safe_string(name),
                    "filled": stats["filled"],
                    "fill_rate": round(float(stats["filled"]) / total, 2) if total else 0,
                    "distinct_count": len(values),
                    "distinct_capped": len(values) >= MAX_DISTINCT,
                    "examples": values[:MAX_EXAMPLES],
                })
            parameters.sort(key=lambda x: (-x["fill_rate"], x["name"]))

            return routes.make_response(data={
                "total_rooms": total,
                "placed_rooms": placed,
                "unplaced_rooms": total - placed,
                "parameters": parameters,
            })

        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, str(e))
            logger.error("Error in discover_room_parameters: {}".format(msg))
            return routes.make_response(data={"error": msg}, status=500)

    @api.route('/rooms/overview/', methods=["POST"])
    def rooms_overview(doc, request):
        """Lean room overview — naam, nummer, area, level + opgevraagde parameters.

        Filters (alle optioneel, toegepast ín Revit):
          level:            exacte levelnaam (case-insensitief)
          group_param:      parameternaam waarvan de waarde als 'group' terugkomt
          group_prefix:     prefix-filter op die waarde
          params:           extra parameternamen om per room terug te geven
          include_unplaced: ook unplaced rooms (area 0) teruggeven
        """
        try:
            data = None
            if request is not None and request.data:
                if isinstance(request.data, str):
                    data = json.loads(request.data)
                else:
                    data = request.data
            data = data or {}

            level_f = (data.get("level") or "").strip()
            group_param = (data.get("group_param") or "").strip()
            group_prefix = (data.get("group_prefix") or "").strip()
            extra_params = [p for p in (data.get("params") or []) if p]
            include_unplaced = bool(data.get("include_unplaced"))

            collector = (
                DB.FilteredElementCollector(doc)
                .OfCategory(DB.BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType()
            )

            results = []
            unplaced_skipped = 0
            for room in collector:
                try:
                    try:
                        area_m2 = round(room.Area * 0.092903, 2)
                    except Exception:
                        area_m2 = 0
                    placed = bool(area_m2)
                    if not placed and not include_unplaced:
                        unplaced_skipped += 1
                        continue

                    try:
                        level_name = safe_string(room.Level.Name) if room.Level else ""
                    except Exception:
                        level_name = ""
                    if level_f and level_name.lower() != level_f.lower():
                        continue

                    group_val = None
                    if group_param:
                        try:
                            p = room.LookupParameter(group_param)
                            if p and p.HasValue:
                                group_val = safe_string(p.AsString())
                        except Exception:
                            pass
                        if group_prefix and not (group_val or "").startswith(group_prefix):
                            continue

                    try:
                        name = safe_string(
                            room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or "")
                    except Exception:
                        name = ""
                    try:
                        number = safe_string(
                            room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or "")
                    except Exception:
                        number = ""

                    entry = {
                        "id": _elem_id_int(room.Id),
                        "name": name,
                        "number": number,
                        "area_m2": area_m2 if placed else None,
                        "level": level_name,
                        "placed": placed,
                    }
                    if group_param:
                        entry["group"] = group_val
                    if extra_params:
                        values = {}
                        for pname in extra_params:
                            val = None
                            try:
                                p = room.LookupParameter(pname)
                                if p and p.HasValue:
                                    st = p.StorageType
                                    if st == DB.StorageType.String:
                                        val = safe_string(p.AsString())
                                    elif st == DB.StorageType.Integer:
                                        val = p.AsInteger()
                                    elif st == DB.StorageType.Double:
                                        val = safe_string(p.AsValueString() or "") or p.AsDouble()
                                    elif st == DB.StorageType.ElementId:
                                        eid = p.AsElementId()
                                        val = _elem_id_int(eid) if eid else None
                            except Exception:
                                pass
                            values[pname] = val
                        entry["params"] = values
                    results.append(entry)
                except Exception:
                    pass

            results.sort(key=lambda x: (x.get("group") or "", x["level"], x["name"]))

            return routes.make_response(data={
                "count": len(results),
                "unplaced_skipped": unplaced_skipped,
                "filters": {
                    "level": level_f,
                    "group_param": group_param,
                    "group_prefix": group_prefix,
                    "params": extra_params,
                    "include_unplaced": include_unplaced,
                },
                "rooms": results,
            })

        except Exception as e:
            msg = "{}: {}".format(type(e).__name__, str(e))
            logger.error("Error in rooms_overview: {}".format(msg))
            return routes.make_response(data={"error": msg}, status=500)
