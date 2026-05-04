# -*- coding: UTF-8 -*-
"""
Rooms route
GET /rooms/  - list all placed rooms with name, number, area, level,
               and the custom BEEL_C_TX_AppartementNummer parameter.
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger


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
