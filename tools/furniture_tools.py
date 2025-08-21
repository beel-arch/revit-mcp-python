from mcp.server.fastmcp import Context
from typing import Union

def register_furniture_by_room_tools(mcp, revit_get, revit_post, revit_image=None):
    @mcp.tool()
    async def get_furniture_by_room(ctx: Context = None) -> Union[dict, list, str]:
        """Get furniture inventory organized by room with family, type, and mark information."""
        response = await revit_get("/furniture/byroom/", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle list responses (room data)
        if isinstance(response, list):
            result = [f"🛋️ FURNITURE BY ROOM ({len(response)} rooms)"]
            result.append("")
            
            total_furniture = 0
            
            for room_data in response:
                room_number = room_data.get('RoomNumber', '')
                room_name = room_data.get('RoomName', '')
                furniture_list = room_data.get('Furniture', [])
                
                # Create room identifier
                if room_number and room_name:
                    room_id = f"{room_number} - {room_name}"
                elif room_number:
                    room_id = room_number
                elif room_name:
                    room_id = room_name
                else:
                    room_id = "No Room"
                
                total_furniture += len(furniture_list)
                
                if furniture_list:  # Only show rooms with furniture
                    result.append(f"🚪 {room_id} ({len(furniture_list)} items):")
                    
                    for item in furniture_list:
                        family = item.get('Family', 'Unknown')
                        item_type = item.get('Type', 'Unknown')
                        mark = item.get('Mark', '')
                        element_id = item.get('ElementId', '')
                        
                        # Format furniture item
                        furniture_info = f"  • {family} - {item_type}"
                        if mark:
                            furniture_info += f" (Mark: {mark})"
                        if element_id:
                            furniture_info += f" [ID: {element_id}]"
                        
                        result.append(furniture_info)
                    
                    result.append("")  # Add spacing between rooms
            
            # Add summary
            result.insert(1, f"Total Furniture Items: {total_furniture}")
            result.insert(2, "")
            
            return "\n".join(result)
        
        return str(response)
