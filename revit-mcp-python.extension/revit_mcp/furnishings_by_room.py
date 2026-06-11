# -*- coding: UTF-8 -*-
"""
Furnishings by Room — unified route for all furnishing/equipment categories.

Routes:
    GET /furnishings/byroom/                           all categories, all rooms
    GET /furnishings/byroom/cat/<categories>           comma-sep aliases, all rooms
    GET /furnishings/byroom/apt/<apt_filter>           all categories, by apartment prefix
    GET /furnishings/byroom/cat/<categories>/apt/<apt> both filters (leanest)
    GET /furnishings/byroom/groupby/<param>/<prefix>               grouping-parameter
                                                       uit het project profile ('all' = geen filter)
    GET /furnishings/byroom/cat/<categories>/groupby/<param>/<prefix>  beide filters

Category aliases (case-insensitive, comma-separated):
    furniture    kasten, bedden, stoelen, tafels
    systems      systeemmeubilair, werkstations
    casework     inbouwmeubelen, keukens, badkamermeubels
    plumbing     wastafel, douche, ligbad, toilet (Plumbing Fixtures)
    plumbingeq   sanitaire toestellen (Plumbing Equipment)
    specialty    keukenapparaten, postbussen, speciale uitrusting
    lighting     verlichtingsarmaturen (Lighting Fixtures)
    lightingdev  verlichtingstoestellen (Lighting Devices)
    electrical   stopcontacten, schakelaars (Electrical Fixtures)
    electricaleq wasmachine, droogkast, kookfornuis (Electrical Equipment)
    mechanical   radiatoren, ventilatieunits, HVAC
    firealarm    rookmelders, noodknoppen
    all          alle bovenstaande (default)
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from revit_mcp.utils import safe_string, get_family_name_safe, get_element_name_safe
import logging

logger = logging.getLogger(__name__)


def _safe_cat(bic_name):
    try:
        return getattr(DB.BuiltInCategory, bic_name)
    except AttributeError:
        return None


# (alias, BuiltInCategory name, display label)
_CAT_DEFS = [
    ("furniture",    "OST_Furniture",           "Furniture"),
    ("systems",      "OST_FurnitureSystems",    "Furniture Systems"),
    ("casework",     "OST_Casework",            "Casework"),
    ("plumbing",     "OST_PlumbingFixtures",    "Plumbing Fixtures"),
    ("plumbingeq",   "OST_PlumbingEquipment",   "Plumbing Equipment"),
    ("specialty",    "OST_SpecialityEquipment", "Specialty Equipment"),
    ("lighting",     "OST_LightingFixtures",    "Lighting Fixtures"),
    ("lightingdev",  "OST_LightingDevices",     "Lighting Devices"),
    ("electrical",   "OST_ElectricalFixtures",  "Electrical Fixtures"),
    ("electricaleq", "OST_ElectricalEquipment", "Electrical Equipment"),
    ("mechanical",   "OST_MechanicalEquipment", "Mechanical Equipment"),
    ("firealarm",    "OST_FireAlarmDevices",     "Fire Alarm Devices"),
]

# Only keep categories whose BuiltInCategory exists in this Revit version
CATEGORY_MAP = {}
for _alias, _bic, _label in _CAT_DEFS:
    _cat = _safe_cat(_bic)
    if _cat is not None:
        CATEGORY_MAP[_alias] = (_cat, _label)


def _parse_cat_str(cat_str):
    """Return list of (alias, BuiltInCategory) from comma-separated string. 'all'/'' = all."""
    if not cat_str or cat_str.strip().lower() == "all":
        return [(a, v[0]) for a, v in CATEGORY_MAP.items()]
    result = []
    for alias in (a.strip().lower() for a in cat_str.split(",") if a.strip()):
        if alias in CATEGORY_MAP:
            result.append((alias, CATEGORY_MAP[alias][0]))
    return result


def _elem_id_int(elem_id):
    try:
        return int(elem_id.IntegerValue)
    except AttributeError:
        return int(elem_id.Value)


DEFAULT_GROUPING_PARAMETER = "BEEL_C_TX_AppartementNummer"


def _collect_furnishings(doc, cat_str=None, apt_filter=None, group_param=None):
    try:
        group_param = group_param or DEFAULT_GROUPING_PARAMETER
        is_default_param = group_param == DEFAULT_GROUPING_PARAMETER

        phases = list(DB.FilteredElementCollector(doc).OfClass(DB.Phase))
        last_phase = phases[-1] if phases else None

        apt_f = ""
        if apt_filter:
            stripped = apt_filter.strip()
            if stripped.lower() != "all":
                apt_f = stripped

        categories = _parse_cat_str(cat_str)
        if not categories:
            return routes.make_response(
                data={"error": "Geen geldige category-aliassen in '{}'".format(cat_str)},
                status=400,
            )

        rooms = {}  # room_key -> {meta + "items": [...]}

        for alias, bic in categories:
            try:
                elems = (
                    DB.FilteredElementCollector(doc)
                    .OfCategory(bic)
                    .WhereElementIsNotElementType()
                )
            except Exception as e:
                logger.warning("Categorie {} overgeslagen: {}".format(alias, e))
                continue

            for el in elems:
                try:
                    r = el.Room[last_phase] if last_phase else None

                    if r:
                        apt_nr = None
                        try:
                            p = r.LookupParameter(group_param)
                            if p and p.HasValue:
                                apt_nr = safe_string(p.AsString())
                        except Exception:
                            pass

                        if apt_f and not (apt_nr or "").startswith(apt_f):
                            continue

                        room_id = _elem_id_int(r.Id)
                        try:
                            rnum = safe_string(r.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString() or "")
                        except Exception:
                            rnum = ""
                        try:
                            rname = safe_string(r.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or "")
                        except Exception:
                            rname = ""
                        try:
                            level_name = safe_string(r.Level.Name) if r.Level else ""
                        except Exception:
                            level_name = ""
                        key = str(room_id)
                    else:
                        if apt_f:
                            continue  # skip unroomed items when filtering by apartment
                        room_id, rnum, rname, apt_nr, level_name, key = None, "", "", None, "", "No Room"

                    if key not in rooms:
                        rooms[key] = {
                            "room_id": room_id,
                            "room_number": rnum,
                            "room_name": rname,
                            "group": apt_nr,
                            "appartement_nr": apt_nr if is_default_param else None,
                            "level": level_name,
                            "items": [],
                        }

                    sym = doc.GetElement(el.GetTypeId())
                    family_name = safe_string(get_family_name_safe(sym)) if sym else ""
                    type_name = safe_string(get_element_name_safe(sym)) if sym else ""

                    try:
                        mark_p = el.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                        mark = safe_string(mark_p.AsString() or "") if mark_p else ""
                    except Exception:
                        mark = ""

                    rooms[key]["items"].append({
                        "element_id": _elem_id_int(el.Id),
                        "category": alias,
                        "family": family_name,
                        "type": type_name,
                        "mark": mark,
                    })

                except Exception:
                    pass

        out = [rooms[k] for k in sorted(rooms.keys())]
        used_aliases = [a for a, _ in categories]

        return routes.make_response(data={
            "filters": {
                "categories": ",".join(used_aliases),
                "apartment": apt_f or "all",
                "group_parameter": group_param,
            },
            "room_count": len(out),
            "item_count": sum(len(r["items"]) for r in out),
            "rooms": out,
        })

    except Exception as e:
        msg = "{}: {}".format(type(e).__name__, str(e))
        logger.error("Error in _collect_furnishings: {}".format(msg))
        return routes.make_response(data={"error": msg}, status=500)


def register_furnishings_by_room_routes(api):

    @api.route('/furnishings/byroom/', methods=["GET"])
    def get_all_furnishings(doc, request=None):
        """All furnishing categories, all rooms. Avoid without filter — large payload."""
        return _collect_furnishings(doc)

    @api.route('/furnishings/byroom/cat/<categories>', methods=["GET"])
    def get_furnishings_by_cat(doc, categories):
        """Comma-separated category aliases, all apartments."""
        return _collect_furnishings(doc, cat_str=categories)

    @api.route('/furnishings/byroom/apt/<apt_filter>', methods=["GET"])
    def get_furnishings_by_apt(doc, apt_filter):
        """All categories, filter by apartment prefix."""
        return _collect_furnishings(doc, apt_filter=apt_filter)

    @api.route('/furnishings/byroom/cat/<categories>/apt/<apt_filter>', methods=["GET"])
    def get_furnishings_by_cat_and_apt(doc, categories, apt_filter):
        """Specific categories + apartment filter — leanest query."""
        return _collect_furnishings(doc, cat_str=categories, apt_filter=apt_filter)

    @api.route('/furnishings/byroom/groupby/<group_param>/<group_prefix>', methods=["GET"])
    def get_furnishings_by_group(doc, group_param, group_prefix):
        """All categories, gefilterd op prefix van een willekeurige grouping-parameter
        (project profile). group_prefix 'all' = geen filter."""
        return _collect_furnishings(doc, apt_filter=group_prefix, group_param=group_param)

    @api.route('/furnishings/byroom/cat/<categories>/groupby/<group_param>/<group_prefix>', methods=["GET"])
    def get_furnishings_by_cat_and_group(doc, categories, group_param, group_prefix):
        """Categories + grouping-parameter filter — leanest query op niet-KSS projecten."""
        return _collect_furnishings(doc, cat_str=categories, apt_filter=group_prefix,
                                    group_param=group_param)
