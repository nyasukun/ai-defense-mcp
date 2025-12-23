
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.api_client import AIDefenseClient

async def setup_ai_defense_guardrails(
    application_name: str,
    description: str = "Protecting AI Chat Application",
    target_system_description: Optional[str] = None,
    policy_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sets up AI Defense guardrails for an application.

    Workflow:
    1. Create (or resolve existing) Application.
    2. Create (or resolve existing) Connection.
    3. Generate a Runtime API Key for the connection.
    4. Associate the connection with a specified or default Policy.
    5. Generate a client-side code snippet for integration.
    
    Args:
        application_name: Name of the application to protect.
        description: Description of the application.
        target_system_description: Description of the target LLM system.
        policy_name: (Optional) Name of a specific policy to bind.
        
    Returns:
        Dictionary containing setup details (IDs, Keys) and the client code snippet.
    """
    client = AIDefenseClient()

    # 1. Create Application
    print(f"Creating application: {application_name}")
    app_id = None
    try:
        app_resp = await client.create_application(application_name, description)
        app_id = app_resp.get("application_id")
    except Exception as e:
        # Check for 409 Conflict OR 400 Bad Request (API might return 400 for duplicates)
        if hasattr(e, 'response') and e.response.status_code in (400, 409):
            print(f"Application '{application_name}' creation failed ({e.response.status_code}). Checking if it exists...")
            # Failed to create because it exists. Find it.
            # Loop through pages to find the application
            limit = 100
            offset = 0
            while True:
                print(f"Searching for existing application '{application_name}' (offset: {offset})...")
                list_resp = await client.list_applications(limit=limit, offset=offset)
                apps = list_resp.get("applications", {}).get("items", [])
                paging = list_resp.get("applications", {}).get("paging", {})
                
                if not apps:
                    break
                    
                for app in apps:
                    if app.get("application_name") == application_name:
                        app_id = app.get("application_id")
                        print(f"Found existing application ID: {app_id}")
                        break
                
                if app_id:
                    break
                
                # Check if we need to fetch more
                total = paging.get("total", 0)
                if offset + len(apps) >= total:
                    break
                
                offset += limit
            
            if not app_id:
                return {"error": f"Application '{application_name}' already exists but could not be found in list.", "details": str(e)}
        else:
            return {"error": f"Failed to create application: {e}", "details": str(e)}

    if not app_id:
        return {"error": "Failed to resolve application ID", "details": "Unknown error"}

    # 2. Create Connection
    # User requested to ensure we get an API key, so if default connection exists, create a new one.
    import time
    connection_name = f"{application_name}-connection"
    print(f"Creating connection with name: {connection_name}")
    
    conn_id = None
    try:
        conn_resp = await client.create_connection(app_id, connection_name)
        conn_id = conn_resp.get("connection_id")
    except Exception as e:
        # If conflict or fails, try with timestamp to ensure uniqueness and get a new key
        print(f"Connection creation failed ({e}). Trying with unique suffix...")
        unique_suffix = int(time.time())
        connection_name = f"{application_name}-conn-{unique_suffix}"
        try:
            conn_resp = await client.create_connection(app_id, connection_name)
            conn_id = conn_resp.get("connection_id")
        except Exception as e2:
             return {"error": f"Failed to create connection (retried with {connection_name})", "details": str(e2)}

    if not conn_id:
         return {"error": "Failed to resolve connection ID", "details": "Unknown error"}

    # 3. Generate Runtime API Key
    print(f"Generating runtime key for connection: {conn_id}")
    # Set expiry to 1 year from now
    expiry = (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z"
    key_resp = await client.generate_connection_key(conn_id, "Runtime Key", expiry)
    api_key = key_resp.get("key", {}).get("api_key") # Extracted from nested 'key' object

    # 4. Associate Policies
    print("Fetching policies...")
    # Limit fetch and look for a suitable default
    policies_resp = await client.list_policies(limit=100) 
    policies = policies_resp.get("policies", {}).get("items", [])
    
    target_policy_id = None
    target_policy_name = None
    
    if policy_name:
        print(f"Searching for policy matching: {policy_name}")
        for policy in policies:
            # Case-insensitive substring match or exact match preferred
            p_name = policy.get("policy_name", "")
            if policy_name.lower() in p_name.lower():
                target_policy_id = policy.get("policy_id")
                target_policy_name = p_name
                print(f"Found matching policy: {target_policy_name} ({target_policy_id})")
                break
        
        if not target_policy_id:
            available_policies = ", ".join([p.get("policy_name") for p in policies[:10]])
            return {
                "status": "warning",
                "application_id": app_id,
                "connection_id": conn_id,
                "runtime_api_key": api_key, 
                "message": f"Could not find policy matching '{policy_name}'. Available policies: {available_policies}...",
                "available_policies": [p.get("policy_name") for p in policies]
            }

    else:
        # No policy name provided, try to list typical options or fallback
        # improved logic: try to find a policy named "Default" first
        for policy in policies:
            if policy.get("policy_name") == "Default":
                target_policy_id = policy.get("policy_id")
                target_policy_name = "Default"
                print(f"Found 'Default' policy: {target_policy_id}")
                break
                
        # Fallback: Use the very first policy if Default is not found (and list is not empty)
        if not target_policy_id and policies:
            target_policy_id = policies[0].get("policy_id")
            target_policy_name = policies[0].get("policy_name")
            print(f"Default policy not found. Using first available policy: {target_policy_name} ({target_policy_id})")

    if target_policy_id:
        print(f"Associating connection to policy: {target_policy_id}")
        await client.update_policy_connections(target_policy_id, [conn_id])
        policy_message = f"Associated with policy '{target_policy_name}'."
    else:
        print("No policies found to associate.")
        policy_message = "No policies found. Connection created but not associated with any policy."
    
    
    # Generate client snippet (Inspection API format)
    # Note: Using US region as example default, user might need to change based on actual region.
    # Payload structure based on ChatInspectRequest
    client_snippet = f"""
import httpx

async def call_ai_defense_inspection(user_message: str):
    # Endpoint for Chat Inspection (Global/US) - Change to 'eu' or 'ap' subdomain if needed
    url = "https://us.api.inspect.aidefense.security.cisco.com/api/v1/inspect/chat" 
    
    headers = {{
        "X-Cisco-AI-Defense-API-Key": "{api_key}",
        "Content-Type": "application/json"
    }}
    
    # Payload matching ChatInspectRequest schema
    payload = {{
        "messages": [
            {{
                "role": "user", 
                "content": user_message
            }}
        ],
        "metadata": {{
            "user": "end-user-id", # Optional: Map to actual user ID
            "src_app": "{application_name}"
        }}
    }}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Returns InspectResponse (classifications, is_safe, severity, etc.)
        return response.json()
"""

    return {
        "status": "success",
        "application_id": app_id,
        "connection_id": conn_id,
        "runtime_api_key": api_key, 
        "message": "Guardrails setup complete. Use the code snippet below to integrate.",
        "client_code_snippet": client_snippet
    }
