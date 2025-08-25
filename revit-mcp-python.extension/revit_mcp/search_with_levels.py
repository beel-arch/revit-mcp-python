# -*- coding: UTF-8 -*-
"""
Element Search with Level Information
Search elements and organize by level with detailed type information
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger
import re

# Import centralized mappings
try:
    import sys
    import os
    # Add lib folder to path for import
    lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
    if lib_path not in sys.path:
        sys.path.append(lib_path)
    
    from CategoryMapping import category_mapping
    from LevelParameterMapping import level_parameter_mapping
except ImportError as e:
    logger.error("Failed to import mappings: {}".format(str(e)))
    category_mapping = {}
    level_parameter_mapping = {}


def text_contains(search_term, target_text):
    """Check if search term is contained in target text (case insensitive)"""
    if not search_term or not target_text:
        return False
    return search_term.lower() in target_text.lower()


def get_level_parameter_for_category(category_name):
    """Get the appropriate level parameter name for a category"""
    return level_parameter_mapping.get(category_name, "Level")


def register_search_with_levels_routes(api):
    """Register search routes with level information"""
    
    @api.route('/search_elements_by_level/<search_term>', methods=["GET"])
    def search_elements_by_level(doc, search_term):
        """Search elements and organize by level with type details"""
        return _search_elements_by_level_impl(doc, search_term, None)
    
    @api.route('/search_elements_by_level/<search_term>/<category_filter>', methods=["GET"])
    def search_elements_by_level_filtered(doc, search_term, category_filter):
        """Search elements in specific category and organize by level"""
        return _search_elements_by_level_impl(doc, search_term, category_filter)
    
    def _search_elements_by_level_impl(doc, search_term, category_filter):
        """Search elements and organize by level with type details"""
        try:
            # Get all levels for reference
            levels = DB.FilteredElementCollector(doc).OfClass(DB.Level).WhereElementIsNotElementType()
            level_dict = {}
            for level in levels:
                level_name = level.Name
                level_dict[level.Id] = level_name
            
            results_by_level = {}
            total_found = 0
            debug_info = []
            
            debug_info.append("Searching for: {}".format(search_term))
            if category_filter:
                debug_info.append("Category filter: {}".format(category_filter))
            debug_info.append("Available levels: {}".format(list(level_dict.values())))
            
            # Search categories in mapping
            for category_key, builtin_category in category_mapping.items():
                # Apply category filter if specified
                if category_filter and category_key.lower() != category_filter.lower():
                    continue
                elements = DB.FilteredElementCollector(doc).OfCategory(builtin_category).WhereElementIsNotElementType()
                
                # Get the appropriate level parameter for this category
                level_param_name = get_level_parameter_for_category(category_key)
                
                for element in elements:
                    try:
                        # Extract family and type names using robust method
                        family_name = None
                        type_name = None
                        element_type = None
                        
                        # 1) Normalize to an ElementType
                        if isinstance(element, DB.ElementType):
                            element_type = element
                        else:
                            if hasattr(element, 'GetTypeId'):
                                try:
                                    tid = element.GetTypeId()
                                except:
                                    tid = DB.ElementId.InvalidElementId
                                if tid and tid != DB.ElementId.InvalidElementId:
                                    element_type = doc.GetElement(tid)
                        
                        # 2) Extract type and family names
                        if element_type:
                            # Type name via parameter
                            try:
                                type_param = element_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                                if type_param and type_param.HasValue:
                                    type_name = type_param.AsString()
                            except:
                                type_name = None
                            
                            # Family name
                            fam_obj = None
                            if hasattr(element_type, 'Family'):
                                try:
                                    fam_obj = element_type.Family
                                except:
                                    fam_obj = None
                            
                            if fam_obj:
                                try:
                                    family_name = fam_obj.Name
                                except:
                                    family_name = None
                        
                        # Ensure we have at least empty strings
                        family_name = family_name or ""
                        type_name = type_name or ""
                        
                        # Check if search term matches family or type name
                        if (text_contains(search_term, family_name) or 
                            text_contains(search_term, type_name)):
                            
                            # Get level information
                            element_level_id = None
                            level_name = "No Level"
                            
                            # Use LookupParameter with the mapped parameter name
                            level_param = element.LookupParameter(level_param_name)
                            if level_param and level_param.HasValue and level_param.StorageType == DB.StorageType.ElementId:
                                element_level_id = level_param.AsElementId()
                            
                            if element_level_id and element_level_id in level_dict:
                                level_name = level_dict[element_level_id]
                            
                            # Initialize level group if needed
                            if level_name not in results_by_level:
                                results_by_level[level_name] = {}
                            
                            # Create type key for grouping
                            type_key = "{} - {}".format(family_name, type_name)
                            
                            # Initialize type group if needed
                            if type_key not in results_by_level[level_name]:
                                results_by_level[level_name][type_key] = {
                                    "family_name": family_name,
                                    "type_name": type_name,
                                    "category": category_key,
                                    "count": 0,
                                    "element_ids": []
                                }
                            
                            # Add element to group
                            results_by_level[level_name][type_key]["count"] += 1
                            results_by_level[level_name][type_key]["element_ids"].append(element.Id.IntegerValue)
                            total_found += 1
                    
                    except Exception as e:
                        continue
            
            # Convert nested dict to list format for easier consumption
            formatted_results = {}
            for level_name, types in results_by_level.items():
                formatted_results[level_name] = list(types.values())
            
            # Calculate summary counts
            level_counts = {}
            for level_name, types in formatted_results.items():
                level_counts[level_name] = sum(t["count"] for t in types)
            
            return routes.make_response(data={
                "status": "success",
                "search_term": search_term,
                "total_found": total_found,
                "level_counts": level_counts,
                "results_by_level": formatted_results,
                "debug_info": debug_info
            })
            
        except Exception as e:
            logger.error("Error in search_elements_by_level: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)
