# -*- coding: UTF-8 -*-
from pyrevit import routes, DB
import logging, re

logger = logging.getLogger(__name__)

import json

def _extract_data(request):
    """Haal JSON body robuust uit diverse request-varianten."""
    if request is None:
        return {}

    # Flask-achtig
    try:
        j = request.get_json()
        if j is not None:
            return j
    except Exception:
        pass

    # Eigenschap .json (soms een dict, soms property)
    try:
        j = request.json
        if j is not None:
            return j
    except Exception:
        pass

    # .data kan bytes/str/dict zijn
    try:
        d = request.data
        if isinstance(d, (bytes, str)):
            return json.loads(d)
        if isinstance(d, dict):
            return d
    except Exception:
        pass

    # In sommige setups is het al een dict
    if isinstance(request, dict):
        return request

    # Fallback: .body
    try:
        b = request.body
        if isinstance(b, (bytes, str)):
            return json.loads(b)
    except Exception:
        pass

    return {}



# -------------------------
# Helpers
# -------------------------
def _iter_rooms(doc):
    return (DB.FilteredElementCollector(doc)
            .OfCategory(DB.BuiltInCategory.OST_Rooms)
            .WhereElementIsNotElementType())

def _room_name(room):
    try:
        p = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME)
        return p.AsString() if p else ""
    except:
        return ""

def _room_number(room):
    try:
        p = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER)
        return p.AsString() if p else ""
    except:
        return ""

def _match_text(text, pattern, mode="equals", case_sensitive=False):
    if text is None:
        text = ""
    if pattern is None:
        return False
    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()
    if mode == "equals":
        return text == pattern
    elif mode == "contains":
        return pattern in text
    elif mode == "startswith":
        return text.startswith(pattern)
    elif mode == "endswith":
        return text.endswith(pattern)
    elif mode == "regex":
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.search(pattern, text, flags) is not None
    else:
        return False

def _select_rooms(doc, selector):
    """
    selector ondersteunt:
      - room_id (int) of room_ids (lijst)
      - number (str) / numbers (lijst)
      - name (str)   / names  (lijst)
      - match: 'equals'|'contains'|'startswith'|'endswith'|'regex' (default 'equals')
      - case_sensitive: bool (default False)
      - first_only: bool (default False) => enkel eerste match teruggeven
    """
    if not selector:
        return []

    match = selector.get("match", "equals")
    case_sensitive = bool(selector.get("case_sensitive", False))
    first_only = bool(selector.get("first_only", False))

    # 1) Via ElementId(s)
    if "room_id" in selector or "room_ids" in selector:
        ids = []
        if "room_id" in selector:
            ids.append(int(selector["room_id"]))
        if "room_ids" in selector:
            ids.extend(int(x) for x in selector["room_ids"])
        out = []
        for rid in ids:
            el = doc.GetElement(DB.ElementId(rid))
            if el and el.Category and el.Category.Id.IntegerValue == int(DB.BuiltInCategory.OST_Rooms):
                out.append(el)
                if first_only:
                    break
        return out

    # 2) Via number(s) en/of name(s)
    number = selector.get("number")
    numbers = selector.get("numbers") or ([number] if number else [])
    name = selector.get("name")
    names = selector.get("names") or ([name] if name else [])

    if not numbers and not names:
        return []

    results = []
    for r in _iter_rooms(doc):
        rnum = _room_number(r)
        rname = _room_name(r)

        match_num = (any(_match_text(rnum, n, match, case_sensitive) for n in numbers) if numbers else True)
        match_name = (any(_match_text(rname, n, match, case_sensitive) for n in names) if names else True)

        if match_num and match_name:
            results.append(r)
            if first_only:
                break
    return results

def _get_param_value_for_report(p):
    try:
        st = p.StorageType
        if st == DB.StorageType.String:
            return p.AsString()
        elif st == DB.StorageType.Integer:
            return p.AsInteger()
        elif st == DB.StorageType.Double:
            return p.AsDouble()
        elif st == DB.StorageType.ElementId:
            eid = p.AsElementId()
            return eid.IntegerValue if eid else None
    except:
        pass
    return None

def _set_param_value(param, value):
    stype = param.StorageType
    if stype == DB.StorageType.String:
        param.Set("" if value is None else str(value))
        return

    if stype == DB.StorageType.Integer:
        if isinstance(value, bool):
            param.Set(1 if value else 0)
        else:
            param.Set(int(value))
        return

    if stype == DB.StorageType.Double:
        # Revit 2021+: GetUnitTypeId() => UnitUtils.ConvertToInternalUnits(value, unitTypeId)
        try:
            unit_type_id = param.GetUnitTypeId()  # type: Autodesk.Revit.DB.ForgeTypeId
            dbl = float(value)
            dbl_internal = DB.UnitUtils.ConvertToInternalUnits(dbl, unit_type_id)
            param.Set(dbl_internal)
            return
        except Exception:
            # Legacy fallback
            try:
                dut = param.DisplayUnitType  # kan ontbreken in recente Revit versies
                dbl_internal = DB.UnitUtils.ConvertToInternalUnits(float(value), dut)
                param.Set(dbl_internal)
                return
            except Exception:
                # Als alles faalt: zet raw double (feet)
                param.Set(float(value))
                return

    if stype == DB.StorageType.ElementId:
        param.Set(DB.ElementId(int(value)))
        return

    raise ValueError("Unsupported parameter storage type")


