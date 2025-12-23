
from typing import Dict, Any, Optional
from src.api_client import AIDefenseClient

async def start_ai_validation(
    validation_scan_name: str,
    model_endpoint: str,
    test_suite: str = "default",  # Placeholder for future config
    application_id: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    model_request_template: Optional[str] = None,
    model_provider: Optional[str] = None,
    model_response_json_path: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Starts an AI validation job against a specific model endpoint.
    
    Features:
    - Auto-configures templates for OpenAI endpoints.
    - Supports system prompt injection for testing prompt injection defenses.
    - Requires valid headers (e.g., Authorization) for external models.

    Args:
        validation_scan_name: Name of the scan/test run.
        model_endpoint: Full URL of the LLM endpoint (e.g., https://api.openai.com/v1/...).
        application_id: (Optional) AI Defense Application ID to associate with.
        headers: (Optional) Headers needed to call the model_endpoint.
        model_request_template: (Optional) JSON template for the request body.
        model_provider: (Optional) Name of the provider.
        model_response_json_path: (Optional) JSONPath to extract the response text.
        system_prompt: (Optional) System prompt to inject into the test.

    Returns:
        Dictionary containing the `task_id`.
    """
    client = AIDefenseClient()
    
    
    # Auto-detect OpenAI configuration if not provided
    if "openai.com" in model_endpoint or "gpt" in model_endpoint.lower():
        if not model_request_template:
            # Standard OpenAI Chat Completions template with model parameter as required by OpenAI
            import json
            template_obj = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt if system_prompt else "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": "{{prompt}}"
                    }
                ]
            }
            model_request_template = json.dumps(template_obj)

        if not model_provider:
             model_provider = "OpenAI"
        
        if not model_response_json_path:
            model_response_json_path = "choices.0.message.content"

    # Note: We are passing model_endpoint into model_endpoint_url_model_id
    response = await client.start_ai_validation(
        model_endpoint, 
        validation_scan_name, 
        application_id, 
        headers, 
        model_request_template, 
        model_provider,
        model_response_json_path
    )
    return response

async def get_ai_validation_status(task_id: str) -> Dict[str, Any]:
    """
    Checks the status of an AI validation job.
    """
    client = AIDefenseClient()
    response = await client.get_ai_validation_job(task_id)
    return response
