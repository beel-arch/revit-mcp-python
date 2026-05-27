# -*- coding: UTF-8 -*-
"""
Element override routes
GET  /room_tags/<room_id>  - all RoomTag elements that tag a given room
POST /override_graphics    - apply (or clear) a color override on any element in a view
POST /element/write_param  - write Mark or Comments to any element
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
import logging
import json
import System
from utils import safe_string
logger = logging.getLogger(__name__)


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


def _get_solid_fill_id(doc):
    """Return the ElementId of the solid fill pattern."""
    # Try IsSolidFill property
    try:
        for pat in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
            try:
                fp = pat.GetFillPattern()
                if fp.IsSolidFill:
                    return pat.Id
            except Exception:
                continue
    except Exception:
        pass
    # Fallback: look by common solid fill names
    solid_names = {"<solid fill>", "solid fill", "massief", "solid", "effen"}
    try:
        for pat in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
            try:
                name = (pat.Name or "").strip().lower()
                if name in solid_names:
                    return pat.Id
            except Exception:
                continue
    except Exception:
        pass
    # Last resort: pick the first drafting fill pattern (usually solid)
    try:
        for pat in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
            try:
                fp = pat.GetFillPattern()
                if str(fp.Target) == "Drafting":
                    return pat.Id
            except Exception:
                continue
    except Exception:
        pass
    return None


def _list_fill_patterns(doc):
    """Return all fill pattern names and IsSolidFill — for debugging."""
    result = []
    try:
        for pat in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
            try:
                fp = pat.GetFillPattern()
                try:
                    is_solid = bool(fp.IsSolidFill)
                except Exception:
                    is_solid = None
                try:
                    target = str(fp.Target)
                except Exception:
                    target = "?"
                try:
                    pid = int(pat.Id.IntegerValue)
                except AttributeError:
                    pid = int(pat.Id.Value)
                result.append({
                    "id": pid,
                    "name": safe_string(pat.Name or ""),
                    "is_solid": is_solid,
                    "target": target,
                })
            except Exception:
                continue
    except Exception:
        pass
    return result


def register_element_override_routes(api):

    @api.route('/debug/fill_patterns', methods=["GET"])
    def debug_fill_patterns(doc):
        """List all fill patterns in the model — for diagnosing solid fill issues."""
        patterns = _list_fill_patterns(doc)
        return routes.make_response(data={"count": len(patterns), "patterns": patterns})

    @api.route('/active_view_id/', methods=["GET"])
    def get_active_view_id(uidoc):
        """Return the element ID and name of the currently active view."""
        try:
            view = uidoc.ActiveView
            if view is None:
                return routes.make_response(
                    data={"error": "No active view"}, status=404)
            try:
                vid = int(view.Id.IntegerValue)
            except AttributeError:
                vid = int(view.Id.Value)
            return routes.make_response(data={
                "view_id": vid,
                "view_name": view.Name,
                "view_type": str(view.ViewType),
            })
        except Exception as e:
            return routes.make_response(data={"error": str(e)}, status=500)

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
        Apply or clear a graphic color override on any element in a view.

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
                ogs.SetCutLineColor(revit_color)
                ogs.SetSurfaceForegroundPatternColor(revit_color)
                ogs.SetCutForegroundPatternColor(revit_color)
                ogs.SetSurfaceBackgroundPatternColor(revit_color)
                ogs.SetCutBackgroundPatternColor(revit_color)
                solid_fill_id = _get_solid_fill_id(doc)
                if solid_fill_id is not None:
                    ogs.SetSurfaceForegroundPatternId(solid_fill_id)
                    ogs.SetCutForegroundPatternId(solid_fill_id)
                    ogs.SetSurfaceBackgroundPatternId(solid_fill_id)
                    ogs.SetCutBackgroundPatternId(solid_fill_id)

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

    @api.route('/element/write_param', methods=["POST"])
    def write_element_param(doc, request):
        """
        Write a value to the Mark or Comments parameter of any element.

        Body: {
            "element_id": <int>,
            "param":      "mark" | "comments",
            "value":      <string>
        }
        """
        try:
            data = request.data
            if isinstance(data, str):
                data = json.loads(data)

            element_id = int(data["element_id"])
            param_key  = data.get("param", "").lower().strip()
            value      = data.get("value", "")

            if param_key not in ("mark", "comments"):
                return routes.make_response(
                    data={"error": "param must be 'mark' or 'comments'"}, status=400)

            elem = doc.GetElement(_make_elem_id(element_id))
            if elem is None:
                return routes.make_response(
                    data={"error": "Element not found: {}".format(element_id)}, status=404)

            bip = (DB.BuiltInParameter.ALL_MODEL_MARK
                   if param_key == "mark"
                   else DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)

            param = elem.get_Parameter(bip)
            if param is None or param.IsReadOnly:
                return routes.make_response(
                    data={"error": "Parameter '{}' not writable on element {}".format(
                        param_key, element_id)}, status=400)

            t = DB.Transaction(doc, "MCP Write Parameter")
            t.Start()
            try:
                param.Set(value)
                t.Commit()
            except Exception as tx_err:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise tx_err

            return routes.make_response(data={
                "status": "success",
                "element_id": element_id,
                "param": param_key,
                "value": value,
            })

        except Exception as e:
            logger.error("Error in write_element_param: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route('/element/write_param_by_name', methods=["POST"])
    def write_element_param_by_name(doc, request):
        """
        Write any Revit parameter by its exact name (LookupParameter).

        Body: {
            "element_id": <int>,
            "param_name": <string>,   e.g. "BEEL_C_TX_AppartementNummer"
            "value":      <string>
        }
        """
        try:
            data = request.data
            if isinstance(data, str):
                data = json.loads(data)

            element_id = int(data["element_id"])
            param_name = str(data.get("param_name", "")).strip()
            value      = str(data.get("value", ""))

            if not param_name:
                return routes.make_response(
                    data={"error": "param_name is required"}, status=400)

            elem = doc.GetElement(_make_elem_id(element_id))
            if elem is None:
                return routes.make_response(
                    data={"error": "Element not found: {}".format(element_id)}, status=404)

            param = elem.LookupParameter(param_name)
            if param is None:
                return routes.make_response(
                    data={"error": "Parameter '{}' not found on element {}".format(
                        param_name, element_id)}, status=404)
            if param.IsReadOnly:
                return routes.make_response(
                    data={"error": "Parameter '{}' is read-only".format(param_name)}, status=400)

            t = DB.Transaction(doc, "MCP Write Parameter By Name")
            t.Start()
            try:
                param.Set(value)
                t.Commit()
            except Exception as tx_err:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise tx_err

            return routes.make_response(data={
                "status": "success",
                "element_id": element_id,
                "param_name": param_name,
                "value": value,
            })

        except Exception as e:
            logger.error("Error in write_element_param_by_name: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route('/element/write_params_bulk', methods=["POST"])
    def write_element_params_bulk(doc, request):
        """
        Write Mark or Comments to multiple elements in one transaction.

        Body: {
            "writes": [
                { "element_id": <int>, "param": "mark"|"comments", "value": <string> },
                ...
            ]
        }

        Returns per-element results and an overall summary.
        All writes happen in a single transaction — if one fails the rest still proceed
        (individual errors are captured per entry).
        """
        try:
            data = request.data
            if isinstance(data, str):
                data = json.loads(data)

            writes = data.get("writes", [])
            if not writes:
                return routes.make_response(
                    data={"error": "No writes provided"}, status=400)

            BIP_MAP = {
                "mark":     DB.BuiltInParameter.ALL_MODEL_MARK,
                "comments": DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS,
            }

            results = []
            t = DB.Transaction(doc, "MCP Bulk Write Parameters")
            t.Start()
            try:
                for entry in writes:
                    eid        = int(entry["element_id"])
                    value      = str(entry.get("value", ""))
                    pkey       = str(entry.get("param", "")).lower().strip()
                    param_name = str(entry.get("param_name", "")).strip()

                    elem = doc.GetElement(_make_elem_id(eid))
                    if elem is None:
                        results.append({"element_id": eid, "status": "error",
                                        "error": "element not found"})
                        continue

                    # Resolve parameter: named BIP (mark/comments) or free name
                    if param_name:
                        param = elem.LookupParameter(param_name)
                        label = param_name
                    elif pkey in BIP_MAP:
                        param = elem.get_Parameter(BIP_MAP[pkey])
                        label = pkey
                    else:
                        results.append({"element_id": eid, "status": "error",
                                        "error": "provide 'param' (mark/comments) or 'param_name'"})
                        continue

                    if param is None or param.IsReadOnly:
                        results.append({"element_id": eid, "status": "error",
                                        "error": "param '{}' not writable".format(label)})
                        continue

                    try:
                        param.Set(value)
                        results.append({"element_id": eid, "status": "ok",
                                        "param": label, "value": value})
                    except Exception as we:
                        results.append({"element_id": eid, "status": "error",
                                        "error": str(we)})

                t.Commit()
            except Exception as tx_err:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise tx_err

            ok_count  = sum(1 for r in results if r["status"] == "ok")
            err_count = len(results) - ok_count
            return routes.make_response(data={
                "status": "success",
                "written": ok_count,
                "errors": err_count,
                "results": results,
            })

        except Exception as e:
            logger.error("Error in write_element_params_bulk: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route('/override_graphics_bulk', methods=["POST"])
    def override_graphics_bulk(doc, request):
        """
        Apply (or clear) color overrides on multiple elements across multiple views
        in a single Revit transaction.

        Body: {
            "overrides": [
                { "view_id": <int>, "element_id": <int>, "color": "red"|[r,g,b]|null },
                ...
            ]
        }
        Returns per-entry results and a summary.
        """
        try:
            data = request.data
            if isinstance(data, str):
                data = json.loads(data)

            overrides = data.get("overrides", [])
            if not overrides:
                return routes.make_response(
                    data={"error": "No overrides provided"}, status=400)

            solid_fill_id = _get_solid_fill_id(doc)

            results = []
            t = DB.Transaction(doc, "MCP Bulk Override Graphics")
            t.Start()
            try:
                for entry in overrides:
                    view_id    = int(entry["view_id"])
                    element_id = int(entry["element_id"])
                    color_val  = entry.get("color")

                    view = doc.GetElement(_make_elem_id(view_id))
                    if view is None:
                        results.append({"view_id": view_id, "element_id": element_id,
                                        "status": "error", "error": "view not found"})
                        continue

                    elem = doc.GetElement(_make_elem_id(element_id))
                    if elem is None:
                        results.append({"view_id": view_id, "element_id": element_id,
                                        "status": "error", "error": "element not found"})
                        continue

                    ogs = DB.OverrideGraphicSettings()
                    if color_val is not None:
                        if isinstance(color_val, str):
                            rgb = NAMED_COLORS.get(color_val.lower())
                            if rgb is None:
                                results.append({"view_id": view_id, "element_id": element_id,
                                                "status": "error",
                                                "error": "unknown color '{}'".format(color_val)})
                                continue
                        else:
                            rgb = (int(color_val[0]), int(color_val[1]), int(color_val[2]))

                        revit_color = DB.Color(rgb[0], rgb[1], rgb[2])
                        ogs.SetProjectionLineColor(revit_color)
                        ogs.SetCutLineColor(revit_color)
                        ogs.SetSurfaceForegroundPatternColor(revit_color)
                        ogs.SetCutForegroundPatternColor(revit_color)
                        ogs.SetSurfaceBackgroundPatternColor(revit_color)
                        ogs.SetCutBackgroundPatternColor(revit_color)
                        if solid_fill_id is not None:
                            ogs.SetSurfaceForegroundPatternId(solid_fill_id)
                            ogs.SetCutForegroundPatternId(solid_fill_id)
                            ogs.SetSurfaceBackgroundPatternId(solid_fill_id)
                            ogs.SetCutBackgroundPatternId(solid_fill_id)

                    try:
                        view.SetElementOverrides(_make_elem_id(element_id), ogs)
                        results.append({"view_id": view_id, "element_id": element_id,
                                        "status": "ok",
                                        "color": "cleared" if color_val is None else str(color_val)})
                    except Exception as oe:
                        results.append({"view_id": view_id, "element_id": element_id,
                                        "status": "error", "error": str(oe)})

                t.Commit()
            except Exception as tx_err:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise tx_err

            ok_count  = sum(1 for r in results if r["status"] == "ok")
            err_count = len(results) - ok_count
            return routes.make_response(data={
                "status": "success",
                "applied": ok_count,
                "errors": err_count,
                "results": results,
            })

        except Exception as e:
            logger.error("Error in override_graphics_bulk: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route('/override_graphics/reset_view/<view_id>', methods=["POST"])
    def reset_view_overrides(doc, view_id):
        """Remove all graphic overrides from every element in the given view."""
        try:
            vid = int(view_id)
            view = doc.GetElement(_make_elem_id(vid))
            if view is None:
                return routes.make_response(
                    data={"error": "View not found: {}".format(vid)}, status=404)

            collector = (
                DB.FilteredElementCollector(doc, _make_elem_id(vid))
                .WhereElementIsNotElementType()
                .ToElements()
            )

            empty_ogs = DB.OverrideGraphicSettings()
            t = DB.Transaction(doc, "MCP Reset View Overrides")
            t.Start()
            try:
                count = 0
                for elem in collector:
                    try:
                        view.SetElementOverrides(elem.Id, empty_ogs)
                        count += 1
                    except Exception:
                        continue
                t.Commit()
            except Exception as tx_err:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise tx_err

            return routes.make_response(data={
                "status": "success",
                "view_id": vid,
                "elements_reset": count,
            })

        except Exception as e:
            logger.error("Error in reset_view_overrides: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    logger.info("Element override routes registered successfully")
