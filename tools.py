from langchain_core.tools import tool

# --- EXPANDED MOCK DATABASE ---
MOCK_DB = {
    "users": {
        "alice@dev.com": {"id": "U-101", "role": "Admin", "active_servers": ["SRV-01", "SRV-02"]},
        "bob@dev.com": {"id": "U-102", "role": "Developer", "active_servers": ["SRV-03"]}
    },
    "servers": {
        "SRV-01": {"status": "Running", "cpu": "45%", "cost_per_hour": "$0.05"},
        "SRV-02": {"status": "Failing", "error": "Out of Memory", "cost_per_hour": "$0.08"},
        "SRV-03": {"status": "Stopped", "cpu": "0%", "cost_per_hour": "$0.02"}
    }
}

@tool
def get_user_info(email: str) -> str:
    """Retrieve user details and their assigned server IDs using their email address."""
    user = MOCK_DB["users"].get(email.lower())
    return f"User Found: {user}" if user else "Error: User email not found."

@tool
def get_server_status(server_id: str) -> str:
    """Check the health, CPU usage, and billing cost of a specific server."""
    server = MOCK_DB["servers"].get(server_id.upper())
    return f"Server {server_id} Status: {server}" if server else "Error: Server not found."

@tool
def restart_server(server_id: str) -> str:
    """Trigger a restart for a failing server."""
    server_id = server_id.upper()
    if server_id in MOCK_DB["servers"]:
        MOCK_DB["servers"][server_id]["status"] = "Running (Restarted)"
        MOCK_DB["servers"][server_id]["error"] = "None"
        return f"SUCCESS: Restart command sent to {server_id}."
    return "ERROR: Cannot restart. Server ID unknown."

# Export the list of tools for LangGraph
local_tools = [get_user_info, get_server_status, restart_server]
