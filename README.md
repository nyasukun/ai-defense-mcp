# Cisco AI Defense MCP Server

This project implements a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for the **Cisco AI Defense Management API**. It empowers AI coding assistants (like Cursor, Claude Desktop) to proactively secure AI applications by injecting guardrails, monitoring events, and running validations directly from the chat interface.

## 📚 API Reference

This server interfaces with the following Cisco APIs:

-   **[AI Defense Management API](https://developer.cisco.com/docs/ai-defense-management/introduction/)** (Customer Login Required)
    -   Used for configuring Applications, Connections, Policies, and retrieving Events.
-   **[AI Defense Inspection API](https://developer.cisco.com/docs/ai-defense/introduction/)**
    -   Used for the actual inspection of chat traffic (referenced in generated client code).

---

## ✨ Features

-   **🛡️ Automated Guardrails Setup**:
    -   One-shot tool to create an Application, Connection, and associate Policies.
    -   Handles duplicate resources intelligently (e.g., reusing existing Apps/Connections).
    -   Generates Python client code snippets ready for integration.
-   **🚨 Event Monitoring**:
    -   Retrieve recent security events.
    -   Inspect detailed event payloads and conversation history.
-   **✅ AI Validation**:
    -   Trigger validation scans against LLM endpoints (external or internal).
    -   **OpenAI Support**: Auto-configures templates for OpenAI endpoints.
    -   **System Prompt Injection**: Validates how models behave under specific system prompts.

---

## 🚀 Installation & Setup

### Prerequisites
-   Python 3.10+
-   Cisco AI Defense Management API Key

### Quick Start

1.  **Clone and Setup**:
    ```bash
    git clone <repository-url>
    cd ai-defense-mcp
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Copy `.env.example` to `.env` and set your API key:
    ```bash
    cp .env.example .env
    ```
    
    Edit `.env`:
    ```ini
    AIC_MANAGEMENT_API_KEY=your_management_api_key_here
    # Optional: OPENAI_API_KEY=... (needed only if you run local validation tests against OpenAI)
    ```

---

## 🛠️ Usage with MCP Clients (e.g., Cursor)

### Configuration
Add the server to your Cursor MCP settings (`~/.cursor/mcp.json` or via UI):

```json
{
  "mcpServers": {
    "ai-defense-mcp": {
      "command": "/absolute/path/to/ai-defense-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/ai-defense-mcp",
      "env": {
        "AIC_MANAGEMENT_API_KEY": "your_key_here" 
      }
    }
  }
}
```
*Note: Setting `cwd` is critical for loading `.env` correctly.*

### Available Tools

| Tool | Description | Key Arguments |
| :--- | :--- | :--- |
| `setup_ai_defense_guardrails` | Configures protection resources (App, Connection, Policy). | `application_name`, `description`, `target_system_description`, `policy_name` |
| `start_ai_validation` | Starts a security scan/validation job. | `model_endpoint`, `validation_scan_name`, `headers`, `system_prompt`, `model_request_template`, `model_response_json_path` |
| `get_ai_validation_status` | Checks status of a validation job. | `task_id` |
| `get_ai_defense_events` | Lists security events. | `limit`, `offset` |
| `get_ai_defense_event_details` | Gets event details & conversation. | `event_id`, `include_conversation` |

### 💡 Example Prompts

**1. Setting up Guardrails**
> "Protect this chat application. The app name is 'finance-bot-v1'."
> _(Agent creates resources and provides a Python code snippet to use)_

**2. Running AI Validation (OpenAI)**
> "Run a security validation against https://api.openai.com/v1/chat/completions. Use my OpenAI key in headers."
> _(Agent asks for the key or uses provided headers, auto-configures the template, and starts the scan)_

**3. Checking Security Events**
> "Show me the latest blocked attacks."

---

## 🤖 Coding Instructions for Future Agents

If you are an AI Agent modifying this codebase, please adhere to the following guidelines:

1.  **API Schema Compliance**:
    -   Always verify request payloads against the [Official API Docs](https://developer.cisco.com/docs/ai-defense-management/introduction/).
    -   Be careful with nested objects (e.g., `header` lists in Validation API).

2.  **Tool Definitions**:
    -   When adding new tools, use descriptive `description` fields. These act as the "System Prompt" for the calling model.
    -   Expose necessary configurations (like `headers` or `system_prompt`) as arguments to let the user/model provide context.

3.  **Error Handling**:
    -   The AI Defense API may return `409 Conflict` (duplicates) or `400 Bad Request` (schema errors).
    -   Handle these gracefully (e.g., retry with a new name, or fallback to default values) as seen in `src/tools/guardrails.py`.

4.  **Validation Logic**:
    -   The `start_ai_validation` tool has special logic for OpenAI.
    -   To ensure stability, templates are minified (`json.dumps`) before sending. Maintain this pattern for complex JSON strings.

5.  **Environment**:
    -   Use `dotenv` for local development but respect passed environment variables in production.

---

## 🧪 Verification

To manually verify the core logic without MCP:
```bash
python test_guardrails_logic.py
```
*(Tests connection creation, policy association, and client code generation)*



## License
[License Name]
