# AI-Powered GitHub Code Intelligence & Review System

An enterprise-grade, Multi-Agent AI architecture combining **Retrieval-Augmented Generation (RAG)** and the **Model Context Protocol (MCP)** to intelligently review codebases, spot logical bugs, explain architectures, and query live GitHub data dynamically.

---

## 🏗️ System Architecture

This project is built around **LangGraph** to predictably orchestrate seven specialized AI Agents. Depending on the query space (Local vs Remote GitHub), the system dynamically routes tool usage to minimize hallucination and maximize precision.

```mermaid
graph TD
    classDef llm fill:#4a154b,stroke:#000,stroke-width:2px,color:#fff;
    classDef tool fill:#0052cc,stroke:#000,stroke-width:2px,color:#fff;
    classDef sys fill:#1c2d3d,stroke:#000,stroke-width:2px,color:#fff;

    Start((Query)) --> Planner[Planner Agent<br/>Determines Context Scope]:::llm

    subgraph ContextIngestion["Dynamic Context Generation"]
        Planner --> RAG[Retriever Agent<br/>Vectorize & Search]:::llm
        Planner --> MCP[MCP Tool Agent<br/>GitHub API]:::llm
        Planner --> Both{Hybrid Context}:::llm

        RAG -.-> DB[(Local FAISS DB)]:::sys
        MCP -.-> GH[GitHub Endpoints]:::tool
    end

    RAG --> Analyzer[Analyzer Agent<br/>Maps Logic]:::llm
    MCP --> Analyzer
    Both --> Analyzer

    subgraph AnalysisPhase["Analysis Phase"]
        Analyzer --> Debugger[Debugger Agent<br/>Finds Logic Flaws]:::llm
        Analyzer --> Architect[Architecture Agent<br/>System Design Checks]:::llm
    end

    Debugger --> Synthesizer[Synthesizer Agent<br/>Generates Markdown Report]:::llm
    Architect --> Synthesizer

    Synthesizer --> Finish(((Final Report)))
```

## 🔄 Semantic Workflow Details

Instead of blindly feeding massive text files to an LLM, the local codebase is structurally decomposed using `tree-sitter`. The diagram below illustrates how code is processed before and after prompting.

```mermaid
graph TD
    %% ====== STYLES ======
    classDef llm fill:#4a154b,stroke:#000,stroke-width:2px,color:#fff;
    classDef tool fill:#0052cc,stroke:#000,stroke-width:2px,color:#fff;
    classDef sys fill:#1c2d3d,stroke:#000,stroke-width:2px,color:#fff;

    %% ====== ENTRY ======
    Start((Scenario Input)) --> Init[Initialize State<br/>scenario_X]:::sys
    Init --> Loader[Scenario Loader<br/>Load Data Files]:::sys

    %% ====== ORCHESTRATION ======
    Loader --> Orchestrator[LangGraph Orchestrator<br/>Controls Agent Flow]:::llm

    %% ====== AGENT PIPELINE ======
    subgraph AgentPipeline["Autonomous War Room Agents"]
        direction LR
        DA[Data Analyst]:::llm --> PM[Product Manager]:::llm
        PM --> MKT[Marketing Strategist]:::llm
        MKT --> SRE[SRE / Infra Agent]:::llm
        SRE --> CS[Customer Support Agent]:::llm
        CS --> RISK[Risk Critic]:::llm
    end

    Orchestrator --> DA
    RISK --> Orchestrator

    %% ====== EXECUTION ENGINE ======
    subgraph ExecutionEngine["Agent Execution Engine (Reusable Logic)"]
        direction TB
        Tools[Load Tools / External Data]:::tool
        Prompt[Structured Prompt Builder]:::sys
        LLM((LLaMA 3.2 via Ollama)):::llm
        Parser[Strict JSON Parser<br/>Validation Layer]:::sys

        Tools --> Prompt
        Prompt --> LLM
        LLM --> Parser
    end

    %% Each agent uses execution engine
    DA -.-> Tools
    PM -.-> Tools
    MKT -.-> Tools
    SRE -.-> Tools
    CS -.-> Tools
    RISK -.-> Tools

    %% ====== DECISION ======
    Orchestrator --> Decision{Final Decision}:::llm
    Decision -->|PROCEED| Proceed[Launch Approved]:::sys
    Decision -->|PAUSE| Pause[Hold Execution]:::sys
    Decision -->|ROLLBACK| Rollback[Abort & Log Issues]:::sys

    %% ====== OUTPUT ======
    Proceed --> Output[(Logs + Console Output)]:::sys
    Pause --> Output
    Rollback --> Output
```

---

## 🚀 Features That Stand Out

1. **AST-Driven Vector Chunking**: Instead of relying on naive line-based text splitters, we use Tree-Sitter to extract *perfectly bounded* functions and classes. This ensures the LLM never receives half-cut context windows.
2. **Model Context Protocol (MCP)**: Implements the exact same zero-shot framework that powers VS Code's Copilot and Anthropic's Claude to trigger dynamic real-time integrations to GitHub repos natively via standard JSON RPC.
3. **No-Latency DAG Execution (LangGraph)**: The multi-agent formulation guarantees strict outputs separated by concern avoiding single-prompt confusion that plagues simplistic systems.
4. **Dynamic Ephemeral Memory**: FAISS vector indices are generated entirely on-the-fly and cleaned to ensure guaranteed codebase sync and to prevent token bloat across versions.

## 💻 Tech Stack
- **Orchestration**: `langgraph`, `langchain-core`
- **Models**: `langchain-google-genai` (Gemini Flash + Gemini Embeddings)
- **Vector Core**: `faiss-cpu`
- **AST Engine**: `tree-sitter`, `tree-sitter-python`
- **Client Protocol**: `@modelcontextprotocol/server-github` via NodeJS STDIO invocation.

## 🛠️ Quickstart

1. Clone repo, install dependencies from `requirements.txt`.
2. Copy .env.example to .env and configure `.env`:
   ```env
   GOOGLE_API_KEY=your_gemini_key
   GITHUB_PERSONAL_ACCESS_TOKEN=your_token
   ```
3. Run Local RAG Retrieval:
   ```bash
   python main.py "Find potential bugs in the AST parser"
   ```
4. Run Remote GitHub Investigation:
   ```bash
   python main.py "Fetch and summarize the active issues for repo github_username/repository_name"
   ```

### For example queries , look into terminal_exeecution_logs.md

### 📧 For any queries, contact me at [anughnakandimalla11@gmail.com](anughnakandimalla11@gmail.com).

## 👩‍💻Author

Anughna
