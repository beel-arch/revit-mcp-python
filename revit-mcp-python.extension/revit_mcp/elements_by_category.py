# -*- coding: UTF-8 -*-
"""
Elements by Category and Element Parameters routes
GET /elements_by_category/<category_name>  - list all instances of a category
GET /element_parameters/<element_id>       - all parameters for one element
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger
import sys
import os

# Load CategoryMapping from lib
try:
    lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
    if lib_path not in sys.path:
        sys.path.append(lib_path)
    from CategoryMapping import category_mapping
except ImportError as e:
    logger.error("Failed to import CategoryMapping: {}".format(str(e)))
    category_mapping = {}


def _get_param_value(param):
    """Safely read a parameter value, returns serialisable Python type."""
    try:
        if not param.HasValue:
            return None
        st = param.StorageType
        if st == DB.StorageType.String:
            return param.AsString()
        elif st == DB.StorageType.Integer:
            return param.AsInteger()
        elif st == DB.StorageType.Double:
            # Prefer the display string; fall back to raw double
            vs = param.AsValueString()
            return vs if vs is not None else param.AsDouble()
        elif st == DB.StorageType.ElementId:
            eid = param.AsElementId()
            return eid.IntegerValue if eid else None
        return None
    except Exception:
        return None


def register_element_routes(api):
    """Register element query routes"""

    # ------------------------------------------------------------------
    # GET /elements_by_category/<category_name>
    # ------------------------------------------------------------------
    @api.route('/elements_by_category/<category_name>', methods=["GET"])
    def get_elements_by_category(doc, category_name):
        """Return all instances of a category with id, family, type and level."""
        try:
            # Match category name case-insensitively
            builtin_cat = None
            matched_key = None
            for key, bic in category_mapping.items():
                if key.lower() == category_name.lower():
                    builtin_cat = bic
                    matched_key = key
                    break

            if builtin_cat is None:
                return routes.make_response(
                    data={
                        "error": "Unknown category: '{}'. Available categories: {}".format(
                            category_name, sorted(category_mapping.keys())
                        )
                    },
                    status=400
                )

            elements = (
                DB.FilteredElementCollector(doc)
                .OfCategory(builtin_cat)
                .WhereElementIsNotElementType()
                .ToElements()
            )

            results = []
            for elem in elements:
                elem_data = {"id": elem.Id.IntegerValue}

                # Family and type name from the element type
                try:
                    type_el = doc.GetElement(elem.GetTypeId())
                    if type_el:
                        tp = type_el.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                        elem_data["type_name"] = tp.AsString() if (tp and tp.HasValue) else ""
                        fam = getattr(type_el, 'Family', None)
                        elem_data["family_name"] = fam.Name if fam else ""
                    else:
                        elem_data["type_name"] = ""
                        elem_data["family_name"] = ""
                except Exception:
                    elem_data["type_name"] = ""
                    elem_data["family_name"] = ""

                # Level
                elem_data["level"] = "No Level"
                try:
                    lp = elem.LookupParameter("Level")
                    if lp and lp.HasValue and lp.StorageType == DB.StorageType.ElementId:
                        level_el = doc.GetElement(lp.AsElementId())
                        if level_el:
                            elem_data["level"] = level_el.Name
                    elif hasattr(elem, 'LevelId'):
                        level_el = doc.GetElement(elem.LevelId)
                        if level_el:
                            elem_data["level"] = level_el.Name
                except Exception:
                    pass

                results.append(elem_data)

            return routes.make_response(data={
                "category": matched_key,
                "count": len(results),
                "elements": results
            })

        except Exception as e:
            logger.error("Error in get_elements_by_category: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    # ------------------------------------------------------------------
    # GET /element_parameters/<element_id>
    # ------------------------------------------------------------------
    @api.route('/element_parameters/<element_id>', methods=["GET"])
    def get_element_parameters(doc, element_id):
        """Return all instance and type parameters for a single element."""
        try:
            eid = DB.ElementId(int(element_id))
            elem = doc.GetElement(eid)

            if not elem:
                return routes.make_response(
                    data={"error": "Element not found: {}".format(element_id)},
                    status=404
                )

            # Instance parameters
            instance_params = []
            for param in elem.Parameters:
                try:
                    instance_params.append({
                        "name": param.Definition.Name,
                        "storage_type": str(param.StorageType).split(".")[-1],
                        "is_read_only": param.IsReadOnly,
                        "value": _get_param_value(param),
                        "value_string": param.AsValueString() if param.HasValue else None
                    })
                except Exception:
                    continue
            instance_params.sort(key=lambda x: x["name"])

            # Type parameters
            type_params = []
            try:
                type_el = doc.GetElement(elem.GetTypeId())
                if type_el:
                    for param in type_el.Parameters:
                        try:
                            type_params.append({
                                "name": param.Definition.Name,
                                "storage_type": str(param.StorageType).split(".")[-1],
                                "is_read_only": param.IsReadOnly,
                                "value": _get_param_value(param),
                                "value_string": param.AsValueString() if param.HasValue else None
                            })
                        except Exception:
                            continue
                    type_params.sort(key=lambda x: x["name"])
            except Exception:
                pass

            cat_name = elem.Category.Name if elem.Category else "Unknown"

            return routes.make_response(data={
                "element_id": int(element_id),
                "category": cat_name,
                "instance_parameters": instance_params,
                "type_parameters": type_params
            })

        except Exception as e:
            logger.error("Error in get_element_parameters: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)

    logger.info("Element routes registered successfully")
