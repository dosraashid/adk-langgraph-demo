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

load_dotenv()

async def run_agent_with_mcp(user_input: str, thread_id: str):
    # 1. Configure the Official DO MCP Server
    # We enable specific services (apps, droplets, databases) to keep context lean
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@digitalocean/mcp", "--services", "apps,droplets,databases"],
        env={**os.environ, "DIGITALOCEAN_API_TOKEN": os.getenv("DIGITALOCEAN_API_TOKEN")}
    )

    # 2. Open the MCP connection
    async with MultiServerMCPClient({"digitalocean": server_params}) as client:
        # Dynamically fetch all DO tools
        mcp_tools = await client.get_tools()

        # 3. Define the AI Brain
        def call_model(state):
            llm = ChatGradient(
                model="llama3.3-70b-instruct",
                api_key=os.getenv("GRADIENT_MODEL_ACCESS_KEY")
            )
            # Bind all discovered MCP tools to the LLM
            llm_with_tools = llm.bind_tools(mcp_tools)
            
            sys_msg = SystemMessage(content=(
                "You are an official DigitalOcean Cloud Assistant. "
                "You have direct access to the user's infrastructure via MCP. "
                "Be concise, and always confirm before performing destructive actions."
            ))
            
            response = llm_with_tools.invoke([sys_msg] + state["messages"])
            return {"messages": [response]}

        # 4. Standard LangGraph Orchestration
        workflow = StateGraph(dict) # Using a basic dict for state simplicity here
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(mcp_tools))

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent", 
            lambda x: "tools" if x["messages"][-1].tool_calls else END
        )
        workflow.add_edge("tools", "agent")

        # Compile with persistence
        app = workflow.compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": thread_id}}

        # Execute
        result = await app.ainvoke(
            {"messages": [HumanMessage(content=user_input)]}, 
            config
        )
        return result["messages"][-1].content

@entrypoint
def main(payload: dict) -> dict:
    user_input = payload.get("prompt", "List my apps")
    thread_id = payload.get("thread_id", "mcp-session-1")
    
    # Run the async loop
    response_text = asyncio.run(run_agent_with_mcp(user_input, thread_id))
    
    return {
        "response": response_text,
        "thread_id": thread_id
    }
