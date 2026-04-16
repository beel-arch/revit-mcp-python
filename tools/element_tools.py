"""MCP tools for querying elements by category and element parameters"""

from mcp.server.fastmcp import Context
from typing import Union


def register_element_tools(mcp, revit_get):
    """Register element query tools"""

    @mcp.tool()
    async def get_elements_by_category(category: str, ctx: Context) -> str:
        """
        Get all instances of a Revit category with their ID, family, type and level.

        Args:
            category: Category name, e.g. "Doors", "Windows", "Walls", "Furniture".
                      Use the exact name from the Revit category list.
        """
        response = await revit_get(f"/elements_by_category/{category}", ctx)

        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            if "error" in response:
                return f"Error: {response['error']}"

            lines = [
                f"Category: {response.get('category', category)}",
                f"Total elements: {response.get('count', 0)}",
                "",
            ]

            for el in response.get("elements", []):
                family = el.get("family_name", "")
                type_name = el.get("type_name", "")
                level = el.get("level", "No Level")
                el_id = el.get("id")
                lines.append(f"  ID {el_id} | {family} - {type_name} | Level: {level}")

            return "\n".join(lines)

        return str(response)

    @mcp.tool()
    async def get_element_parameters(element_id: int, ctx: Context) -> str:
        """
        Get all instance and type parameters for a specific Revit element.

        Args:
            element_id: The integer element ID (e.g. from get_elements_by_category)
        """
        response = await revit_get(f"/element_parameters/{element_id}", ctx)

        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            if "error" in response:
                return f"Error: {response['error']}"

            lines = [
                f"Element ID: {response.get('element_id')}",
                f"Category: {response.get('category', 'Unknown')}",
                "",
                "--- INSTANCE PARAMETERS ---",
            ]

            for p in response.get("instance_parameters", []):
                val = p.get("value_string") or p.get("value")
                val = val if val is not None else "(no value)"
                ro = " [read-only]" if p.get("is_read_only") else ""
                lines.append(f"  {p['name']}: {val}{ro}")

            type_params = response.get("type_parameters", [])
            if type_params:
                lines.append("")
                lines.append("--- TYPE PARAMETERS ---")
                for p in type_params:
                    val = p.get("value_string") or p.get("value")
                    val = val if val is not None else "(no value)"
                    ro = " [read-only]" if p.get("is_read_only") else ""
                    lines.append(f"  {p['name']}: {val}{ro}")

            return "\n".join(lines)

        return str(response)
