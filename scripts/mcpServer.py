from fastmcp import FastMCP
import copy
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import requests

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
    """Browse files/subdirs at a path within a reductus data source.
       Use this for any requests of finding intent of a file. If 
       pathlist is omitted from a request of the intent of a file,
       ask user for pathlist"""
    return reductus_api.get_file_metadata(source=source, pathlist=pathlist or [])


NCNR_METADATA_API = "https://ncnr.nist.gov/ncnrdata/metadata/api/v1"


@mcp.tool()
def find_raw_data_paths(experiment_id: str, instrument: str | None = None, limit: int = 500) -> list[dict]:
    """Find the raw data files belonging to an NCNR experiment, given its
    experiment_id (and optionally an instrument alias, e.g. 'candor', 'macs',
    'bt1', to narrow the search if the experiment_id alone is ambiguous).

    Queries the NCNR metadata API (/datafiles), which reports the authoritative
    "localdir" for each file, then looks up each directory's real file mtimes
    via list_data_files (reductus requires an exact mtime on every file
    descriptor it loads). Returns a list of
    {"path", "source", "mtime", "filename", "instrument", "rxcycle_id", "start_date"}
    per file, ready to use directly as a file descriptor in reduce_files'
    node_files, or as a pathlist prefix for list_data_files."""
    params = {"experiment_id": experiment_id, "limit": limit}
    if instrument:
        params["instrument"] = instrument
    resp = requests.get(f"{NCNR_METADATA_API}/datafiles", params=params, timeout=30)
    resp.raise_for_status()
    datafiles = resp.json()
    if not datafiles:
        raise ValueError(
            f"No datafiles found for experiment_id={experiment_id!r}"
            + (f", instrument={instrument!r}" if instrument else "")
        )

    mtimes_by_dir = {}
    results = []
    for d in datafiles:
        if d["filename"].lower().startswith("fp"):
            continue
        localdir = d["localdir"]
        if localdir not in mtimes_by_dir:
            metadata = reductus_api.get_file_metadata(source="ncnr", pathlist=localdir.split("/"))
            mtimes_by_dir[localdir] = metadata.get("files_metadata", {})
        file_meta = mtimes_by_dir[localdir].get(d["filename"])
        if file_meta is None:
            continue
        results.append({
            "path": f"ncnrdata/{localdir}/{d['filename']}",
            "source": "ncnr",
            "mtime": file_meta["mtime"],
            "filename": d["filename"],
            "instrument": d["instrument"],
            "rxcycle_id": d["rxcycle_id"],
            "start_date": d.get("start_date"),
        })
    return results


def _load_file_nodes(instrument_id: str, template_name: str) -> tuple[dict, list[dict]]:
    """Look up a named template for an instrument and find its file-input nodes.

    Returns (template_def, load_nodes) where load_nodes is
    [{"node": index, "title": ..., "module": ..., "intent": config.get("intent")}, ...]
    for every module in the template that has a 'filelist' (fileinfo) field.
    """
    instrument = reductus_api.get_instrument(instrument_id)
    templates = instrument.get("templates", {})
    if template_name not in templates:
        raise ValueError(
            f"Unknown template {template_name!r} for {instrument_id!r}; "
            f"available: {sorted(templates)}"
        )
    registry = {m["id"]: m for m in instrument["modules"]}
    template_def = copy.deepcopy(templates[template_name])

    load_nodes = []
    for i, node in enumerate(template_def["modules"]):
        module = registry.get(node["module"])
        if module is None:
            continue
        has_filelist = any(
            f.get("id") == "filelist" and f.get("datatype") == "fileinfo"
            for f in module.get("fields", [])
        )
        if has_filelist:
            load_nodes.append({
                "node": i,
                "title": node.get("title", node["module"]),
                "module": node["module"],
                "intent": node.get("config", {}).get("intent"),
            })
    return template_def, load_nodes


@mcp.tool()
def list_reduction_templates(instrument_id: str) -> dict:
    """List the standard reduction templates available for a reductus instrument,
    and for each template, which module nodes accept data files (and their role,
    e.g. 'specular'/'background+'/'intensity' for reflectometry).

    Instrument IDs are like 'ncnr.sans' or 'ncnr.refl'. Returns a dict mapping

    Use this before reduce_files to find a template_name and the node indices
    to pass in node_files."""
    instrument = reductus_api.get_instrument(instrument_id)
    result = {}
    for template_name in instrument.get("templates", {}):
        _, load_nodes = _load_file_nodes(instrument_id, template_name)
        result[template_name] = load_nodes
    return result


