import os
import asyncio
from dotenv import load_dotenv
from gradient_adk import entrypoint
from langchain_gradient import ChatGradient
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

# MCP Imports
from mcp import StdioServerParameters
from langchain_mcp_adapters.client import MultiServerMCPClient

from state import AgentState

# 1. Setup Environment
load_dotenv()

async def run_mcp_agent(user_input: str, thread_id: str):
    # Retrieve the API Token for the MCP Server
    do_token = os.getenv("DIGITALOCEAN_API_TOKEN")
    
    # 2. Configure the DigitalOcean MCP Server (Node.js based)
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@digitalocean/mcp", "--services", "apps,droplets,databases"],
        env={**os.environ, "DIGITALOCEAN_API_TOKEN": do_token}
    )

    # 3. Establish the MCP Connection
    # We use 'async with' to ensure the background Node process closes correctly
    async with MultiServerMCPClient({"digitalocean": server_params}) as client:
        
        # This dynamically fetches 30+ real DigitalOcean tools!
        mcp_tools = await client.get_tools()

        # 4. Define the AI Thinking Node
        def call_model(state: AgentState):
            llm = ChatGradient(
                model="llama3.3-70b-instruct",
                api_key=os.getenv("GRADIENT_MODEL_ACCESS_KEY", "missing_key")
            )
            llm_with_tools = llm.bind_tools(mcp_tools)
            
            sys_msg = SystemMessage(content=(
                "You are the official DigitalOcean Cloud Agent. "
                "You have direct access to manage real user infrastructure via MCP. "
                "Current time: March 2026. Be professional and safe."
            ))
            
            response = llm_with_tools.invoke([sys_msg] + state["messages"])
            return {"messages": [response]}

        # 5. Build the LangGraph
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(mcp_tools))

        workflow.add_edge(START, "agent")
        
        # Router: If the AI wants to use a DO tool, go to 'tools', else END
        workflow.add_conditional_edges(
            "agent",
            lambda x: "tools" if x["messages"][-1].tool_calls else END
        )
        workflow.add_edge("tools", "agent")

        # Compile with persistent thread memory
        app = workflow.compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": thread_id}}
        
        # 6. Run the agent asynchronously
        result = await app.ainvoke(
            {"messages": [HumanMessage(content=user_input)]}, 
            config
        )
        return result["messages"][-1].content

@entrypoint
def main(payload: dict) -> dict:
    # This is the "front door" of your DigitalOcean Agent
    user_input = payload.get("prompt", "Hello")
    thread_id = payload.get("thread_id", "mcp-demo-thread")
    
    # Use asyncio.run to handle the 3.14/3.12 bridge
    final_response = asyncio.run(run_mcp_agent(user_input, thread_id))
    
    return {
        "response": final_response,
        "thread_id": thread_id
    }
