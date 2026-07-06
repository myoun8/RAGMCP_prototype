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

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = REPO_ROOT / "scripts" / "mcpServer.py"

_spec = importlib.util.spec_from_file_location("mcpServer", MCP_SERVER)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["mcpServer"] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

MCP_TOOL_NAMES = [
    "run_pipeline",
    "gen_chunks",
    "list_instruments",
    "get_instrument",
    "list_datasources",
    "list_data_files",
    "run_reduction",
    "get_reduction_output",
]
mcp_server_tools = [
    StructuredTool.from_function(
        func=getattr(_mod, name),
        name=name,
        description=getattr(_mod, name).__doc__,
    )
    for name in MCP_TOOL_NAMES
]

# --- Old Local Model ---
# local_llm = ChatOllama(
#     model="llama3.2:latest",
#     base_url="http://127.0.0.1:11434",
#     temperature=0.0
# )
rchat_key = os.getenv("RCHAT_API_KEY")
# gemma-4-31B-it cannot disambiguate among >=2 tools under tool_choice="auto"
# (it returns a blank tool_call with no name/id, which crashes ToolMessage
# construction). gpt-oss-120b handles multi-tool auto tool-choice correctly.
rchat_model = "gpt-oss-120b"
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
    tools = await mcp_client.get_tools() + mcp_server_tools

    system_instruction = ("You are an intelligent data router for the NIST Center for Neutron Research (NCNR).\n"
                          "You have access to structured API databases and an unstructured RAG vector database "
                          "through your provided tools.\n"
                          "\n"
                          "CRITICAL TOOL RULES:\n"
                          "1. ONLY include arguments that are explicitly requested by the user.\n"
                          "2. DO NOT pass empty strings, 'None', or null for optional parameters. Omit them entirely.")
 
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
