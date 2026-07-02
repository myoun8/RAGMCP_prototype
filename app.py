import importlib.util
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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

agent_executor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_executor

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

    rchat_key = os.getenv("RCHAT_API_KEY")
    rchat_model = "gemma-4-31B-it"
    raw_endpoint = "https://rchat.nist.gov/api/v1/chat/completions"
    clean_base_url = raw_endpoint.replace("/chat/completions", "")

    rchat_llm = ChatOpenAI(
        model=rchat_model,
        api_key=rchat_key,
        base_url=clean_base_url,
        temperature=0.0,
    )

    mcp_client = MultiServerMCPClient({
        "ncnr-api-server": {
            "transport": "stdio",
            "command": "npx.cmd",
            "args": [
                "--yes",
                "@ivotoby/openapi-mcp-server",
                "--api-base-url", "https://ncnr.nist.gov/ncnrdata/metadata/api/v1",
                "--openapi-spec", str(REPO_ROOT / "openAPI.json"),
            ],
        },
    })

    print("Connecting to MCP servers...")
    tools = await mcp_client.get_tools() + [gen_chunks_tool, run_pipeline_tool]

    system_instruction = ("You are an intelligent data router for the NIST Center for Neutron Research (NCNR).\n"
                          "You have access to structured API databases and an unstructured RAG vector database through "
                          "your provided tools.\n"
                          "\n"
                          "CRITICAL TOOL RULES:\n"
                          "1. ONLY include arguments that are explicitly requested by the user.\n"
                          "2. DO NOT pass empty strings, 'None', or null for optional parameters. Omit them entirely.")

    memory = MemorySaver()
    agent_executor = create_agent(
        model=rchat_llm,
        tools=tools,
        system_prompt=system_instruction,
        checkpointer=memory,
    )

    print("Agent ready at http://127.0.0.1:8000")
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(REPO_ROOT / "static")), name="static")


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


@app.get("/", response_class=HTMLResponse)
async def root():
    with open(REPO_ROOT / "static" / "index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = await agent_executor.ainvoke(
        {"messages": [("user", req.message)]},
        config=config,
    )
    final_msg = result["messages"][-1]
    content = final_msg.content
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return {"response": content}


TOOL_STATUS = {
    "gen_chunks":         "Searching knowledge base…",
    "run_pipeline":       "Running ingestion pipeline…",
    "search-instruments": "Searching instruments…",
    "search-experiments": "Searching experiments…",
    "search-datafiles":   "Searching data files…",
}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def generate():
        config = {"configurable": {"thread_id": req.thread_id}}

        def emit(obj: dict) -> str:
            return f"data: {json.dumps(obj)}\n\n"

        try:
            async for event in agent_executor.astream_events(
                {"messages": [("user", req.message)]},
                config=config,
                version="v2",
            ):
                kind = event["event"]
                name = event.get("name", "")

                if kind == "on_chat_model_start":
                    yield emit({"type": "status", "text": "Thinking…"})

                elif kind == "on_tool_start":
                    status = TOOL_STATUS.get(name, f"Using {name}…")
                    inp = event["data"].get("input", {})
                    inp_str = (
                        inp.get("input", str(inp)) if isinstance(inp, dict) else str(inp)
                    )
                    yield emit({"type": "status", "text": status})
                    yield emit({"type": "step_start", "name": name, "input": inp_str[:1200]})

                elif kind == "on_tool_end":
                    out = event["data"].get("output", "")
                    yield emit({"type": "step_end", "name": name, "output": str(out)[:2000]})

                elif kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and not getattr(chunk, "tool_call_chunks", None):
                        content = getattr(chunk, "content", "")
                        if isinstance(content, str) and content:
                            yield emit({"type": "token", "text": content})
                        elif isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    t = block.get("text", "")
                                    if t:
                                        yield emit({"type": "token", "text": t})

            yield emit({"type": "done"})

        except Exception as exc:
            yield emit({"type": "error", "text": str(exc)})
            yield emit({"type": "done"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
