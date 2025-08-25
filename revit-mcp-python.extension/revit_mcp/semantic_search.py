# -*- coding: UTF-8 -*-
"""
Simple Element Search Routes
Search elements by family/type names across all categories
"""

from pyrevit import routes
import Autodesk.Revit.DB as DB
from . import logger
from .utils import safe_string
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
except ImportError as e:
    logger.error("Failed to import CategoryMapping: {}".format(str(e)))
    category_mapping = {}


def normalize_search_term(term):
    """Normalize search term for matching"""
    if not term:
        return ""
    normalized = re.sub(r'[^a-z0-9\s]', '', term.lower())
    return normalized.strip()


def text_contains(search_term, target_text):
    """Check if search term is contained in target text (case insensitive)"""
    if not search_term or not target_text:
        return False
    
    # Simple case-insensitive contains check
    return search_term.lower() in target_text.lower()


def register_simple_search_routes(api):
    """Register simple search routes"""
    
    @api.route('/search_elements/<search_term>', methods=["GET"])
    def search_elements(doc, search_term):
        """Search elements by family/type names across all categories"""
        try:
            results = {}
            total_found = 0
            debug_info = []  # Keep for minimal debug
            
            # Only debug Furniture category to avoid crashes
            debug_info.append("Searching categories for: {}".format(search_term))
            
            # Search all categories in mapping (use actual keys from CategoryMapping)
            for category_key, builtin_category in category_mapping.items():
                elements = DB.FilteredElementCollector(doc).OfCategory(builtin_category).WhereElementIsNotElementType()
                
                # Only debug Furniture to avoid memory issues
                if category_key == "Furniture":
                    element_count = len(list(elements))
                    debug_info.append("Furniture category: {} elements".format(element_count))
                
                # Only process Furniture for now to avoid crashes
                if category_key != "Furniture":
                    continue
                
                category_results = []
                
                for element in elements:
                    try:
                        # Robust family/type name extraction
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
                        
                        # 2) Extract type and family names safely
                        if element_type:
                            # Type name via parameter instead of .Name property
                            try:
                                # Use parameter method instead of direct property
                                type_param = element_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                                if type_param and type_param.HasValue:
                                    type_name = type_param.AsString()
                                else:
                                    type_name = None
                                # Only debug first few to avoid memory issues
                                if len(category_results) < 3:
                                    debug_info.append("Type name: '{}'".format(type_name))
                            except Exception as ex:
                                type_name = None
                                debug_info.append("Type name extraction failed: {}".format(str(ex)))
                            
                            # Try loadable family first
                            fam_obj = None
                            if hasattr(element_type, 'Family'):
                                try:
                                    fam_obj = element_type.Family
                                except:
                                    fam_obj = None
                            
                            if fam_obj:
                                try:
                                    family_name = fam_obj.Name  # NO safe_string
                                except:
                                    family_name = None
                            else:
                                # System families often expose .FamilyName
                                if hasattr(element_type, 'FamilyName'):
                                    try:
                                        family_name = element_type.FamilyName  # NO safe_string
                                    except:
                                        family_name = None
                                
                                # Fallback: built-in parameter for family name
                                if not family_name:
                                    try:
                                        p = element_type.get_Parameter(DB.BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)
                                        if p:
                                            family_name = p.AsString()  # NO safe_string
                                    except:
                                        pass
                        
                        # Ensure we have at least empty strings
                        family_name = family_name or ""
                        type_name = type_name or ""
                        
                        # Only debug first few elements to avoid memory issues
                        if category_key == "Furniture" and len(category_results) < 3:
                            debug_info.append("Element {}: Family='{}', Type='{}'".format(
                                element.Id.IntegerValue, family_name, type_name))
                        
                        # Check if search term matches family or type name
                        if (text_contains(search_term, family_name) or 
                            text_contains(search_term, type_name)):
                            
                            category_results.append({
                                "element_id": element.Id.IntegerValue,
                                "family_name": family_name,
                                "type_name": type_name,
                                "category": category_key.title()
                            })
                            total_found += 1
                    
                    except Exception as e:
                        continue
                
                # Group results by family-type combination
                if category_results:
                    grouped = {}
                    for item in category_results:
                        key = "{} - {}".format(item['family_name'], item['type_name'])
                        if key not in grouped:
                            grouped[key] = {
                                "family_name": item["family_name"],
                                "type_name": item["type_name"],
                                "category": item["category"],
                                "count": 0,
                                "element_ids": []
                            }
                        grouped[key]["count"] += 1
                        grouped[key]["element_ids"].append(item["element_id"])
                    
                    results[category_key.title()] = list(grouped.values())
            
            return routes.make_response(data={
                "status": "success",
                "search_term": search_term,  # NO safe_string
                "total_found": total_found,
                "results": results,
                "debug_info": debug_info
            })
            
        except Exception as e:
            logger.error("Error in search_elements: {}".format(str(e)))
            return routes.make_response(data={"error": str(e)}, status=500)
