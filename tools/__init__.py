"""Tool registration system for Revit MCP Server"""

def register_tools(mcp_server, revit_get_func, revit_post_func, revit_image_func):
    """Register all tools with the MCP server"""
    
    # Import all tool modules
    from .status_tools import register_status_tools
    from .view_tools import register_view_tools
    from .family_tools import register_family_tools
    from .model_tools import register_model_tools
    from .door_tools import register_door_all_params_tools
    from .furniture_tools import register_furniture_by_room_tools
    from .room_write_tool import register_room_write_parameters_tools
    # Register tools from each module
    register_status_tools(mcp_server, revit_get_func)
    register_view_tools(mcp_server, revit_get_func, revit_post_func, revit_image_func)
    register_family_tools(mcp_server, revit_get_func, revit_post_func)
    register_model_tools(mcp_server, revit_get_func)
    register_door_all_params_tools(mcp_server, revit_get_func, revit_post_func, revit_image_func)
    register_furniture_by_room_tools(mcp_server, revit_get_func, revit_post_func, revit_image_func)
    register_room_write_parameters_tools(mcp_server, revit_get_func, revit_post_func, revit_image_func)