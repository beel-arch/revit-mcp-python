# -*- coding: UTF-8 -*-
"""
Areas route
GET /areas/                          - list all areas with their scheme, number, name, area
GET /areas/<scheme_name>             - list areas filtered by Area Scheme name
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger


def register_areas_routes(api):

    @api.route('/areas/', methods=["GET"])
    def get_all_areas(doc, request=None):
        """Return all Area instances with scheme, number, name and area value."""
        return _collect_areas(doc, scheme_filter=None)

    @api.route('/areas/<scheme_name>', methods=["GET"])
    def get_areas_by_scheme(doc, scheme_name):
        """Return areas that belong to the given Area Scheme name."""
        return _collect_areas(doc, scheme_filter=scheme_name)


def _elem_id_int(elem_id):
    """Return integer value of an ElementId as a plain int (IronPython-safe)."""
    try:
        return int(elem_id.IntegerValue)
    except AttributeError:
        return int(elem_id.Value)


def _collect_areas(doc, scheme_filter):
    try:
        # Build a dict of AreaScheme id -> name for quick lookup
        schemes = {}
        for s in DB.FilteredElementCollector(doc).OfClass(DB.AreaScheme):
            schemes[_elem_id_int(s.Id)] = s.Name

        collector = (
            DB.FilteredElementCollector(doc)
            .OfCategory(DB.BuiltInCategory.OST_Areas)
            .WhereElementIsNotElementType()
        )

        results = []
        for area in collector:
            try:
                scheme_name = area.AreaScheme.Name
            except Exception:
                scheme_name = ""

            if scheme_filter and scheme_name.lower() != scheme_filter.lower():
                continue

            try:
                number = area.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or ""
            except Exception:
                number = ""

            try:
                name = area.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or ""
            except Exception:
                name = ""

            try:
                # Internal units are square feet; 1 ft² = 0.092903 m²
                area_m2 = round(area.Area * 0.092903, 2)
            except Exception:
                area_m2 = None

            # Skip unplaced areas
            if area_m2 == 0.0:
                continue

            try:
                level_name = area.Level.Name if area.Level else ""
            except Exception:
                level_name = ""

            results.append({
                "id": _elem_id_int(area.Id),
                "scheme": scheme_name,
                "number": number,
                "name": name,
                "area_m2": area_m2,
                "level": level_name,
            })

        results.sort(key=lambda x: (x["scheme"], x["number"], x["name"]))

        return routes.make_response(data={
            "scheme_filter": scheme_filter or "all",
            "count": len(results),
            "areas": results,
        })

    except Exception as e:
        logger.error("Error in _collect_areas: {}".format(str(e)))
        return routes.make_response(data={"error": str(e)}, status=500)
