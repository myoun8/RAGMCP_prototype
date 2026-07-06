from fastmcp import FastMCP
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "rag" / "scripts"

_common_spec = importlib.util.spec_from_file_location("_common", SCRIPTS / "_common.py")
_common = importlib.util.module_from_spec(_common_spec)  # type: ignore[arg-type]
sys.modules["_common"] = _common
_common_spec.loader.exec_module(_common)  # type: ignore[union-attr]
ensure_ollama = _common.ensure_ollama

ensure_ollama()

from reductus.web_gui import api as reductus_api

reductus_api.initialize()  # loads reductus/configurations/config.py once at startup

mcp = FastMCP("ProtoRAG")

@mcp.tool()
def run_pipeline() -> bool:
    """Runs the full NCNR RAG ingestion pipeline in four
    sequential steps: normalize raw source documents into
    Markdown via the Groq API, chunk each pack's Markdown
    by headings into JSONL, validate pack structure and
    schema, then embed all chunks and load them into a Chroma vectorstore.
    Should be run after the original database is updated or new source documents are added.
    """
    result = subprocess.run([sys.executable, str(SCRIPTS / "run_pipeline.py")], cwd=str(REPO_ROOT))

    return result.returncode == 0
 
@mcp.tool()
def gen_chunks(input: str) -> str:
    """Retrieves the top-k most relevant chunks from
    the NCNR RAG Chroma vectorstore for a given
    natural-language query, using cosine-distance
    similarity search with optional filtering by
    instrument pack, access level, and status. Returns
    the matching chunk texts (dropping any below a
    configurable distance threshold). You MUST use 
    this tool if the user asks HOW a specific 
    instrument (like CANDOR or MACS) works."""
    output = subprocess.run(
        [sys.executable, str(SCRIPTS / "gen_chunks.py"), input],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    if output.returncode != 0:
        return output.stderr or "gen_chunks failed with no error output"

    return (
        f"<retrieved_chunks query={input!r} source=\"NCNR RAG Chroma vectorstore\">\n"
        "```text\n"
        f"{output.stdout}\n"
        "```\n"
        "</retrieved_chunks>"
    )


@mcp.tool()
def list_instruments() -> list:
    """List available reductus instruments (e.g. 'ncnr.refl', 'ncnr.sans')."""
    return reductus_api.list_instruments()


@mcp.tool()
def get_instrument(instrument_id: str) -> dict:
    """Get the module/terminal definition for a reductus instrument
    (the graph of modules you can wire together for that instrument)."""
    return reductus_api.get_instrument(instrument_id)


@mcp.tool()
def list_datasources() -> list:
    """List configured reductus data sources (e.g. 'ncnr', 'local')."""
    return reductus_api.list_datasources()


@mcp.tool()
def list_data_files(source: str = "ncnr", pathlist: list[str] | None = None) -> dict:
    """Browse files/subdirs at a path within a reductus data source."""
    return reductus_api.get_file_metadata(source=source, pathlist=pathlist or [])


@mcp.tool()
def run_reduction(template_def: dict, config: dict) -> dict:
    """Run a full reductus reduction template graph and return every node's output.
    template_def needs 'name', 'modules' (list of {"module": ..., "version": ...}),
    'wires' (connections between module terminals), and 'instrument'."""
    return reductus_api.calc_template(template_def, config)


@mcp.tool()
def get_reduction_output(
    template_def: dict, config: dict, nodenum: int, terminal_id: str,
    return_type: str = "metadata",
) -> dict:
    """Compute one output terminal of a reductus template (cheaper than run_reduction
    since only the dependency path to that node is evaluated).
    return_type: 'full' | 'plottable' | 'metadata' | 'export'."""
    return reductus_api.calc_terminal(template_def, config, nodenum, terminal_id, return_type=return_type)


if __name__ == "__main__":
    mcp.run(transport="stdio")