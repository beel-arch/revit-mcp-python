# -*- coding: UTF-8 -*-
"""
Tag override routes
GET  /room_tags/<room_id>  - all RoomTag elements that tag a given room
POST /override_graphics    - apply (or clear) a color override on an element in a view
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger
import json
import System


NAMED_COLORS = {
    "red":    (255, 0,   0),
    "green":  (0,   128, 0),
    "blue":   (0,   0,   255),
    "yellow": (255, 255, 0),
    "orange": (255, 128, 0),
    "purple": (128, 0,   128),
    "white":  (255, 255, 255),
    "black":  (0,   0,   0),
}


def _elem_id_int(elem_id):
    try:
        return int(elem_id.IntegerValue)
    except AttributeError:
        return int(elem_id.Value)


def _make_elem_id(int_val):
    try:
        return DB.ElementId(System.Int64(int(int_val)))
    except TypeError:
        return DB.ElementId(System.Int32(int(int_val)))


def register_tag_override_routes(api):

    @api.route('/room_tags/<room_id>', methods=["GET"])
    def get_room_tags(doc, room_id):
        """Return all RoomTag elements that tag the given room ID, with their view info."""
        try:
            target_id = int(room_id)
            collector = (
                DB.FilteredElementCollector(doc)
                .OfCategory(DB.BuiltInCategory.OST_RoomTags)
                .WhereElementIsNotElementType()
                .ToElements()
            )
            results = []
            for tag in collector:
                try:
                    room = tag.Room
                    if room is None:
                        continue
                    if _elem_id_int(room.Id) != target_id:
                        continue
                    view_id = _elem_id_int(tag.OwnerViewId)
                    view_el = doc.GetElement(tag.OwnerViewId)
                    view_name = view_el.Name if view_el else ""
                    results.append({
                        "tag_id": _elem_id_int(tag.Id),
                        "view_id": view_id,
                        "view_name": view_name,
                    })
                except Exception:
                    continue
            return routes.make_response(data={"room_id": target_id, "tags": results})
        except Exception as e:
            logger.error("Error in get_room_tags: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route('/override_graphics', methods=["POST"])
    def override_graphics(doc, request):
        """
        Apply or clear a graphic color override on an element in a view.

        Body: {
            "view_id":    <int>,
            "element_id": <int>,
            "color":      "red" | [r, g, b] | null   (null = clear overrides)
        }
        """
        try:
            data = request.data
            if isinstance(data, str):
                data = json.loads(data)

            view_id    = int(data["view_id"])
            element_id = int(data["element_id"])
            color_val  = data.get("color")

            view = doc.GetElement(_make_elem_id(view_id))
            if view is None:
                return routes.make_response(
                    data={"error": "View not found: {}".format(view_id)}, status=404)

            elem = doc.GetElement(_make_elem_id(element_id))
            if elem is None:
                return routes.make_response(
                    data={"error": "Element not found: {}".format(element_id)}, status=404)

            ogs = DB.OverrideGraphicSettings()

            if color_val is not None:
                if isinstance(color_val, str):
                    rgb = NAMED_COLORS.get(color_val.lower())
                    if rgb is None:
                        return routes.make_response(
                            data={"error": "Unknown color '{}'. Use: {}".format(
                                color_val, list(NAMED_COLORS.keys()))},
                            status=400)
                else:
                    rgb = (int(color_val[0]), int(color_val[1]), int(color_val[2]))

                revit_color = DB.Color(rgb[0], rgb[1], rgb[2])
                ogs.SetProjectionLineColor(revit_color)

            t = DB.Transaction(doc, "MCP Override Graphics")
            t.Start()
            try:
                view.SetElementOverrides(_make_elem_id(element_id), ogs)
                t.Commit()
            except Exception as tx_err:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise tx_err

            action = "cleared" if color_val is None else str(color_val)
            return routes.make_response(data={
                "status": "success",
                "element_id": element_id,
                "view_id": view_id,
                "color": action,
            })

        except Exception as e:
            logger.error("Error in override_graphics: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    logger.info("Tag override routes registered successfully")
