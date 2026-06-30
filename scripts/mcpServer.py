from fastmcp import FastMCP
import subprocess
import sys
from pathlib import Path
 
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
 
mcp = FastMCP("ProtoRAG")
 
@mcp.tool()
def run_pipeline() -> bool:
    """Runs the full NCNR RAG ingestion pipeline in four
    sequential steps: normalize raw source documents into
    Markdown via the Groq API, chunk each pack's Markdown
    by headings into JSONL, validate pack structure and
    schema, then embed all chunks and load them into a Chroma vectorstore.
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
    configurable distance threshold)."""
    output = subprocess.run([sys.executable, str(SCRIPTS / "gen_chunks.py"), input], cwd=str(REPO_ROOT), capture_output=True, text=True)

    return output.stdout
 
if __name__ == "__main__":
    mcp.run(transport="stdio")