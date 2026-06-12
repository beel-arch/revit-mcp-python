"""Tool for querying rooms with their associated doors (Room -> Door direction)"""

from urllib.parse import quote

from mcp.server.fastmcp import Context

from .project_profile_tool import get_grouping, DEFAULT_GROUPING_PARAMETER


def register_rooms_with_doors_tools(mcp, revit_get):

    @mcp.tool()
    async def get_rooms_with_doors(
        unit_filter: str = None,
        ctx: Context = None
    ) -> str:
        """
        Return all rooms with their associated doors.

        Answers questions like:
        - "Hebben alle ruimtes een deur?"
        - "Wat voor deur heeft de badkamer in appartement 1.A?"
        - "Welke ruimtes hebben geen deur?"

        Each door entry shows family type, width, and whether the room is the
        from_room (door swings away from room) or to_room (door swings into room).

        Args:
            unit_filter: Optional prefix op de grouping-parameter uit het project
                         profile (KSS: appartementnummer "1.A"; JGC: ruimtegroep "BW";
                         THELLO: UnitID "C1"). Roep get_model_structure op voor
                         geldige waarden.
        """
        group_param, group_label, _profile = await get_grouping(revit_get, ctx)

        if group_param == DEFAULT_GROUPING_PARAMETER:
            if unit_filter:
                endpoint = "/rooms/with_doors/apartment/{}".format(quote(unit_filter, safe=""))
            else:
                endpoint = "/rooms/with_doors/"
        else:
            endpoint = "/rooms/with_doors/groupby/{}/{}".format(
                quote(group_param, safe=""),
                quote(unit_filter, safe="") if unit_filter else "all")

        response = await revit_get(endpoint, ctx)

        if isinstance(response, str):
            return response

        if not isinstance(response, dict):
            return str(response)

        if "error" in response:
            return "Error: {}".format(response["error"])

        total = response.get("total_rooms", 0)
        without_doors = response.get("rooms_without_doors", 0)
        rooms = response.get("rooms", [])

        if total == 0:
            apt_msg = " (filter: {})".format(unit_filter) if unit_filter else ""
            return "Geen ruimtes gevonden{}.".format(apt_msg)

        lines = [
            "RUIMTES MET DEUREN — {} ruimtes, {} zonder deur".format(total, without_doors),
            "Grouping: '{}' ({})".format(group_param, group_label),
            "",
        ]

        # Show rooms without doors first — this is the most actionable signal
        no_door_rooms = [r for r in rooms if r.get("door_count", 0) == 0]
        if no_door_rooms:
            lines.append("RUIMTES ZONDER DEUR ({})".format(len(no_door_rooms)))
            for r in no_door_rooms:
                grp = r.get("group") or r.get("appartement_nr") or ""
                lines.append("  {} | {} | {}".format(
                    r.get("room_name", ""),
                    r.get("room_number", ""),
                    grp,
                ))
            lines.append("")

        # Rooms with doors
        with_door_rooms = [r for r in rooms if r.get("door_count", 0) > 0]
        if with_door_rooms:
            lines.append("RUIMTES MET DEUREN ({})".format(len(with_door_rooms)))
            lines.append("  {:<25} {:<8} {:<20} {:<30} {:>6}  {:<10}  {}".format(
                "Ruimte", "Nr", group_label.capitalize()[:20], "Deur type", "Breed.", "Zijde", "Deur ID"
            ))
            lines.append("  " + "-" * 110)
            for r in with_door_rooms:
                grp = r.get("group") or r.get("appartement_nr") or ""
                room_name = r.get("room_name", "")
                room_nr = r.get("room_number", "")
                for door in r.get("doors", []):
                    type_label = "{} {}".format(
                        door.get("family_name", ""),
                        door.get("type_name", "")
                    ).strip()
                    width = "{}mm".format(door.get("width_mm")) if door.get("width_mm") else "—"
                    side = door.get("side", "")
                    door_id = door.get("element_id", "")
                    lines.append("  {:<25} {:<8} {:<20} {:<30} {:>6}  {:<10}  [id:{}]".format(
                        room_name[:25], room_nr[:8], grp[:20], type_label[:30], width, side, door_id
                    ))
                    # Clear room name for subsequent doors of same room
                    room_name = ""
                    room_nr = ""
                    grp = ""

        return "\n".join(lines)
