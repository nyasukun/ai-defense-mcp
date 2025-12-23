
import httpx
from typing import Optional, Dict, List, Any
from src.config import Config

class AIDefenseClient:
    """
    Async client for the Cisco AI Defense Management API.
    
    Handles authentication, request execution, and interaction with various
    endpoints (Applications, Connections, Policies, Events, Validation).
    """
    def __init__(self):
        """Initializes the client, verifying API key presence."""
        Config.validate()
        self.base_url = Config.AIC_MANAGEMENT_API_URL
        self.headers = {
            "X-Cisco-AI-Defense-Tenant-API-Key": Config.AIC_MANAGEMENT_API_KEY,
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, endpoint: str, json: Optional[Dict] = None, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=self.headers, json=json, params=params)
            response.raise_for_status()
            return response.json()

    # Application Management
    async def create_application(self, name: str, description: str, connection_type: str = "API") -> Dict:
        """Creates a new application."""
        payload = {
            "application_name": name,
            "description": description,
            "connection_type": connection_type
        }
        return await self._request("POST", "/applications", json=payload)

    async def list_applications(self, limit: int = 100, offset: int = 0) -> Dict:
        """Lists applications."""
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", "/applications", params=params)

    # Connection Management
    async def create_connection(self, application_id: str, name: str, connection_type: str = "API") -> Dict:
        """Creates a new connection for an application."""
        payload = {
            "application_id": application_id,
            "connection_name": name,
            "connection_type": connection_type
        }
        return await self._request("POST", "/connections", json=payload)

    async def generate_connection_key(self, connection_id: str, name: str, expiry: str) -> Dict:
        """Generates an API key for a connection."""
        payload = {
            "op": "GENERATE_API_KEY",
            "key": {
                "name": name,
                "expiry": expiry
            }
        }
        return await self._request("POST", f"/connections/{connection_id}/keys", json=payload)

    # Policy Management
    async def list_policies(self, limit: int = 100, offset: int = 0) -> Dict:
        """Lists all policies."""
        params = {"limit": limit, "offset": offset}
        return await self._request("GET", "/policies", params=params)

    async def update_policy_connections(self, policy_id: str, connections_to_associate: List[str]) -> Dict:
        """Associates connections with a policy."""
        payload = {
            "connections_to_associate": connections_to_associate
        }
        return await self._request("POST", f"/policies/{policy_id}/connections", json=payload)

    # Events
    async def list_events(self, limit: int = 20, offset: int = 0) -> Dict:
        """Lists security events."""
        payload = {
            "limit": limit,
            "offset": offset
        }
        # Note: The spec says POST for listing events
        return await self._request("POST", "/events", json=payload)

    async def get_event_details(self, event_id: str) -> Dict:
        """Gets details of a specific event."""
        return await self._request("GET", f"/events/{event_id}")

    async def get_event_conversation(self, event_id: str) -> Dict:
        """Gets conversation history for an event."""
        return await self._request("GET", f"/events/{event_id}/conversation")

    # AI Validation
    async def start_ai_validation(self, model_endpoint_url: str, validation_scan_name: str, application_id: Optional[str] = None, headers: Optional[Dict[str, str]] = None, model_request_template: Optional[str] = None, model_provider: Optional[str] = None, model_response_json_path: Optional[str] = None) -> Dict:
        """Starts an AI validation job."""
        payload = {
            "validation_scan_name": validation_scan_name,
            "model_endpoint_url_model_id": model_endpoint_url,
            "asset_type": "APPLICATION" if application_id else "EXTERNAL",
        }
        if application_id:
            payload["application_id"] = application_id
            
        if headers:
            # Transform dict headers to list of key-value objects as per API spec
            payload["headers"] = [{"key": k, "value": v} for k, v in headers.items()]
            
        if model_request_template:
            payload["model_request_template"] = model_request_template
            
        if model_provider:
             payload["model_provider"] = model_provider

        if model_response_json_path:
            payload["model_response_json_path"] = model_response_json_path

        # Re-checking spec for start validation
        # The spec showed /ai-validation/start taking a body. 
        # I'll need to be careful with the payload structure.
        # Based on v1StartAiValidationRequest in spec:
        # It needs `validation_scan_name`, `model_endpoint_url_model_id`, etc.
        
        return await self._request("POST", "/ai-validation/start", json=payload)

    async def get_ai_validation_job(self, task_id: str) -> Dict:
        """Gets the status of an AI validation job."""
        return await self._request("GET", f"/ai-validation/job/{task_id}")
