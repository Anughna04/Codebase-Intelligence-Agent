import sys
import asyncio
from graph import create_review_graph

async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"\n🚀 Starting AI-Powered Code Intelligence Pipeline...")
    print(f"Query: {query}\n")

    app = create_review_graph()
    
    initial_state = {
        "query": query,
        "route": "",
        "context": [],
        "messages": [],
        "analysis": "",
        "bugs": "",
        "architecture": "",
        "final_report": ""
    }
    
    print("--- Executing Agents DAG ---")
    try:
        async for output in app.astream(initial_state):
            for node_name, state in output.items():
                print(f"✅ Finished node: {node_name}")
                if "final_report" in state and node_name == "synthesizer":
                    print("\n" + "="*60)
                    print(state["final_report"])
                    print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    import warnings
    warnings.filterwarnings("ignore")
    
    asyncio.run(main())
