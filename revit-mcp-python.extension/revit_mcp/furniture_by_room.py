# -*- coding: UTF-8 -*-
from pyrevit import routes, DB

def register_furniture_by_room_routes(api):
    @api.route('/furniture/byroom/', methods=["GET"])
    def furniture_by_room(doc, request=None):
        # 1) Laatste phase
        phases = list(DB.FilteredElementCollector(doc).OfClass(DB.Phase))
        last_phase = phases[-1] if phases else None

        # 2) Alle Furniture instances
        elems = (DB.FilteredElementCollector(doc)
                 .OfCategory(DB.BuiltInCategory.OST_Furniture)
                 .WhereElementIsNotElementType())

        # 3) Groeperen per Room
        rooms = {}  # key -> {"RoomNumber":..,"RoomName":..,"Furniture":[...]}
        for el in elems:
            # type/family/mark
            sym = doc.GetElement(el.GetTypeId())
            type_name = sym.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            type_name = type_name.AsString() if type_name else ""
            family_name = sym.Family.Name if getattr(sym, "Family", None) else ""
            mark = (el.LookupParameter("Mark").AsString()
                    if el.LookupParameter("Mark") else "")

            # Room via laatste phase (simpel)
            r = el.Room[last_phase] if last_phase else None

            # Room key + metadata
            if r:
                rnum = r.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() if r.LookupParameter("Number") or r.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER) else ""
                rname = r.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() if r.LookupParameter("Name") or r.get_Parameter(DB.BuiltInParameter.ROOM_NAME) else ""
                key = "{} - {}".format(rnum, rname) if (rnum or rname) else "No Room"
            else:
                rnum, rname, key = "", "", "No Room"

            if key not in rooms:
                rooms[key] = {"RoomNumber": rnum, "RoomName": rname, "Furniture": []}

            rooms[key]["Furniture"].append({
                "ElementId": el.Id.IntegerValue,
                "Family": family_name,
                "Type": type_name,
                "Mark": mark
            })

        # 4) Maak een nette lijst (ipv dict) voor stabiele volgorde
        out = []
        for key in sorted(rooms.keys()):
            out.append(rooms[key])

        return routes.make_response(data=out)