# -------------------------
# Route
# -------------------------
def register_set_room_parameter_route(api):
    @api.route('/room/setparameter/', methods=['POST'])
    def set_room_parameter(doc, request):
        """
        Zet een parameter op één of meerdere Rooms, met selectie op id, name, number.
        - Matching-modi: equals|contains|startswith|endswith|regex (default: equals, case-insensitive)
        - Dry run mogelijk
        - Rapporteert per kamer id/number/name + oude/nieuwe waarde of fout

        JSON body (voorbeelden):

        1) Op naam 'Woonkamer' (case-insensitive, equals):
        {
          "parameter": "Comments",
          "value": "hello world",
          "selector": { "name": "Woonkamer" }
        }

        2) Alias (kort):
        {
          "room_name": "Woonkamer",
          "parameter": "Comments",
          "value": "hello world"
        }

        3) Bevat 'slaap' in de naam:
        {
          "parameter": "Comments",
          "value": "Nachtzone",
          "selector": { "name": "slaap", "match": "contains" }
        }

        4) Dry run (geen wijzigingen wegschrijven):
        {
          "parameter": "Comments",
          "value": "x",
          "selector": { "name": "Woonkamer" },
          "dry_run": true
        }

        5) Enkel eerste match (first_only):
        {
          "parameter": "Comments",
          "value": "x",
          "selector": { "name": "Woonkamer", "first_only": true }
        }
        """
        try:
            data = _extract_data(request)

            param_name = data.get("parameter")
            value = data.get("value")
            dry_run = bool(data.get("dry_run", False))

            # Selector + aliases
            selector = data.get("selector", {})
            if "room_id" in data:
                selector["room_id"] = data["room_id"]
            if "room_ids" in data:
                selector["room_ids"] = data["room_ids"]
            if "room_name" in data:
                selector["name"] = data["room_name"]
            if "room_number" in data:
                selector["number"] = data["room_number"]

            if not param_name:
                return {"status": "error", "message": "parameter is verplicht"}, 400

            targets = _select_rooms(doc, selector)
            if not targets:
                return {"status": "ok", "updated": 0, "rooms": [], "message": "Geen kamers gevonden voor de selector."}

            # Dry run: enkel rapporteren
            if dry_run:
                results = []
                for r in targets:
                    p = r.LookupParameter(param_name)
                    old_val = _get_param_value_for_report(p) if p else None
                    results.append({
                        "id": r.Id.IntegerValue,
                        "number": _room_number(r),
                        "name": _room_name(r),
                        "old_value": old_val,
                        "new_value": value if p and not p.IsReadOnly else None,
                        "error": None if (p and not p.IsReadOnly) else "Parameter niet gevonden of read-only"
                    })
                return {"status": "ok", "updated": 0, "rooms": results, "dry_run": True}

            # Echte update binnen transaction
            results = []
            updated = 0
            t = DB.Transaction(doc, "MCP: Set Room Parameter '{}'".format(param_name))
            t.Start()
            try:
                for r in targets:
                    p = r.LookupParameter(param_name)
                    if not p or p.IsReadOnly:
                        results.append({
                            "id": r.Id.IntegerValue,
                            "number": _room_number(r),
                            "name": _room_name(r),
                            "old_value": None,
                            "new_value": None,
                            "error": "Parameter niet gevonden of read-only"
                        })
                        continue

                    old_val = _get_param_value_for_report(p)
                    try:
                        _set_param_value(p, value)
                        updated += 1
                        results.append({
                            "id": r.Id.IntegerValue,
                            "number": _room_number(r),
                            "name": _room_name(r),
                            "old_value": old_val,
                            "new_value": value
                        })
                    except Exception as ex:
                        results.append({
                            "id": r.Id.IntegerValue,
                            "number": _room_number(r),
                            "name": _room_name(r),
                            "old_value": old_val,
                            "new_value": None,
                            "error": str(ex)
                        })
                t.Commit()
            except Exception as ex:
                logger.exception("Transaction failed")
                try:
                    t.RollBack()
                except:
                    pass
                return {"status": "error", "message": "Transaction failed: {}".format(str(ex))}, 500

            return {"status": "ok", "updated": updated, "rooms": results}

        except Exception as e:
            logger.exception("Error setting room parameter")
            return {"status": "error", "message": str(e)}, 500
