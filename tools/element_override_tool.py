"""MCP tools: universal element color override and parameter write."""

from mcp.server.fastmcp import Context


def register_element_override_tools(mcp, revit_get, revit_post):

    @mcp.tool()
    async def get_active_view_id(ctx: Context) -> str:
        """
        Return the element ID and name of the currently active view in Revit.
        Use this as view_id for override_element_color when the user has not specified a view.
        Before applying an override, always ask:
          'Wil je dit in het actieve view doen, of geef je een specifiek view op?'
        """
        resp = await revit_get("/active_view_id/", ctx)
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])
        return "Actief view: '{}' — view_id: {}  (type: {})".format(
            resp.get("view_name"), resp.get("view_id"), resp.get("view_type"))

    @mcp.tool()
    async def get_room_tags(room_id: int, ctx: Context) -> str:
        """
        Find all RoomTag elements in the Revit model for a given room element ID.
        Returns the tag element IDs and the views they appear in.
        Use this before calling override_element_color when you want to highlight a room tag.
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
        Override the graphic color of any element in a Revit view.

        Works on any element type: doors, walls, rooms, room tags, windows, furniture, etc.
        The element_id comes from whichever query tool returned the element
        (get_doors_with_rooms, get_furniture_by_room, get_room_tags, ...).
        The view_id comes from get_view_id_by_name or get_room_tags.

        Parameters:
        - view_id:    Revit view element ID. Get it via get_view_id_by_name (by name) or
                      get_active_view_id (active view). If the user did not specify a view,
                      ask: "Wil je dit in het actieve view doen, of geef je een specifiek view op?"
        - element_id: Any Revit element ID (from any query tool)
        - color:      red, green, blue, yellow, orange, purple, white, black
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

    @mcp.tool()
    async def write_element_parameter(
        element_id: int,
        param: str,
        value: str,
        ctx: Context,
    ) -> str:
        """
        Write a value to the Mark or Comments parameter of any Revit element.

        Works on any element type: doors, walls, rooms, windows, furniture, etc.
        The element_id comes from whichever query tool returned the element.

        Parameters:
        - element_id: Any Revit element ID (from any query tool)
        - param:      "mark" or "comments"
        - value:      The string value to write

        Examples:
        - Copy room number to door mark: element_id=<door>, param="mark", value="02"
        - Tag a door with apartment info:  param="comments", value="1.A.Niv 0.12"
        """
        resp = await revit_post("/element/write_param", {
            "element_id": element_id,
            "param": param,
            "value": value,
        }, ctx)
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])
        return "Geschreven: element {} → {}='{}'.".format(
            element_id, resp.get("param"), resp.get("value"))

    @mcp.tool()
    async def write_element_parameter_by_name(
        element_id: int,
        param_name: str,
        value: str,
        ctx: Context,
    ) -> str:
        """
        Write any Revit parameter by its exact name (LookupParameter).

        Works on any element type and any writable parameter — not limited to
        mark or comments. Use get_element_parameters to discover parameter names first.

        Parameters:
        - element_id: Any Revit element ID (from any query tool)
        - param_name: Exact Revit parameter name, e.g. "BEEL_C_TX_AppartementNummer"
        - value:      String value to write

        Tip: combine with write_element_parameters_bulk using param_name key for bulk writes.
        """
        resp = await revit_post("/element/write_param_by_name", {
            "element_id": element_id,
            "param_name": param_name,
            "value": value,
        }, ctx)
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])
        return "Geschreven: element {} → {}='{}'.".format(
            element_id, resp.get("param_name"), resp.get("value"))

    @mcp.tool()
    async def write_element_parameters_bulk(
        writes: list,
        ctx: Context,
    ) -> str:
        """
        Write Mark or Comments to multiple Revit elements in one atomic transaction.

        Works on any element type. All writes happen in a single Revit transaction.

        Parameter `writes` is a list of dicts. Each entry uses either:
          { "element_id": <int>, "param": "mark"|"comments", "value": "<string>" }
        or any Revit parameter by name:
          { "element_id": <int>, "param_name": "BEEL_C_TX_AppartementNummer", "value": "<string>" }
        Both forms can be mixed in one call.

        ## Typical workflows

        **Door marks from room numbers (with suffix for multiple doors per room):**
        1. Call get_doors_with_rooms with apartment_filter / room_name_filter
        2. Group doors by their ToRoom room number
        3. If a room has 1 door → value = room_number  (e.g. "02")
           If a room has N doors → value = room_number + suffix  (e.g. "02a", "02b", "02c")
        4. Call write_element_parameters_bulk with the full list

        **Write compliance result to room comments:**
        1. Run compliance check (compare_rooms_with_checklist / check_window_area_compliance)
        2. Collect element_ids of non-compliant rooms
        3. Call write_element_parameters_bulk:
           [{ "element_id": X, "param": "comments", "value": "te klein" }, ...]

        **Clear marks / comments:**
        Use value="" to erase existing content.
        """
        resp = await revit_post("/element/write_params_bulk", {"writes": writes}, ctx)  # noqa
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])

        written   = resp.get("written", 0)
        errors    = resp.get("errors", 0)
        results   = resp.get("results", [])

        lines = ["{} elementen geschreven, {} fouten.".format(written, errors)]
        for r in results:
            if r["status"] == "ok":
                lines.append("  OK  element {} → {}='{}'".format(
                    r["element_id"], r.get("param"), r.get("value")))
            else:
                lines.append("  ERR element {} → {}".format(
                    r["element_id"], r.get("error")))
        return "\n".join(lines)

    @mcp.tool()
    async def debug_fill_patterns(ctx: Context) -> str:
        """
        List all fill patterns in the Revit model with their name, IsSolidFill flag,
        and target (Drafting/Model). Use this to diagnose why solid fill overrides are
        not working.
        """
        resp = await revit_get("/debug/fill_patterns", ctx)
        if isinstance(resp, str):
            return resp
        if "error" in resp:
            return "Fout: {}".format(resp["error"])
        patterns = resp.get("patterns", [])
        lines = ["{} fill patterns:".format(resp.get("count", 0)), ""]
        for p in patterns:
            lines.append("  {:>10}  is_solid={!s:<5}  target={:<10}  {}".format(
                p["id"], p["is_solid"], p["target"], p["name"]))
        return "\n".join(lines)

    @mcp.tool()
    async def override_elements_color_bulk(
        overrides: list,
        ctx: Context,
    ) -> str:
        """
        Apply (or clear) graphic color overrides on multiple elements across multiple
        views in one Revit transaction.

        Parameter `overrides` is a list of dicts:
          { "view_id": <int>, "element_id": <int>, "color": "red"|"green"|...|"clear" }

        Use "clear" to remove an existing override.
        Colors: red, green, blue, yellow, orange, purple, white, black.

        Typical use: compliance check → collect non-compliant element_ids with their
        view_ids → call this once to highlight all of them in red.
        """
        payload = []
        for entry in overrides:
            color_val = None if str(entry.get("color", "")).strip().lower() == "clear" else entry.get("color")
            payload.append({
                "view_id": entry["view_id"],
                "element_id": entry["element_id"],
                "color": color_val,
            })

        resp = await revit_post("/override_graphics_bulk", {"overrides": payload}, ctx)
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])

        applied = resp.get("applied", 0)
        errors  = resp.get("errors", 0)
        lines   = ["{} overrides toegepast, {} fouten.".format(applied, errors)]
        for r in resp.get("results", []):
            if r["status"] == "error":
                lines.append("  ERR  element {} in view {} → {}".format(
                    r["element_id"], r["view_id"], r.get("error")))
        return "\n".join(lines)

    @mcp.tool()
    async def reset_view_overrides(view_id: int, ctx: Context) -> str:
        """
        Remove all graphic color overrides from every element in a view.
        Use get_active_view_id or get_view_id_by_name to get the view_id.
        """
        resp = await revit_post("/override_graphics/reset_view/{}".format(view_id), {}, ctx)
        if isinstance(resp, str):
            return "Fout: {}".format(resp)
        if "error" in resp:
            return "Fout: {}".format(resp["error"])
        return "Alle overrides verwijderd in view {} — {} elementen gereset.".format(
            view_id, resp.get("elements_reset", 0))
