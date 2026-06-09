"""Tool for swapping family types on Revit elements"""

from mcp.server.fastmcp import Context
from typing import List, Union


def register_swap_family_type_tools(mcp, revit_post):

    @mcp.tool()
    async def swap_family_type(
        element_ids: List[int],
        family_name: str,
        type_name: str,
        ctx: Context = None
    ) -> str:
        """
        Change the family type of one or more Revit elements.

        Works for any category: Doors, Windows, Furniture, Walls, Floors, etc.
        The target type must be in the same category as the source elements.

        Args:
            element_ids: List of element IDs to change (from get_elements_by_category)
            family_name: Target family name (e.g. "BEEL_DR_Deur")
            type_name: Target type name within the family (e.g. "900x2100")
        """
        data = {
            "element_ids": element_ids,
            "family_name": family_name,
            "type_name": type_name,
        }
        response = await revit_post("/swap_family_type/", data, ctx)

        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            if "error" in response:
                return "Error: {}".format(response["error"])

            changed = response.get("changed", 0)
            errors = response.get("errors", [])
            target = "{} - {}".format(
                response.get("target_family", ""), response.get("target_type", "")
            )

            lines = [
                "Swap Family Type: {}".format(target),
                "Changed: {} element(s)".format(changed),
            ]
            if errors:
                lines.append("Errors ({}):".format(len(errors)))
                for err in errors[:10]:
                    lines.append("  ID {}: {}".format(err.get("id"), err.get("error")))

            return "\n".join(lines)

        return str(response)
