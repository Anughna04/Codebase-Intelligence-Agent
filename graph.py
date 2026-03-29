from langgraph.graph import StateGraph, START, END
from core.state import AgentState
from agents.nodes import (
    planner_node,
    retriever_node,
    mcp_tool_node,
    analyzer_node,
    debugger_node,
    architecture_node,
    synthesizer_node
)

def route_from_planner(state: AgentState) -> str:
    route = state["route"]
    if route == "ROUTE_RAG":
        return "retriever"
    elif route == "ROUTE_MCP":
        return "mcp_tools"
    else:
        return "retriever"

def route_after_retriever(state: AgentState) -> str:
    if state["route"] == "ROUTE_BOTH":
        return "mcp_tools"
    return "analyzer"

def create_review_graph():
    workflow = StateGraph(AgentState)
    
    # 1. Add all nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("mcp_tools", mcp_tool_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("debugger", debugger_node)
    workflow.add_node("architecture", architecture_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # 2. Add edges
    workflow.add_edge(START, "planner")
    
    workflow.add_conditional_edges(
        "planner", 
        route_from_planner, 
        {
            "retriever": "retriever", 
            "mcp_tools": "mcp_tools"
        }
    )
    
    workflow.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {
            "mcp_tools": "mcp_tools",
            "analyzer": "analyzer"
        }
    )
    
    workflow.add_edge("mcp_tools", "analyzer")
    
    # Parallelize or serialize analyzer -> debugger -> architecture
    # Keep it simple: Serial funnel to avoid Complex joins
    workflow.add_edge("analyzer", "debugger")
    workflow.add_edge("debugger", "architecture")
    workflow.add_edge("architecture", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()
