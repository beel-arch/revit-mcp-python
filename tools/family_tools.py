"""Family and placement tools"""

from mcp.server.fastmcp import Context
from typing import Dict, Any, Union


def register_family_tools(mcp, revit_get, revit_post):
    """Register family-related tools"""
    
    @mcp.tool()
    async def place_family(
        family_name: str,
        type_name: str = None,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        rotation: float = 0.0,
        level_name: str = None,
        properties: Dict[str, Any] = None,
        ctx: Context = None
    ) -> Union[dict, str]:
        """Place a family instance at a specified location in the Revit model"""
        data = {
            "family_name": family_name,
            "type_name": type_name,
            "location": {"x": x, "y": y, "z": z},
            "rotation": rotation,
            "level_name": level_name,
            "properties": properties or {}
        }
        return await revit_post("/place_family/", data, ctx)

    @mcp.tool()
    async def list_families(
        contains: str = None,
        limit: int = 50,
        ctx: Context = None
    ) -> Union[dict, str]:
        """Get a flat list of available family types in the current Revit model"""
        params = {}
        if contains:
            params["contains"] = contains
        if limit != 50:
            params["limit"] = str(limit)
        
        response = await revit_get("/list_families/", ctx, params=params)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict) and 'families' in response:
            families = response['families']
            total = response.get('truncated_total', len(families))
            
            result = [f"🏠 AVAILABLE FAMILIES ({total} shown)"]
            if contains:
                result[0] = f"🏠 FAMILIES CONTAINING '{contains}' ({total} found)"
            result.append("")
            
            # Group by category for better organization
            by_category = {}
            for family in families:
                category = family.get('category', 'Unknown')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(family)
            
            for category, family_list in sorted(by_category.items()):
                result.append(f"{category} ({len(family_list)}):")
                for family in family_list[:10]:  # Limit per category
                    family_name = family.get('family_name', 'Unknown')
                    type_name = family.get('type_name', 'Unknown')
                    is_active = "✅" if family.get('is_active') else "⏸️"
                    result.append(f"  {is_active} {family_name} - {type_name}")
                
                if len(family_list) > 10:
                    result.append(f"  ... and {len(family_list) - 10} more")
                result.append("")
            
            return "\n".join(result)
        
        return str(response)

    @mcp.tool()
    async def list_family_categories(ctx: Context = None) -> Union[dict, str]:
        """Get a list of all family categories in the current Revit model"""
        response = await revit_get("/list_family_categories/", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict) and 'categories' in response:
            categories = response['categories']
            total_categories = response.get('total_categories', len(categories))
            
            result = [f"📏 FAMILY CATEGORIES ({total_categories} total)"]
            result.append("")
            
            # Sort by count, descending
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            for category, count in sorted_categories:
                result.append(f"  {category}: {count:,} families")
            
            return "\n".join(result)
        
        return str(response)