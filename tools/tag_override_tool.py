"""MCP tools: find room tags and override their graphics in a view."""

from mcp.server.fastmcp import Context


def register_tag_override_tools(mcp, revit_get, revit_post):

    @mcp.tool()
    async def get_room_tags(room_id: int, ctx: Context) -> str:
        """
        Find all RoomTag elements in the Revit model for a given room element ID.
        Returns the tag element IDs and the views they appear in.
        Use this before calling override_element_color.
        """
        resp = await revit_get("/room_tags/{}".format(room_id), ctx)
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])
        tags = resp.get("tags", [])
        if not tags:
            return "Geen tags gevonden voor room {}.".format(room_id)
        lines = ["Tags voor room {}:".format(room_id)]
        for t in tags:
            lines.append("  tag_id={tag_id}  view='{view_name}' (view_id={view_id})".format(**t))
        return "\n".join(lines)

    @mcp.tool()
    async def override_element_color(
        view_id: int,
        element_id: int,
        color: str,
        ctx: Context,
    ) -> str:
        """
        Override the graphic color of an element in a Revit view.
        Typically used to highlight a room tag (e.g. red = non-compliant).

        Parameters:
        - view_id:    Revit view element ID (from get_room_tags)
        - element_id: Element to override, e.g. a RoomTag ID (from get_room_tags)
        - color:      Color name: red, green, blue, yellow, orange, purple, white, black
                      Use "clear" to remove the override.
        """
        color_val = None if color.strip().lower() == "clear" else color.strip()
        resp = await revit_post("/override_graphics", {
            "view_id": view_id,
            "element_id": element_id,
            "color": color_val,
        }, ctx)
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])
        return "Override toegepast: element {} in view {} → {}.".format(
            element_id, view_id, resp.get("color", color))
