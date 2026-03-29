import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.state import AgentState
from core.vector_db import GlobalCodeContext
from core.mcp_adapter import get_mcp_tools
from prompts.system_prompts import (
    PLANNER_SYSTEM_PROMPT,
    ANALYZER_SYSTEM_PROMPT,
    DEBUGGER_SYSTEM_PROMPT,
    ARCHITECTURE_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
)

# Shared LLM Instance
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)

def planner_node(state: AgentState) -> dict:
    """Plans retrieval strategy: RAG, MCP, or BOTH based on the query."""
    llm = get_llm()
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=state["query"])
    ]
    response = llm.invoke(messages)
    content = response.content.strip()
    
    route = "ROUTE_RAG"
    if "ROUTE_MCP" in content:
        route = "ROUTE_MCP"
    elif "ROUTE_BOTH" in content:
        route = "ROUTE_BOTH"
        
    print(f"\n[Planner Agent] Routing execution to: {route}")
    return {"route": route}

def retriever_node(state: AgentState) -> dict:
    """Invokes semantic vector DB on the current repo structure."""
    print("[Retriever Agent] Re-indexing workspace and retrieving semantic code...")
    ctx = GlobalCodeContext(os.getcwd())
    # User constraint: rebuild index exactly for every query
    ctx.build_index_for_repo() 
    docs = ctx.search(state["query"], top_k=5)
    
    contexts = []
    for d in docs:
        contexts.append(f"### [RAG Rerieval] File: {d.metadata['file_path']} ({d.metadata['entity_name']})\n{d.page_content}\n")
    return {"context": contexts}

async def mcp_tool_node(state: AgentState) -> dict:
    """Uses LLM tool calling to interact with GitHub MCP Tools explicitly typed."""
    print("[MCP Tool Agent] Booting interactive session with Github...")
    llm = get_llm()
    tools = get_mcp_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    prompt = f"""You possess external tools to interact with GitHub (read files, get PR diffs, commits, issues). 
Given the user's query, determine which tool to call and pass the arguments.
If you do not need context beyond current knowledge, do not call any tools. Return the output of the tools or a summary."""
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=state["query"])
    ]
    # We will trigger the tool and append to context. To keep it simple, LangChain tool executor manually:
    response = await llm_with_tools.ainvoke(messages)
    
    mcp_contexts = []
    if response.tool_calls:
        print(f"[MCP Tool Agent] LLM requested {len(response.tool_calls)} external tools.")
        for tcall in response.tool_calls:
            for tool in tools:
                if tool.name == tcall["name"]:
                    print(f"   -> Executing: {tool.name}({tcall['args']})")
                    try:
                        res = await tool.ainvoke(tcall["args"])
                        data = f"### [MCP Context: {tool.name}]\n{res}\n"
                        mcp_contexts.append(data)
                    except Exception as e:
                        mcp_contexts.append(f"### [MCP Failure: {tool.name}]\n{str(e)}\n")
    else:
        print("[MCP Tool Agent] LLM didn't request any github tools.")
        
    return {"context": mcp_contexts}

def analyzer_node(state: AgentState) -> dict:
    print("[Analyzer Agent] Processing relationships and behavior...")
    llm = get_llm()
    agg_context = "\n".join(state["context"])
    msgs = [SystemMessage(content=ANALYZER_SYSTEM_PROMPT), 
            HumanMessage(content=f"Context:\n{agg_context}\n\nQuery:\n{state['query']}")]
    res = llm.invoke(msgs)
    return {"analysis": res.content}

def debugger_node(state: AgentState) -> dict:
    print("[Debugger Agent] Hunting for edge cases/bugs...")
    llm = get_llm()
    agg_context = "\n".join(state["context"])
    msgs = [SystemMessage(content=DEBUGGER_SYSTEM_PROMPT),
            HumanMessage(content=f"Analysis:\n{state.get('analysis', '')}\n\nContext:\n{agg_context}")]
    res = llm.invoke(msgs)
    return {"bugs": res.content}

def architecture_node(state: AgentState) -> dict:
    print("[Architecture Agent] Reviewing system design and constraints...")
    llm = get_llm()
    agg_context = "\n".join(state["context"])
    msgs = [SystemMessage(content=ARCHITECTURE_SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{agg_context}\n\nQuery:\n{state['query']}")]
    res = llm.invoke(msgs)
    return {"architecture": res.content}

def synthesizer_node(state: AgentState) -> dict:
    print("[Synthesizer Agent] Generating final comprehensive report...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7) # slightly more creative formats here
    msgs = [
        SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
        HumanMessage(content=f"Query: {state['query']}\n\nAnalysis:\n{state['analysis']}\n\nBugs:\n{state['bugs']}\n\nArch:\n{state['architecture']}")
    ]
    res = llm.invoke(msgs)
    return {"final_report": res.content}
