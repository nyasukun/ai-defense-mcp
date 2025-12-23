
from typing import Dict, Any, Optional
from src.api_client import AIDefenseClient

async def get_ai_defense_events(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """
    Retrieves a paginated list of security events from AI Defense.
    
    Args:
        limit: Max number of events to return.
        offset: Pagination offset.
        
    Returns:
        JSON response containing the list of events and paging info.
    """
    client = AIDefenseClient()
    response = await client.list_events(limit, offset)
    return response

async def get_ai_defense_event_details(event_id: str, include_conversation: bool = False) -> Dict[str, Any]:
    """
    Retrieves full details of a specific security event.
    
    Args:
        event_id: The ID of the event to inspect.
        include_conversation: If True, fetches related chat conversation history.
        
    Returns:
        Dictionary with 'event' and optional 'conversation' keys.
    """
    client = AIDefenseClient()
    details = await client.get_event_details(event_id)
    
    result = {"event": details}
    
    if include_conversation:
        conversation = await client.get_event_conversation(event_id)
        result["conversation"] = conversation
        
    return result
