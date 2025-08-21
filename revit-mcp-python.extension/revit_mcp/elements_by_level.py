# -*- coding: UTF-8 -*-
"""
Elements by Category and Level Analysis Routes
Provides efficient endpoints for analyzing specific element categories by level
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger
from .utils import safe_string

# Import fuzzy matcher from lib folder - REQUIRED, no fallbacks
import sys
import os
# Add lib folder to path for import
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

from fuzzy_category_matcher import resolve_category, get_supported_categories

# Import centralized mappings - REQUIRED, no fallbacks
from LevelParameterMapping import level_parameter_mapping


# Removed hardcoded parameter enum mapping - we'll use flexible parameter lookup by name only


def get_level_parameter_for_category(canonical_label):
    """Get the appropriate level parameter name for a category"""
    return level_parameter_mapping.get(canonical_label, "Level")  # Default to "Level"


def register_elements_by_category_level_routes(api):
    """Register elements by category and level analysis routes"""
    
    @api.route('/elements_by_category_level/<category>', methods=["GET"])
    def get_elements_by_category_level(doc, category):
        """Get elements of specific category grouped by level (efficient approach)"""
        try:
            # Use fuzzy category resolution
            canonical_label, built_in_category, confidence = resolve_category(category)
            
            if not canonical_label or not built_in_category:
                supported = get_supported_categories()
                return routes.make_response(data={
                    "error": "Category '{}' not recognized (confidence: {:.2f}). Try: {}".format(
                        category, confidence, ", ".join(supported[:10])  # Show first 10
                    )
                }, status=400)
            
            logger.info("Resolved '{}' to '{}' (confidence: {:.2f})".format(
                category, canonical_label, confidence
            ))
            
            # Get all levels for reference
            levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).WhereElementIsNotElementType()
            level_dict = {}
            for level in levels:
                level_name = safe_string(level.Name)
                level_dict[level.Id] = level_name
            
            # Efficiently get only elements of this category
            elements = DB.FilteredElementCollector(doc).OfCategory(built_in_category).WhereElementIsNotElementType()
            
            # Get the appropriate level parameter for this category
            level_param_name = get_level_parameter_for_category(canonical_label)
            
            # Group elements by level
            result_by_level = {}
            no_level_elements = []
            total_elements = 0
            
            for element in elements:
                total_elements += 1
                try:
                    element_level_id = None
                    
                    # Try to get level using parameter name from mapping
                    level_param = element.LookupParameter(level_param_name)
                    if level_param and level_param.HasValue and level_param.StorageType == DB.StorageType.ElementId:
                        element_level_id = level_param.AsElementId()
                    
                    if element_level_id and element_level_id != DB.ElementId.InvalidElementId and element_level_id in level_dict:
                        level_name = level_dict[element_level_id]
                        if level_name not in result_by_level:
                            result_by_level[level_name] = []
                        
                        # Get element info
                        element_info = {
                            "id": element.Id.IntegerValue,
                            "name": safe_string(element.Name if hasattr(element, 'Name') else "Unnamed"),
                        }
                        
                        # Add type information if available
                        if hasattr(element, 'GetTypeId'):
                            type_id = element.GetTypeId()
                            if type_id != DB.ElementId.InvalidElementId:
                                element_type = doc.GetElement(type_id)
                                if element_type:
                                    element_info["type"] = safe_string(element_type.Name)
                        
                        result_by_level[level_name].append(element_info)
                    else:
                        # Level niet gevonden - clean fallback
                        element_info = {
                            "id": element.Id.IntegerValue,
                            "name": safe_string(element.Name if hasattr(element, 'Name') else "Unnamed"),
                            "level": "Level niet gevonden"
                        }
                        no_level_elements.append(element_info)
                        
                except Exception as e:
                    logger.warning("Skipped element {}: {}".format(element.Id, safe_string(str(e))))
                    continue
            
            # Calculate counts per level
            level_counts = {}
            for level_name, elements_list in result_by_level.items():
                level_counts[level_name] = len(elements_list)
            
            return routes.make_response(data={
                "status": "success",
                "category": safe_string(category),
                "resolved_category": canonical_label,
                "confidence": confidence,
                "level_parameter_used": level_param_name,
                "total_elements": total_elements,
                "elements_by_level": result_by_level,
                "level_counts": level_counts,
                "elements_without_level": no_level_elements,
                "no_level_count": len(no_level_elements)
            })
            
        except Exception as e:
            logger.error("Error in get_elements_by_category_level: {}".format(safe_string(str(e))))
            return routes.make_response(data={"error": safe_string(str(e))}, status=500)
