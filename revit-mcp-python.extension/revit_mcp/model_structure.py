# -*- coding: UTF-8 -*-
"""
Lightweight model structure discovery endpoints.
GET /model_structure/                    - overview, grouping op de KSS-default parameter
GET /model_structure/groupby/<param>     - zelfde overview, grouping op een willekeurige
                                           room-parameter (uit het project profile)
Returns identifiers (grouping values, room names, levels, area schemes, view counts,
family category counts) without any deep parameter lookups.
"""

from pyrevit import routes, DB
from revit_mcp.utils import safe_string

DEFAULT_GROUPING_PARAMETER = "BEEL_C_TX_AppartementNummer"


def _collect_structure(doc, group_param):
    """Structuuroverzicht van het model, met grouping-waarden uit group_param."""

    # --- Levels ---
    levels = []
    for lvl in (DB.FilteredElementCollector(doc)
                .OfClass(DB.Level)
                .WhereElementIsNotElementType()):
        try:
            levels.append({
                "name": safe_string(lvl.Name),
                "elevation_m": round(lvl.Elevation * 0.3048, 2),
            })
        except Exception:
            pass
    levels.sort(key=lambda x: x["elevation_m"])

    # --- Rooms: grouping values + unique room name variants + placement ---
    grouping_values = set()
    room_name_variants = set()
    total_rooms = 0
    placed_rooms = 0
    for room in (DB.FilteredElementCollector(doc)
                 .OfCategory(DB.BuiltInCategory.OST_Rooms)
                 .WhereElementIsNotElementType()):
        try:
            total_rooms += 1
            try:
                if room.Area > 0:
                    placed_rooms += 1
            except Exception:
                pass
            name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or ""
            if name:
                room_name_variants.add(safe_string(name))
            p = room.LookupParameter(group_param)
            if p and p.HasValue:
                val = p.AsString()
                if val:
                    grouping_values.add(safe_string(val))
        except Exception:
            pass

    # --- Area schemes ---
    area_schemes = []
    try:
        for scheme in (DB.FilteredElementCollector(doc).OfClass(DB.AreaScheme)):
            try:
                area_schemes.append(safe_string(scheme.Name))
            except Exception:
                pass
    except Exception:
        pass

    # --- Views: count by type ---
    view_counts = {}
    for v in (DB.FilteredElementCollector(doc)
              .OfClass(DB.View)
              .WhereElementIsNotElementType()):
        try:
            if v.IsTemplate:
                continue
            vt = str(v.ViewType)
            view_counts[vt] = view_counts.get(vt, 0) + 1
        except Exception:
            pass

    # --- Families: count by category ---
    family_categories = {}
    for sym in (DB.FilteredElementCollector(doc)
                .OfClass(DB.FamilySymbol)
                .WhereElementIsNotElementType()):
        try:
            cat = sym.Category.Name if sym.Category else "Unknown"
            family_categories[cat] = family_categories.get(cat, 0) + 1
        except Exception:
            pass

    return {
        "levels": levels,
        "grouping_parameter": group_param,
        "grouping_values": sorted(grouping_values),
        "grouping_count": len(grouping_values),
        "room_name_variants": sorted(room_name_variants),
        "total_rooms": total_rooms,
        "placed_rooms": placed_rooms,
        "unplaced_rooms": total_rooms - placed_rooms,
        "area_schemes": sorted(area_schemes),
        "views": view_counts,
        "family_categories": family_categories,
    }


def _kss_building_segments(apartment_numbers):
    """Unieke leading segments van KSS-appartementnummers (vóór 'Niv')."""
    building_segments = set()
    for apt in apartment_numbers:
        parts = apt.split(".")
        seg_parts = []
        for part in parts:
            if "niv" in part.lower():
                break
            seg_parts.append(part)
        if seg_parts:
            building_segments.add(".".join(seg_parts))
    return sorted(building_segments)


def register_model_structure_routes(api):

    @api.route('/model_structure/', methods=["GET"])
    def get_model_structure(doc, request=None):
        """
        Return a lightweight structural overview of the model — fast, no deep lookups.
        Designed as a discovery call so the AI can ask one targeted clarifying question
        before running expensive queries. Groups on the KSS-default parameter;
        legacy apartment_* keys blijven aanwezig voor bestaande consumers.
        """
        data = _collect_structure(doc, DEFAULT_GROUPING_PARAMETER)
        # Legacy keys (KSS-conventie) voor bestaande tool-laag consumers
        data["apartment_numbers"] = data["grouping_values"]
        data["apartment_count"] = data["grouping_count"]
        data["building_segments"] = _kss_building_segments(data["grouping_values"])
        return routes.make_response(data=data)

    @api.route('/model_structure/groupby/<group_param>', methods=["GET"])
    def get_model_structure_groupby(doc, group_param):
        """Zelfde overview, maar grouping-waarden uit een willekeurige room-parameter
        (de filter-as uit het project profile)."""
        data = _collect_structure(doc, group_param)
        return routes.make_response(data=data)
