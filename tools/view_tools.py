"""View-related tools for capturing and listing Revit views"""

from mcp.server.fastmcp import Context
from typing import Union


def register_view_tools(mcp, revit_get, revit_post, revit_image):
    """Register view-related tools"""
    
    @mcp.tool()
    async def get_revit_view(view_name: str, ctx: Context = None) -> str:
        """Export a specific Revit view as an image"""
        return await revit_image(f"/get_view/{view_name}", ctx)

    @mcp.tool()
    async def list_revit_views(ctx: Context = None) -> Union[dict, str]:
        """Get a list of all exportable views in the current Revit model"""
        response = await revit_get("/list_views/", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict):
            if 'views_by_type' in response:
                views_data = response['views_by_type']
                total = response.get('total_exportable_views', 0)
                
                result = [f"📷 EXPORTABLE VIEWS ({total} total)"]
                result.append("")
                
                for view_type, view_list in views_data.items():
                    if view_list:  # Only show categories that have views
                        formatted_type = view_type.replace('_', ' ').title()
                        result.append(f"{formatted_type} ({len(view_list)}):")
                        for view_name in view_list[:10]:  # Limit to first 10 per category
                            result.append(f"  • {view_name}")
                        if len(view_list) > 10:
                            result.append(f"  ... and {len(view_list) - 10} more")
                        result.append("")
                
                return "\n".join(result)
            else:
                return "No views data found in response"
        
        return str(response)

    @mcp.tool()
    async def get_current_view_info(ctx: Context = None) -> Union[dict, str]:
        """
        Get detailed information about the currently active view in Revit.
        
        Returns comprehensive information including:
        - View name, type, and ID
        - Scale and detail level
        - Crop box status
        - View family type
        - View discipline
        - Template status
        """
        if ctx:
            ctx.info("Getting current view information...")
        response = await revit_get("/current_view_info/", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict) and 'view_info' in response:
            view = response['view_info']
            
            result = ["📺 CURRENT VIEW INFORMATION"]
            result.append("")
            result.append(f"Name: {view.get('view_name', 'Unknown')}")
            result.append(f"Type: {view.get('view_type', 'Unknown')}")
            result.append(f"ID: {view.get('view_id', 'Unknown')}")
            result.append(f"Scale: {view.get('scale', 'Unknown')}")
            result.append(f"Detail Level: {view.get('detail_level', 'Unknown')}")
            result.append(f"Discipline: {view.get('discipline', 'Unknown')}")
            result.append(f"Family Type: {view.get('view_family_type', 'Unknown')}")
            result.append(f"Crop Box Active: {view.get('crop_box_active', 'Unknown')}")
            result.append(f"Is Template: {view.get('is_template', 'Unknown')}")
            
            return "\n".join(result)
        
        return str(response)

    @mcp.tool()
    async def get_current_view_elements(ctx: Context = None) -> Union[dict, str]:
        """
        Get all elements visible in the currently active view in Revit.
        
        Returns detailed information about each element including:
        - Element ID, name, and type
        - Category and category ID
        - Level information (if applicable)
        - Location information (point or curve)
        - Summary statistics grouped by category
        
        This is useful for understanding what elements are currently visible
        and analyzing the content of the active view.
        """
        if ctx:
            ctx.info("Getting elements in current view...")
        response = await revit_get("/current_view_elements/", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict):
            view_name = response.get('view_name', 'Unknown')
            total_elements = response.get('total_elements', 0)
            category_counts = response.get('category_counts', {})
            
            result = [f"📋 ELEMENTS IN VIEW: {view_name}"]
            result.append(f"Total Elements: {total_elements:,}")
            result.append("")
            
            # Show category summary
            if category_counts:
                result.append("📏 ELEMENTS BY CATEGORY:")
                # Sort by count, descending
                sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
                for category, count in sorted_categories[:15]:  # Show top 15 categories
                    result.append(f"  {category}: {count:,}")
                
                if len(sorted_categories) > 15:
                    remaining = len(sorted_categories) - 15
                    result.append(f"  ... and {remaining} more categories")
            
            # Note about detailed element data
            result.append("")
            result.append("📝 Note: Use get_furniture_by_room() for detailed furniture analysis")
            result.append("or access full element data through the raw response.")
            
            return "\n".join(result)
        
        return str(response)