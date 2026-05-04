# -*- coding: UTF-8 -*-
from pyrevit import routes, DB


def _elem_id_int(elem_id):
    try:
        return int(elem_id.IntegerValue)
    except AttributeError:
        return int(elem_id.Value)


def register_plumbing_by_room_routes(api):
    @api.route('/plumbing/byroom/', methods=["GET"])
    def plumbing_by_room(doc, request=None):
        """Return all plumbing fixtures with the room they are placed in."""
        phases = list(DB.FilteredElementCollector(doc).OfClass(DB.Phase))
        last_phase = phases[-1] if phases else None

        elems = (DB.FilteredElementCollector(doc)
                 .OfCategory(DB.BuiltInCategory.OST_PlumbingFixtures)
                 .WhereElementIsNotElementType())

        out = []
        for el in elems:
            sym = doc.GetElement(el.GetTypeId())
            family_name = sym.Family.Name if getattr(sym, "Family", None) else ""
            type_name = sym.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            type_name = type_name.AsString() if type_name else ""

            r = el.Room[last_phase] if last_phase else None
            if r:
                room_id = _elem_id_int(r.Id)
                try:
                    room_number = r.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or ""
                except Exception:
                    room_number = ""
                try:
                    room_name = r.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or ""
                except Exception:
                    room_name = ""
            else:
                room_id = None
                room_number = ""
                room_name = ""

            out.append({
                "room_id": room_id,
                "room_number": room_number,
                "room_name": room_name,
                "family": family_name,
                "type": type_name,
            })

        return routes.make_response(data={"count": len(out), "fixtures": out})
