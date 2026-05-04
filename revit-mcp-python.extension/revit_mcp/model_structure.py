# -*- coding: UTF-8 -*-
"""
Lightweight model structure discovery endpoint.
Returns identifiers (apartment numbers, room names, levels, area schemes, view counts,
family category counts) without any deep parameter lookups.
"""

from pyrevit import routes, DB


def register_model_structure_routes(api):

    @api.route('/model_structure/', methods=["GET"])
    def get_model_structure(doc, request=None):
        """
        Return a lightweight structural overview of the model — fast, no deep lookups.
        Designed as a discovery call so the AI can ask one targeted clarifying question
        before running expensive queries.
        """

        # --- Levels ---
        levels = []
        for lvl in (DB.FilteredElementCollector(doc)
                    .OfClass(DB.Level)
                    .WhereElementIsNotElementType()):
            try:
                levels.append({
                    "name": lvl.Name,
                    "elevation_m": round(lvl.Elevation * 0.3048, 2),
                })
            except Exception:
                pass
        levels.sort(key=lambda x: x["elevation_m"])

        # --- Rooms: unique apartment numbers + unique room name variants ---
        apartment_numbers = set()
        room_name_variants = set()
        for room in (DB.FilteredElementCollector(doc)
                     .OfCategory(DB.BuiltInCategory.OST_Rooms)
                     .WhereElementIsNotElementType()):
            try:
                area = room.Area * 0.092903
                if not area:
                    continue
                name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString() or ""
                if name:
                    room_name_variants.add(name)
                p = room.LookupParameter("BEEL_C_TX_AppartementNummer")
                if p and p.HasValue:
                    val = p.AsString()
                    if val:
                        apartment_numbers.add(val)
            except Exception:
                pass

        # Derive unique leading segments of apartment numbers (before "Niv") as candidate
        # building / block identifiers — helps the AI present meaningful options to the user.
        building_segments = set()
        for apt in apartment_numbers:
            parts = apt.split(".")
            # Collect leading parts until we hit a segment containing "Niv" or a digit-only part
            seg_parts = []
            for part in parts:
                if "niv" in part.lower():
                    break
                seg_parts.append(part)
            if seg_parts:
                building_segments.add(".".join(seg_parts))

        # --- Area schemes ---
        area_schemes = []
        try:
            for scheme in (DB.FilteredElementCollector(doc).OfClass(DB.AreaScheme)):
                try:
                    area_schemes.append(scheme.Name)
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

        return routes.make_response(data={
            "levels": levels,
            "apartment_numbers": sorted(apartment_numbers),
            "apartment_count": len(apartment_numbers),
            "building_segments": sorted(building_segments),
            "room_name_variants": sorted(room_name_variants),
            "area_schemes": sorted(area_schemes),
            "views": view_counts,
            "family_categories": family_categories,
        })
