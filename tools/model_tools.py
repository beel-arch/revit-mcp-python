"""Model structure and hierarchy tools"""

from mcp.server.fastmcp import Context
from typing import Union


def register_model_tools(mcp, revit_get):
    """Register model structure tools"""
    
    @mcp.tool()
    async def list_levels(ctx: Context = None) -> Union[dict, str]:
        """Get a list of all levels in the current Revit model"""
        response = await revit_get("/list_levels/", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict):
            if 'levels' in response:
                levels = response['levels']
                result = [f"📏 BUILDING LEVELS ({len(levels)} total)"]
                result.append("")
                
                for level in levels:
                    name = level.get('name', 'Unnamed')
                    elevation = level.get('elevation', 'Unknown')
                    level_id = level.get('id', 'Unknown')
                    
                    if isinstance(elevation, (int, float)):
                        # Note: Elevations from Revit API are in project units
                        result.append(f"  {name}: {elevation:.2f} (ID: {level_id})")
                    else:
                        result.append(f"  {name}: {elevation} (ID: {level_id})")
                
                return "\n".join(result)
            else:
                return "No levels data found in response"
        
        return str(response)

    @mcp.tool()
    async def debug_element_parameters(category: str, ctx: Context = None) -> Union[dict, str]:
        """Debug: Show all parameters of first element in category"""
        response = await revit_get(f"/debug_element_parameters/{category}", ctx)
        
        # Return raw response for detailed inspection
        return response

    @mcp.tool()
    async def get_elements_by_category_level(category: str, ctx: Context = None) -> Union[dict, str]:
        """Get elements of specific category grouped by level (efficient approach)
        
        Examples: 'doors', 'deuren', 'walls', 'muren', 'windows', 'ramen'
        """
        response = await revit_get(f"/elements_by_category_level/{category}", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict):
            if 'level_counts' in response:
                category_name = response.get('category', category)
                level_counts = response['level_counts']
                total_elements = response.get('total_elements', 0)
                no_level_count = response.get('no_level_count', 0)
                level_param = response.get('level_parameter_used', 'Level')
                
                result = [f"📊 {category_name.upper()} BY LEVEL ({total_elements} total)"]
                result.append(f"Parameter used: {level_param}")
                result.append("")
                
                # Show counts per level
                if level_counts:
                    for level_name, count in level_counts.items():
                        result.append(f"🏢 {level_name}: {count} {category_name}")
                
                # Show elements without level if any
                if no_level_count > 0:
                    result.append(f"⚠️ No level: {no_level_count} {category_name}")
                
                return "\n".join(result)
            else:
                return "No category level data found in response"
        
        return str(response)