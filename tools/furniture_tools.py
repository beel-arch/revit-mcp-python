from mcp.server.fastmcp import Context

def register_furniture_by_room_tools(mcp, revit_get, revit_post, revit_image=None):
    @mcp.tool()
    async def get_furniture_by_room(ctx: Context = None) -> str:
        """Geeft per Room de lijst met Furniture (Family/Type/Mark)."""
        return await revit_get("/furniture/byroom/", ctx)
