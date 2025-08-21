"""Status and model information tools"""

from mcp.server.fastmcp import Context
from typing import Union


def register_status_tools(mcp, revit_get):
    """Register status-related tools"""
    
    @mcp.tool()
    async def get_revit_status(ctx: Context) -> Union[dict, str]:
        """Check if the Revit MCP API is active and responding"""
        response = await revit_get("/status/", ctx, timeout=10.0)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict):
            if response.get('status') == 'active':
                return f"✅ Revit is ACTIVE and healthy\n" \
                       f"Document: {response.get('document_title', 'Unknown')}\n" \
                       f"API: {response.get('api_name', 'revit_mcp')}"
            else:
                return f"❌ Revit is UNHEALTHY\n" \
                       f"Error: {response.get('error', 'Unknown error')}\n" \
                       f"Status: {response.get('status', 'Unknown')}"
        
        return str(response)

    @mcp.tool()
    async def get_revit_model_info(ctx: Context) -> Union[dict, str]:
        """Get comprehensive information about the current Revit model"""
        response = await revit_get("/model_info/", ctx)
        
        # Handle string error responses
        if isinstance(response, str):
            return response
            
        # Handle dictionary responses
        if isinstance(response, dict):
            result = []
            
            # Project Information
            if 'project_info' in response:
                proj = response['project_info']
                result.append("📋 PROJECT INFORMATION")
                result.append(f"Name: {proj.get('name', 'Not Set')}")
                result.append(f"Number: {proj.get('number', 'Not Set')}")
                result.append(f"Client: {proj.get('client', 'Not Set')}")
                result.append(f"File: {proj.get('file_name', 'Unknown')}")
                result.append("")
            
            # Element Summary
            if 'element_summary' in response:
                elem = response['element_summary']
                result.append("🏗️ MODEL CONTENT")
                result.append(f"Total Elements: {elem.get('total_elements', 0):,}")
                if 'by_category' in elem:
                    for category, count in elem['by_category'].items():
                        if count > 0:
                            result.append(f"  {category}: {count:,}")
                result.append("")
            
            # Model Health
            if 'model_health' in response:
                health = response['model_health']
                result.append("⚕️ MODEL HEALTH")
                result.append(f"Total Warnings: {health.get('total_warnings', 0)}")
                result.append(f"Critical Warnings: {health.get('critical_warnings', 0)}")
                result.append(f"Unplaced Rooms: {health.get('unplaced_rooms', 0)}")
                result.append("")
            
            # Spatial Organization
            if 'spatial_organization' in response:
                spatial = response['spatial_organization']
                result.append(f"🏢 SPATIAL ORGANIZATION")
                result.append(f"Total Rooms: {spatial.get('room_count', 0)}")
                result.append(f"Levels: {len(spatial.get('levels', []))}")
                if spatial.get('levels'):
                    result.append("Levels by elevation:")
                    for level in spatial['levels'][:5]:  # Show first 5 levels
                        elev = level.get('elevation', 'Unknown')
                        if isinstance(elev, (int, float)):
                            result.append(f"  {level.get('name', 'Unnamed')}: {elev:.2f}")
                        else:
                            result.append(f"  {level.get('name', 'Unnamed')}: {elev}")
                result.append("")
            
            # Documentation
            if 'documentation' in response:
                doc_info = response['documentation']
                result.append("📐 DOCUMENTATION")
                result.append(f"Total Views: {doc_info.get('total_views', 0)}")
                result.append(f"Sheets: {doc_info.get('sheets_count', 0)}")
                if 'view_breakdown' in doc_info:
                    vb = doc_info['view_breakdown']
                    result.append("View Types:")
                    for view_type, count in vb.items():
                        if count > 0:
                            result.append(f"  {view_type.replace('_', ' ').title()}: {count}")
                result.append("")
            
            # Linked Models
            if 'linked_models' in response:
                links = response['linked_models']
                result.append(f"🔗 LINKED MODELS: {links.get('count', 0)}")
                if links.get('models'):
                    for link in links['models'][:3]:  # Show first 3 links
                        status = "✅" if link.get('is_loaded') else "❌"
                        result.append(f"  {status} {link.get('name', 'Unknown')} ({link.get('status', 'Unknown')})")
            
            return "\n".join(result)
        
        return str(response)