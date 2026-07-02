import asyncio
import importlib.util
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent
MCP_SERVER = REPO_ROOT / "scripts" / "mcpServer.py"

_spec = importlib.util.spec_from_file_location("mcpServer", MCP_SERVER)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["mcpServer"] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

gen_chunks_tool = StructuredTool.from_function(
    func=_mod.gen_chunks,
    name="gen_chunks",
    description=_mod.gen_chunks.__doc__,
)
run_pipeline_tool = StructuredTool.from_function(
    func=_mod.run_pipeline,
    name="run_pipeline",
    description=_mod.run_pipeline.__doc__,
)

# --- Old Local Model ---
# local_llm = ChatOllama(
#     model="llama3.2:latest",
#     base_url="http://127.0.0.1:11434",
#     temperature=0.0
# )
rchat_key = os.getenv("RCHAT_API_KEY")
rchat_model = "gemma-4-31B-it"
raw_endpoint = "https://rchat.nist.gov/api/v1/chat/completions"

clean_base_url = raw_endpoint.replace("/chat/completions", "")
rchat_llm = ChatOpenAI(
    model=rchat_model,
    api_key=rchat_key,
    base_url=clean_base_url,
    temperature=0.0
)

async def run_agent():
    mcp_client = MultiServerMCPClient({
        "ncnr-api-server": {
            "transport": "stdio",
            "command": "npx.cmd",
            "args": [
                "--yes",
                "@ivotoby/openapi-mcp-server",
                "--api-base-url", "https://ncnr.nist.gov/ncnrdata/metadata/api/v1",
                "--openapi-spec", str(REPO_ROOT / "openAPI.json")
            ]
        },
    })

    print("Connecting LangGraph adapter to MCP Servers...")
    tools = await mcp_client.get_tools() + [gen_chunks_tool, run_pipeline_tool]

    system_instruction = (
        "You are an intelligent data router for the NIST Center for Neutron Research (NCNR).\n"
        "You have access to structured API databases and an unstructured RAG vector database.\n\n"
        "Available tools:\n"
        "--- STRUCTURED API TOOLS ---\n"
        "- 'search-instruments': Use this if the user asks for available, active, or listed instruments.\n"
        "- 'search-experiments': Use this if the user asks for specific research runs, IDs, or experiments.\n"
        "- 'search-datafiles': Use this if the user asks for specific files or raw data arrays.\n\n"
        "--- RAG & KNOWLEDGE TOOLS ---\n"
        "- 'gen_chunks': Use this if the user asks general knowledge questions, wants to search manuals, or asks for semantic information that requires looking up text from the local vector database.\n"
        "- 'run_pipeline': ONLY use this if the user explicitly asks you to 'ingest documents', 'update the database', or 'run the pipeline'. This triggers a heavy ingestion process.\n\n"
        "CRITICAL TOOL RULES:\n"
        "1. ONLY include arguments that are explicitly requested by the user.\n"
        "2. DO NOT pass empty strings, 'None', or null for optional parameters. Omit them entirely.\n"
    )
    memory = MemorySaver()
    agent_executor = create_agent(
        model=rchat_llm,
        tools=tools,
        system_prompt=system_instruction,
        checkpointer=memory
    )

    config = {"configurable": {"thread_id": "ncnr_session_1"}}

    while True:
        user_query = input("\nYou: ")
        if user_query.lower() in ["exit", "quit"]:
            print("Shutting down assistant...")
            break

        print("\nThinking...")

        async for chunk in agent_executor.astream(
            {"messages": [("user", user_query)]},
            config=config,
            stream_mode="updates"
        ):
            for node_name, node_data in chunk.items():
                print(f"\n[NODE: {node_name}]")
                if "messages" in node_data:
                    for msg in node_data["messages"]:
                        msg.pretty_print()
                        

if __name__ == "__main__":
    asyncio.run(run_agent())
