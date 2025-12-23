
import asyncio
import os
import sys
from src.tools.guardrails import setup_ai_defense_guardrails
from src.api_client import AIDefenseClient

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

async def run_scenario():
    print("=== Starting Scenario Test ===")
    
    # 1. Test Listing Policies first to see what we are dealing with
    client = AIDefenseClient()
    print("\n--- Listing Policies ---")
    try:
        policies_resp = await client.list_policies()
        policies = policies_resp.get("policies", {}).get("items", [])
        print(f"Found {len(policies)} policies.")
        for p in policies:
            print(f"- {p.get('policy_name')} (ID: {p.get('policy_id')})")
    except Exception as e:
        print(f"Failed to list policies: {e}")
        return

    # 1.5 Try to create a policy (Undocumented?)
    print("\n--- Testing Policy Creation (POST /policies) ---")
    try:
        new_policy_payload = {
            "name": f"ValidationPolicy-{os.urandom(4).hex()}",
            "description": "Created via MCP Debug",
            "status": "active"
        }
        # Manually calling private request method to bypass client method which doesn't exist
        resp = await client._request("POST", "/policies", json=new_policy_payload)
        print("Create Policy Result:", resp)
    except Exception as e:
        print(f"Failed to create policy: {e}")
        if hasattr(e, 'response'):
             print(f"Response Status: {e.response.status_code}")
             print(f"Response Text: {e.response.text}")

    # 2. Run the main tool logic with Policy Name
    print("\n--- Running setup_ai_defense_guardrails (Testing 409 Conflict) ---")
    # Use a fixed name to trigger conflict on second run (or if it already exists)
    app_name = "ConflictTestApp-v1" 
    print(f"Target App Name: {app_name}")
    
    # Pre-create the app manually to ensure it exists (optional, but good for reliable test)
    try:
        print("Pre-creating app to ensure conflict...")
        await client.create_application(app_name, "Pre-created for testing")
    except Exception as e:
        print(f"Pre-creation result: {e}")
        if hasattr(e, 'response'):
             print(f"Response Text: {e.response.text}")


    # Debug: List all apps to see if we can see it
    print("\n--- Listing Applications ---")
    list_resp = await client.list_applications(limit=100)
    print(f"RAW LIST RESPONSE: {list_resp}")
    apps = list_resp.get("applications", {}).get("items", [])
    found = False
    for app in apps:
        print(f"- {app.get('application_name')} ({app.get('application_id')})")
        if app.get("application_name") == app_name:
            found = True
    print(f"--- 'ConflictTestApp_v1' Found in list? {found} ---\n")

    try:
        # Pass policy_name="Default"
        target_p = "Default"
        if policies:
            target_p = policies[0].get("policy_name")
            
        print(f"Attempting to match policy: {target_p}")
        result = await setup_ai_defense_guardrails(app_name, policy_name=target_p)
        
        import json
        print("\n=== Success ===")
        print(f"Result Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        if "client_code_snippet" in result:
            print("\n--- Generated Client Code Snippet ---")
            print(result["client_code_snippet"])
            print("-------------------------------------")
        # print(json.dumps(result, indent=2)) # optional full dump
    except Exception as e:
        print("\n=== Failed ===")
        print(f"Error during setup: {e}")
        # If it's an HTTP error, it might have response info
        if hasattr(e, 'response'):
             print(f"Response Status: {e.response.status_code}")
             print(f"Response Body: {e.response.text}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("AIC_MANAGEMENT_API_KEY"):
        print("Error: AIC_MANAGEMENT_API_KEY is not set in .env")
        sys.exit(1)
        
    asyncio.run(run_scenario())
