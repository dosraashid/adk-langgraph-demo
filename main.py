import os
from dotenv import load_dotenv
from gradient_adk import entrypoint
from langchain_gradient import ChatGradient
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage

from state import AgentState
from tools import local_tools

# Load API keys from .env
load_dotenv()

# 1. Initialize DO Serverless Inference
# It dynamically reads GRADIENT_MODEL_ACCESS_KEY from your .env file
llm = ChatGradient(
    model="llama3.3-70b-instruct",
    api_key=os.getenv("GRADIENT_MODEL_ACCESS_KEY")
)
llm_with_tools = llm.bind_tools(local_tools)

# 2. Define the Agent Logic
def call_model(state: AgentState):
    memory_context = "\n".join(state.get("shared_memory", ["No prior history."]))
    sys_msg = SystemMessage(content=(
        "You are a DigitalOcean Cloud DevOps Assistant. "
        "Use tools to look up users by email, check their servers, and restart failing ones. "
        f"\n[LONG-TERM MEMORY]: {memory_context}"
    ))
    response = llm_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}

# 3. Build the LangGraph Workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(local_tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", lambda x: "tools" if x["messages"][-1].tool_calls else END)
workflow.add_edge("tools", "agent")

# Attach Persistence
app = workflow.compile(checkpointer=MemorySaver())

# 4. The DigitalOcean ADK Entrypoint
@entrypoint
def main(payload: dict) -> dict:
    user_input = payload.get("prompt", "Hello")
    thread_id = payload.get("thread_id", "default-thread")
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the graph
    result = app.invoke({"messages": [HumanMessage(content=user_input)]}, config)
    
    return {
        "response": result["messages"][-1].content,
        "thread_id": thread_id
    }
