from mcp.server.fastmcp import Context

def register_door_all_params_tools(mcp, revit_get, revit_post, revit_image=None):
    @mcp.tool()
    async def get_doors_all_params(ctx: Context = None) -> str:
        """
        Haalt alle parameters op van alle deuren in het model.
        """
        return await revit_get("/doors/allparams/", ctx)