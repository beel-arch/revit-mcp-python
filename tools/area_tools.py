"""MCP tools for querying Revit Areas"""

from mcp.server.fastmcp import Context


def register_area_tools(mcp, revit_get):

    @mcp.tool()
    async def get_areas_by_scheme(scheme_name: str, ctx: Context) -> str:
        """
        Get all Areas in Revit that belong to a specific Area Scheme.
        Returns each area's number, name, area (m²) and level.

        Args:
            scheme_name: The exact name of the Area Scheme, e.g. "WO" or "Gross Building".
        """
        response = await revit_get(f"/areas/{scheme_name}", ctx)
        return _format_areas(response, scheme_name)

    @mcp.tool()
    async def get_all_areas(ctx: Context) -> str:
        """
        Get all Areas in the Revit model across all Area Schemes.
        Returns each area's scheme, number, name, area (m²) and level.
        """
        response = await revit_get("/areas/", ctx)
        return _format_areas(response, scheme_name=None)


def _format_areas(response, scheme_name):
    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        if "error" in response:
            return f"Error: {response['error']}"

        areas = response.get("areas", [])
        count = response.get("count", 0)
        header = f"Areas for scheme '{scheme_name}'" if scheme_name else "All Areas"
        lines = [header, f"Total: {count}", ""]

        for a in areas:
            scheme_col = f"[{a['scheme']}] " if not scheme_name else ""
            area_str = f"{a['area_m2']} m²" if a["area_m2"] is not None else "N/A"
            level_str = f" | Level: {a['level']}" if a["level"] else ""
            lines.append(
                f"  {scheme_col}{a['number']} - {a['name']} | {area_str}{level_str}"
            )

        return "\n".join(lines)

    return str(response)
