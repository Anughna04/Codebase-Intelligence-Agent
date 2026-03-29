from typing import TypedDict, Annotated, Sequence
from operator import add
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    query: str
    route: str  # ROUTE_RAG, ROUTE_MCP, ROUTE_BOTH
    context: Annotated[list[str], add] # Append-only context from RAG or MCP
    messages: Annotated[Sequence[BaseMessage], add] # Chat history for tools if needed
    analysis: str
    bugs: str
    architecture: str
    final_report: str