def _sanitize_fileinfo(file_descriptor: dict) -> dict:
    """Reduce a file descriptor down to the exact {path, source, mtime[, entries]}
    shape reductus' fileinfo validator requires, dropping any extra descriptive
    keys (e.g. filename/instrument/rxcycle_id from find_raw_data_paths)."""
    if "mtime" not in file_descriptor:
        raise ValueError(f"file descriptor missing required 'mtime': {file_descriptor!r}")
    sanitized = {
        "path": str(file_descriptor["path"]),
        "source": str(file_descriptor["source"]),
        "mtime": int(file_descriptor["mtime"]),
    }
    if file_descriptor.get("entries") is not None:
        sanitized["entries"] = list(file_descriptor["entries"])
    return sanitized


def _all_node_outputs(instrument_id: str, template_def: dict, config: dict, return_type: str) -> dict:
    """Compute every node's output terminal(s) one at a time via calc_terminal.

    reductus' own calc_template (web_gui/api.py) has a latent bug: dataflow/calc.py's
    _key() builds "module:terminal" strings, but calc_template unpacks each result
    key as a 2-tuple, which raises "too many values to unpack" for any real
    multi-node template. calc_terminal doesn't hit that code path, so we call it
    once per (node, output terminal) instead of using calc_template; reductus'
    fingerprint cache means the repeated upstream computation is cheap after the
    first call.
    """
    instrument = reductus_api.get_instrument(instrument_id)
    registry = {m["id"]: m for m in instrument["modules"]}
    output = {}
    for i, node in enumerate(template_def["modules"]):
        module = registry.get(node["module"])
        if module is None:
            continue
        node_key = str(i)
        output[node_key] = {
            terminal["id"]: reductus_api.calc_terminal(
                template_def, config, i, terminal["id"], return_type=return_type,
            )
            for terminal in module.get("outputs", [])
        }
    return output


@mcp.tool()
def reduce_files(
    instrument_id: str,
    template_name: str,
    node_files: dict[str, list[dict]],
    target_node: int | None = None,
    target_terminal: str = "output",
    return_type: str = "metadata",
) -> dict:
    """Pick specific data files and reduce them using one of an instrument's
    standard reduction templates, without hand-building the module graph.

    Workflow:
    1. list_reduction_templates(instrument_id) to get a template_name and the
       load node indices (and their intent, e.g. specular/background+/intensity).
    2. list_data_files(source, pathlist) to browse an experiment's files and get
       their filenames/mtimes.
    3. Call this tool with node_files mapping each load node index (as a string,
       e.g. "0") to a list of file descriptors, each needing at least "path"
       (e.g. "ncnrdata/<instr>/<cycle>/<experiment>/data/<file>"), "mtime"
       (int, required by reductus), and "source" (e.g. "ncnr"). Extra keys
       (e.g. from find_raw_data_paths' output) are ignored automatically.

    Valid template names and load node indices are instrument-specific; see list_reduction_templates.

    If target_node is omitted, every node's output terminal(s) are computed and
    returned; otherwise only the dependency path to target_node/target_terminal
    is computed (like get_reduction_output). return_type applies in both cases:
    'full' | 'plottable' | 'metadata' | 'export'.
    """
    template_def, load_nodes = _load_file_nodes(instrument_id, template_name)
    valid_nodes = {str(n["node"]) for n in load_nodes}
    unknown = set(node_files) - valid_nodes
    if unknown:
        raise ValueError(
            f"Node(s) {sorted(unknown)} are not file-input nodes for template "
            f"{template_name!r}; valid load nodes: {sorted(valid_nodes)}"
        )

    template_def["name"] = template_name
    template_def.setdefault("description", template_name)
    template_def["instrument"] = instrument_id

    config = {
        node_index: {"filelist": [_sanitize_fileinfo(f) for f in files]}
        for node_index, files in node_files.items()
    }

    if target_node is None:
        return _all_node_outputs(instrument_id, template_def, config, return_type)
    return reductus_api.calc_terminal(
        template_def, config, target_node, target_terminal, return_type=return_type,
    )

if __name__ == "__main__":
    mcp.run(transport="stdio")