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
    async def search_elements(search_term: str, ctx: Context = None) -> Union[dict, str]:
        """Search elements by family/type names with semantic understanding
        
        Examples: 'kasten', 'chairs', 'doors', 'tables'
        Returns: Category, family name, type name, and count per type
        """
        response = await revit_get(f"/search_elements/{search_term}", ctx)
        return response
    
    @mcp.tool()
    async def search_elements_by_level(search_term: str, category: str = None, ctx: Context = None) -> Union[dict, str]:
        """Search elements and group results by building level with type details
        
        Args:
            search_term: What to search for (e.g., 'kasten', 'chairs', 'doors')
            category: Optional category filter (e.g., 'Doors', 'Furniture', 'Windows')
        
        Returns: Elements grouped by level with family/type details and counts
        """
        if category:
            response = await revit_get(f"/search_elements_by_level/{search_term}/{category}", ctx)
        else:
            response = await revit_get(f"/search_elements_by_level/{search_term}", ctx)
        return response