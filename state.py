import operator
from typing import Annotated, TypedDict, List
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    # LangGraph standard message history
    messages: Annotated[List[AnyMessage], operator.add]
    
    # Custom memory: Facts the agent extracts about the user
    shared_memory: Annotated[List[str], operator.add]
