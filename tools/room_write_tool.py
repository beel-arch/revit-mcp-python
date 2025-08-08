from mcp.server.fastmcp import Context

def register_room_write_parameters_tools(mcp, revit_get, revit_post, revit_image=None):
    @mcp.tool()
    async def set_room_parameter(room_id: int,
                                 parameter: str,
                                 value: str,
                                 ctx: Context = None) -> str:
        """
        Set a parameter on a Room element in Revit.

        Args:
            room_id: ElementId of the room (integer).
            parameter: Parameter name (exact match in Revit).
            value: Value to set (string, number, or boolean in string form).

        Returns:
            JSON result from the Revit MCP route.
        """
        payload = {
            "room_id": room_id,
            "parameter": parameter,
            "value": value
        }
        return await revit_post("/room/setparameter/", payload, ctx)
