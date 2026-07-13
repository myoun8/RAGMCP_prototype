import os
from turtle import pd

from fastmcp import FastMCP
import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import uuid
import pandas
from pathlib import Path

import pandas
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "rag" / "scripts"

# Figures from generate_plot land here; app.py serves REPO_ROOT/static at
# /static, so a file written here is reachable at /static/generated/<name>.
GENERATED_DIR = REPO_ROOT / "static" / "generated"

_common_spec = importlib.util.spec_from_file_location("_common", SCRIPTS / "_common.py")
_common = importlib.util.module_from_spec(_common_spec)  # type: ignore[arg-type]
sys.modules["_common"] = _common
_common_spec.loader.exec_module(_common)  # type: ignore[union-attr]
ensure_ollama = _common.ensure_ollama

ensure_ollama()

# gen_chunks retrieval runs in-process (not as a per-call subprocess) so the
# heavy chromadb/langchain imports and the Chroma connection happen once, at
# startup, instead of on every tool call. The module does `from _common import
# ...`, which resolves via the _common entry registered in sys.modules above.
_gc_spec = importlib.util.spec_from_file_location("gen_chunks", SCRIPTS / "gen_chunks.py")
_gen_chunks = importlib.util.module_from_spec(_gc_spec)  # type: ignore[arg-type]
sys.modules["gen_chunks"] = _gen_chunks
_gc_spec.loader.exec_module(_gen_chunks)  # type: ignore[union-attr]

_vectorstore = None


def _get_vectorstore():
    """Open the shared Chroma vectorstore once and reuse the handle across
    gen_chunks calls. The old subprocess re-imported chromadb/langchain and
    reconnected on every call; caching the handle keeps that cost to the first
    retrieval only."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore, _ = _common.open_vectorstore(base_url=_common.EMBED_BASE_URL)
    return _vectorstore

from reductus.web_gui import api as reductus_api
from reductus.dataflow import fetch as reductus_fetch
from reductus.dataflow.lib.h5_open import h5_open_zip

reductus_api.initialize()  # loads reductus/configurations/config.py once at startup

mcp = FastMCP("ProtoRAG")

@mcp.tool()
def run_pipeline() -> bool:
    """Runs the full NCNR RAG ingestion pipeline in four
    sequential steps: normalize raw source documents into
    Markdown via the RChat API, chunk each pack's Markdown
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
    instrument (like CANDOR or MACS) works. Do NOT use this tool to answer questions about raw data files"""
    try:
        kept = _gen_chunks.retrieve(input, vectorstore=_get_vectorstore())
        body = _gen_chunks.format_chunks(kept)
    except _gen_chunks.RetrievalError as exc:
        return str(exc)
    except Exception as exc:  # noqa: BLE001 - surface retrieval failure as tool output, don't kill the run
        return f"gen_chunks failed: {type(exc).__name__}: {exc}"

    return (
        f"<retrieved_chunks query={input!r} source=\"NCNR RAG Chroma vectorstore\">\n"
        "```text\n"
        f"{body}\n"
        "```\n"
        "</retrieved_chunks>"
    )


# Base URL of the reductus web app; deep links append instrument/source/pathlist
# query params, which its front-end reads (web_gui/webreduce/js/main.js) to open
# the right instrument and data folder.
REDUCTUS_APP_URL = "https://reductus.nist.gov/"


def _reductus_url(instrument: str | None = None, path: str | None = None,
                  source: str = "ncnr") -> str:
    """Build a reductus web-app deep link. With no instrument, returns the app
    homepage; otherwise encodes instrument/source/pathlist as the reductus
    front-end reads them from the query string."""
    if not instrument:
        return REDUCTUS_APP_URL
    from urllib.parse import urlencode

    params = {"instrument": instrument, "source": source}
    if path:
        params["pathlist"] = str(path).strip("/")
    # safe="/" keeps pathlist's slashes literal (e.g. ...&pathlist=ncnrdata/candor/202011/27839/data)
    # rather than percent-encoded, matching the reductus front-end's expected link format.
    return f"{REDUCTUS_APP_URL}?{urlencode(params, safe='/')}"


# Template payloads from reduce_files/export_reduction land here, keyed by a
# uuid, so generate_plot/the UI can reference one by a short id instead of
# round-tripping the full template JSON through the model's context window.
TEMPLATES_DIR = GENERATED_DIR / "templates"


def _template_payload(template_def: dict, config: dict) -> dict:
    """Merge per-node file-selection config into a template_def's modules,
    producing the exact shape reductus' web editor's `editor.load_template`
    expects: each module carries its own `config` dict (reductus' Template/
    calc_terminal API instead takes template_def and config as two separate
    arguments)."""
    payload = copy.deepcopy(template_def)
    for node_index, node_config in config.items():
        module = payload["modules"][int(node_index)]
        module["config"] = {**module.get("config", {}), **node_config}
    return payload


def _save_template_payload(template_def: dict, config: dict) -> str:
    """Save a reduce_files/export_reduction template+config as an editor-ready
    payload and return its id (the file basename), for generate_plot's
    reductus_template_id and the UI's 'open in reductus editor' button."""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    template_id = uuid.uuid4().hex
    payload = _template_payload(template_def, config)
    (TEMPLATES_DIR / f"{template_id}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return template_id


def _reductus_folder(node_files: dict[str, list[dict]] | None) -> str | None:
    """Best-effort common data folder for a node_files mapping: the directory
    the reduced files live in, used as reductus' pathlist. Returns None when no
    path can be determined."""
    import posixpath
    from collections import Counter

    dirs = []
    for files in (node_files or {}).values():
        for descriptor in files or []:
            path = descriptor.get("path") if isinstance(descriptor, dict) else None
            if path:
                dirs.append(posixpath.dirname(str(path).replace("\\", "/")))
    if not dirs:
        return None
    return Counter(dirs).most_common(1)[0][0] or None


@mcp.tool()
def generate_plot(
    code: str,
    title: str | None = None,
    reductus_instrument: str | None = None,
    reductus_path: str | None = None,
    reductus_source: str = "ncnr",
    reductus_template_id: str | None = None,
) -> str:
    """Build an interactive Plotly figure from Python code and return an HTML
    placeholder the UI renders. For ad-hoc x/y data; to plot a REDUCED curve use
    plot_reduction. `code`: Python building ONE figure assigned to `fig`; `go`,
    `px`, `np` are pre-imported (don't re-import or call fig.show()). Put data
    inline; default to intensity vs Q. Optionally pass reductus_instrument/path/
    source/template_id (from reduce_files) to deep-link. Return the
    <div class="plotly-figure"> verbatim."""
    import uuid

    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    namespace = {"go": go, "px": px, "np": np}
    try:
        exec(code, namespace)  # noqa: S102 - model-authored plotting code, local research tool
    except Exception as exc:  # noqa: BLE001 - surface the failure to the model, don't crash
        raise ValueError(f"plotly code failed: {type(exc).__name__}: {exc}") from exc

    fig = namespace.get("fig")
    if not isinstance(fig, go.Figure):
        raise ValueError(
            "code produced no plot; assign a Plotly figure to a variable named "
            "`fig`, e.g. fig = go.Figure(go.Scatter(x=..., y=...))"
        )

    if title:
        fig.update_layout(title_text=title)

    # Embed a reductus deep-link URL alongside the figure so the UI can point
    # the plot's "Open in Reductus" link at the exact instrument/folder. The
    # reductus web app reads instrument/source/pathlist from the query string.
    fig_dict = json.loads(fig.to_json())
    fig_dict["reductus_url"] = _reductus_url(
        reductus_instrument, reductus_path, reductus_source
    )
    if reductus_template_id:
        fig_dict["reductus_template_id"] = reductus_template_id

    plot_id = uuid.uuid4().hex
    (GENERATED_DIR / f"{plot_id}.json").write_text(
        json.dumps(fig_dict), encoding="utf-8"
    )

    return f'<div class="plotly-figure" data-src="/static/generated/{plot_id}.json"></div>'


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


NCNR_METADATA_API = "https://ncnr.nist.gov/ncnrdata/metadata/api/v1"

# reductus' TRAJECTORY_INTENTS (reflred/nexusref.py): the metadata DB harvests a
# reflectometer/CANDOR file's raw trajectoryData/_scanType into its "intent"
# field, so mapping it here reproduces get_file_intent's value without loading
# the file. VSANS instead exposes "file_purpose" (SCATTERING/TRANSMISSION, =
# analysis.filepurpose) -- that is a purpose, not the Sample/Empty/Blocked/Open
# analysis.intent, so it's surfaced separately as a best-effort hint.
_RAW_INTENT_MAP = {
    "SPEC": "specular",
    "SLIT": "intensity",
    "BGP": "background+",
    "BGM": "background-",
    "ROCK": "rock sample",
}


def _intent_from_metadata_blob(blob: str | None) -> str | None:
    """Read the measurement intent out of a /datafiles record's metadata blob
    (a JSON string), without loading the file through reductus.

    Returns the mapped reflectometer/CANDOR intent when the DB has harvested the
    file's scan type, else the lowercased VSANS file_purpose as a fallback hint,
    else None (e.g. findpeak/alignment scans and instruments whose metadata the
    DB does not harvest -- fall back to get_file_intent for those)."""
    if not blob:
        return None
    try:
        metadata = json.loads(blob)
    except (json.JSONDecodeError, TypeError):
        return None
    raw = metadata.get("intent")  # reflectometer/CANDOR: raw _scanType
    if raw:
        return _RAW_INTENT_MAP.get(raw, raw)
    purpose = metadata.get("file_purpose")  # VSANS: filepurpose, not intent
    return purpose.lower() if purpose else None


def _search_intent_via_metadata(path: str, source: str = "ncnr") -> list[dict] | None:
    """get_file_intent's fast path: look the file up in the NCNR metadata DB by
    filename and read its harvested intent, avoiding a reductus file load.

    Returns [{"filename", "intent", "metadata"}] (metadata = the DB's harvested
    fields) when the DB has a non-empty intent for the file, else None so the
    caller falls back to loading the file. Any failure -- non-ncnr source,
    network/HTTP error, no matching record, or an empty intent -- returns None to
    trigger that fallback."""
    if source != "ncnr":
        return None
    normalized = path.strip("/")
    parts = normalized.split("/")
    filename = parts[-1]
    params = {"filename": filename, "limit": 20}
    # path is ncnrdata/<instrument>/<cycle>/<exp>/data/<filename>; the second
    # segment is the metadata DB's instrument alias, which narrows the search.
    if len(parts) > 2 and parts[0] == "ncnrdata":
        params["instrument"] = parts[1]
    try:
        resp = requests.get(f"{NCNR_METADATA_API}/datafiles", params=params, timeout=30)
        resp.raise_for_status()
        records = resp.json()
    except (requests.RequestException, ValueError):
        return None
    # Prefer the record whose full reconstructed path matches ours; fall back to
    # any filename match (names are effectively unique within an instrument).
    record = next(
        (r for r in records
         if f"ncnrdata/{r.get('localdir')}/{r.get('filename')}" == normalized),
        next((r for r in records if r.get("filename") == filename), None),
    )
    if record is None:
        return None
    intent = _intent_from_metadata_blob(record.get("metadata"))
    if not intent:
        return None
    try:
        db_metadata = json.loads(record["metadata"])
    except (json.JSONDecodeError, TypeError, KeyError):
        db_metadata = {}
    return [{"filename": filename, "intent": intent, "metadata": db_metadata}]


@mcp.tool()
def find_raw_data_paths(experiment_id: str, instrument: str | None = None) -> list[dict]:
    """Find an NCNR experiment's raw data files by experiment_id (optionally an
    instrument alias like 'candor'/'macs' to disambiguate). Returns one dict per
    file with "path", "source", "mtime", "filename", "instrument", "rxcycle_id",
    "start_date", "intent" and "download_url" — usable directly as a reduce_files
    node_files descriptor. Show 20 files unless asked. Surface "download_url" as
    a Markdown link. "intent" is null for un-harvested files — use get_file_intent
    for those and true VSANS intent."""
    limit = 500
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
        path = f"ncnrdata/{localdir}/{d['filename']}"
        results.append({
            "path": path,
            "source": "ncnr",
            "mtime": file_meta["mtime"],
            "filename": d["filename"],
            "instrument": d["instrument"],
            "rxcycle_id": d["rxcycle_id"],
            "start_date": d.get("start_date"),
            "intent": _intent_from_metadata_blob(d.get("metadata")),
            # Relative link the app's /download/raw proxy streams the original
            # file through; surface it to let the user download the raw file.
            "download_url": f"/download/raw/ncnr/{path}",
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

    Metadata results are summarized to one line per dataset (datatype +
    filename/intent): the full per-node metadata runs ~35KB per dataset even
    after array compaction (59-key dicts survive it untouched), so a 13-node
    template returned ~420KB — far past any LLM context budget. Callers who
    need a node's full metadata pass target_node instead.
    """
    instrument = reductus_api.get_instrument(instrument_id)
    registry = {m["id"]: m for m in instrument["modules"]}
    output = {}
    for i, node in enumerate(template_def["modules"]):
        module = registry.get(node["module"])
        if module is None:
            continue
        node_key = str(i)
        output[node_key] = {}
        for terminal in module.get("outputs", []):
            result = reductus_api.calc_terminal(
                template_def, config, i, terminal["id"], return_type=return_type,
            )
            if return_type == "metadata":
                result = _summarize_node_output(result)
            output[node_key][terminal["id"]] = result
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
    """Reduce data files with an instrument's reduction template. Always 
    attempt to use the template relating the given instrument. Call
    list_reduction_templates for a template_name and its load node indices, then
    pass node_files mapping each load node index (string) to descriptors with
    "path", "mtime" (int) and "source". Prefer a specific template. Omit
    target_node for per-node summaries, or pass it for one node's full output
    (return_type: full/plottable/metadata/export). Returns {"reduction",
    "reductus_url", "reductus_template_id"}; to plot use plot_reduction."""
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
        reduction = _fit_result(_all_node_outputs(instrument_id, template_def, config, return_type))
    else:
        reduction = _fit_result(reductus_api.calc_terminal(
            template_def, config, target_node, target_terminal, return_type=return_type,
        ))
    return {
        "reduction": reduction,
        "reductus_url": _reductus_url(instrument_id, _reductus_folder(node_files)),
        "reductus_template_id": _save_template_payload(template_def, config),
    }

# Historical schedule databases live under rag/scraping/, one CSV per
# instrument. All three share the same columns (year, start_date, num_days,
# users, uniq_id, s_no, experiments, equip, contact), so a single search can
# serve any of them just by picking the right file. Keys are lowercased and
# stripped of separators before lookup, so "ng7", "NG7-SANS", "ngb30",
# "bt5", "BT5 USANS", etc. all resolve.
_SCHEDULE_CSVS = {
    "ng7": "NG7_SANS_Mega_Schedule_Database.csv",
    "ng7sans": "NG7_SANS_Mega_Schedule_Database.csv",
    "ngb30": "NGB30_SANS_Mega_Schedule_Database.csv",
    "ngb30sans": "NGB30_SANS_Mega_Schedule_Database.csv",
    "bt5": "BT5_USANS_Mega_Schedule_Database.csv",
    "bt5usans": "BT5_USANS_Mega_Schedule_Database.csv",
}


@mcp.tool()
def search_instrument_schedule(
    instrument: str,
    year: str = None,
    users: str = None,
    experiments: str = None,
    equip: str = None,
    uniq_id: str = None,
    s_no: str = None,
    contact: str = None,
    limit: int = 5
) -> str:
    """Look up the historical experiment SCHEDULE for an SANS/USANS instrument
    (NG7, NGB30, or BT5): who ran an experiment, what was measured, and when --
    e.g. "what did NG7 run in 2019?", "when did John Barker have beam time on
    BT5?". Use this (NOT gen_chunks, which answers how an instrument works) for
    past beam time, experimenter names, experiment titles, or equipment usage.

    You MUST use this tool for ANY question about past experiments on NG7,
    NGB30, or BT5 -- it is the only source of that historical schedule data.
    Do not answer from prior knowledge or other tools; always query here first.

    `instrument` is REQUIRED (ng7, ngb30, or bt5). Filter with any of year,
    users, experiments, equip, contact, uniq_id, s_no (case-insensitive
    substring match); omit all to browse recent entries.
    """
    try:
        key = "".join(ch for ch in (instrument or "").lower() if ch.isalnum())
        csv_name = _SCHEDULE_CSVS.get(key)
        if csv_name is None:
            return (
                f"Unknown instrument {instrument!r}. "
                "Choose one of: ng7, ngb30, bt5."
            )

        script_dir = Path(__file__).resolve().parent

        # Go UP one level to 'rawdataRAG/', then DOWN into 'rag/scraping/'
        csv_path = script_dir.parent / "rag" / "scraping" / csv_name

        # Load the selected instrument's database
        df = pandas.read_csv(csv_path)

        # Fill empty cells with empty strings so text search doesn't crash on NaNs
        df = df.fillna("")

        # 3. Apply dynamic filters (case-insensitive substring matching)
        if year:
            df = df[df['year'].astype(str).str.contains(year, case=False)]
        if users:
            df = df[df['users'].astype(str).str.contains(users, case=False)]
        if experiments:
            df = df[df['experiments'].astype(str).str.contains(experiments, case=False)]
        if equip:
            df = df[df['equip'].astype(str).str.contains(equip, case=False)]
        if uniq_id:
            df = df[df['uniq_id'].astype(str).str.contains(uniq_id, case=False)]
        if s_no:
            df = df[df['s_no'].astype(str).str.contains(s_no, case=False)]
        if contact:
            df = df[df['contact'].astype(str).str.contains(contact, case=False)]

        # 4. Format the output for the LLM
        if df.empty:
            return "No matching schedules found for those parameters."

        # Grab the top 'limit' results
        results = df.head(limit).to_dict(orient="records")
        
        output = f"Found {len(df)} total matches. Showing top {len(results)}:\n\n"
        for i, row in enumerate(results, 1):
            output += f"--- Result {i} ---\n"
            for key, val in row.items():
                if str(val).strip():  # Only show fields that actually have data
                    output += f"  {key.capitalize()}: {val}\n"
            output += "\n"

        return output

    except FileNotFoundError:
        return f"Error: Could not find '{csv_name}' under rag/scraping/."
    except Exception as e:
        return f"An error occurred during search: {str(e)}"

def _plottable_traces(plottable: dict) -> list[dict]:
    """Extract drawable (x, y[, errorbars], axis labels) traces from a reductus
    return_type='plottable' result.

    calc_terminal(..., return_type='plottable') returns
    {'datatype': ..., 'values': [<per-dataset plottable>, ...]}. Reflectometry/
    CANDOR reduced curves serialize as type 'nd' (see refldata.ReflData.
    get_plottable): options.xcol/ycol name the Q and intensity columns,
    datas[col]['values'] holds the full arrays, datas[col]['errorbars'] the
    uncertainties, and options.axes.{xaxis,yaxis}.label the axis titles.

    This pulls the arrays out whole -- unlike reduce_files, which compacts every
    array down to an 8-element sample so the result fits an LLM context window
    (which is exactly why a reduce_files result can't be plotted directly)."""
    traces: list[dict] = []
    values = plottable.get("values") if isinstance(plottable, dict) else None
    for dataset in values or []:
        if not isinstance(dataset, dict):
            continue
        datas = dataset.get("datas")
        options = dataset.get("options") or {}
        if not isinstance(datas, dict):
            continue
        xcol, ycol = options.get("xcol"), options.get("ycol")
        xseries = datas.get(xcol) if isinstance(datas.get(xcol), dict) else None
        yseries = datas.get(ycol) if isinstance(datas.get(ycol), dict) else None
        if not xseries or not yseries:
            continue
        x, y = xseries.get("values"), yseries.get("values")
        if not x or not y:
            continue
        axes = options.get("axes") or {}
        traces.append({
            "label": dataset.get("title") or dataset.get("entry") or ycol,
            "x": x,
            "y": y,
            "dy": yseries.get("errorbars"),
            "xlabel": (axes.get("xaxis") or {}).get("label") or xcol,
            "ylabel": (axes.get("yaxis") or {}).get("label") or ycol,
        })
    return traces


@mcp.tool()
def plot_reduction(
    instrument_id: str,
    template_name: str,
    node_files: dict[str, list[dict]],
    target_node: int = 12,
    target_terminal: str = "output",
    title: str | None = None,
) -> str:
    """Reduce files with a standard template and plot the reduced curve
    (intensity/reflectivity vs Q) in one step. Use this — NOT reduce_files then
    generate_plot — for a reduced dataset: it draws the FULL arrays server-side,
    whereas reduce_files returns truncated summaries that plot empty. Arguments
    mirror reduce_files (instrument_id/template_name, node_files of "path"/
    "mtime"/"source" descriptors); target_node = FINAL reduced node (default 12).
    Return the <div class="plotly-figure"> verbatim."""
    import plotly.graph_objects as go

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

    plottable = reductus_api.calc_terminal(
        template_def, config, target_node, target_terminal, return_type="plottable",
    )
    traces = _plottable_traces(plottable)
    if not traces:
        raise ValueError(
            f"node {target_node} terminal {target_terminal!r} produced no "
            "plottable x/y data; make sure target_node is the reduced-curve "
            "node (the final reduction step)."
        )

    fig = go.Figure()
    xlabel = ylabel = None
    all_positive = True
    for trace in traces:
        scatter = {
            "x": trace["x"],
            "y": trace["y"],
            "mode": "markers+lines",
            "name": trace["label"],
        }
        if trace["dy"]:
            scatter["error_y"] = {"type": "data", "array": trace["dy"], "visible": True}
        fig.add_trace(go.Scatter(**scatter))
        xlabel = xlabel or trace["xlabel"]
        ylabel = ylabel or trace["ylabel"]
        all_positive = all_positive and all(
            isinstance(v, (int, float)) and v > 0 for v in trace["y"]
        )

    fig.update_xaxes(title_text=xlabel or "Q (1/Å)")
    # Reflectivity/intensity span orders of magnitude and are conventionally
    # shown on a log y-axis; fall back to linear if any value is <= 0 (e.g.
    # background-subtracted points can go negative), which log can't render.
    fig.update_yaxes(title_text=ylabel or "Intensity", type="log" if all_positive else "linear")
    fig.update_layout(title_text=title or f"{template_name} — {instrument_id}")

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    fig_dict = json.loads(fig.to_json())
    fig_dict["reductus_url"] = _reductus_url(instrument_id, _reductus_folder(node_files))
    fig_dict["reductus_template_id"] = _save_template_payload(template_def, config)

    plot_id = uuid.uuid4().hex
    (GENERATED_DIR / f"{plot_id}.json").write_text(
        json.dumps(fig_dict), encoding="utf-8"
    )
    return f'<div class="plotly-figure" data-src="/static/generated/{plot_id}.json"></div>'


# Reduction exports (.ort/.orb) are written here for the user to download.
# The dir lives under the static tree, but files are served through app.py's
# /download/export endpoint (not StaticFiles) so each comes back as a Save-As
# attachment with its real filename instead of rendering inline in the browser.
EXPORTS_DIR = GENERATED_DIR / "exports"

# Map the user-facing export format to reductus' registered refl exporter name
# (see reflred/refldata.py's exports_ORSO_text / exports_HDF5) plus the file
# suffix and MIME type used when serving the download.
_ORSO_EXPORTS = {
    "orso_text":  ("ORSO_text",  ".ort", "text/plain; charset=utf-8"),
    "orso_nexus": ("ORSO_nexus", ".orb", "application/x-hdf5"),
}


@mcp.tool()
def export_reduction(
    instrument_id: str,
    template_name: str,
    node_files: dict[str, list[dict]],
    target_node: int,
    target_terminal: str = "output",
    export_format: str = "orso_text",
) -> dict:
    """Export a reduced dataset to a downloadable ORSO file. Reduces files
    exactly as reduce_files (same instrument_id, template_name, node_files,
    target_node), then writes that node's output: export_format='orso_text' ->
    .ort, 'orso_nexus' -> .orb. target_node must be the FINAL reduced node — an
    ORSO file needs reduced R(Q). Returns {"download_url", "filename", "format",
    "reductus_url", "reductus_template_id"}; render download_url and reductus_url
    as Markdown links; use the returned URLs."""
    if export_format not in _ORSO_EXPORTS:
        raise ValueError(
            f"Unknown export_format {export_format!r}; "
            f"choose one of {sorted(_ORSO_EXPORTS)}."
        )
    export_type, suffix, _ = _ORSO_EXPORTS[export_format]

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

    # concatenate=True merges the terminal's datasets into a single ORSO file
    # (multiple data blocks in one .ort/.orb), which is what a user expects to
    # download for one reduced measurement.
    result = reductus_api.calc_terminal(
        template_def, config, target_node, target_terminal,
        return_type="export", export_type=export_type, concatenate=True,
    )
    outputs = (result or {}).get("values") or []
    if not outputs:
        raise ValueError(
            f"{export_type} export of node {target_node} produced no output; "
            "is target_node the reduced-data node?"
        )

    export = outputs[0]
    # reductus builds a proper filename with the right extension; fall back to a
    # generic name and strip to a basename so it can't escape the export dir.
    filename = Path(export.get("filename") or f"reduction{suffix}").name
    value = export["value"]  # ORSO_text -> str, ORSO_nexus -> bytes
    data = value.encode("utf-8") if isinstance(value, str) else bytes(value)

    export_id = uuid.uuid4().hex
    out_dir = EXPORTS_DIR / export_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / filename).write_bytes(data)

    return {
        "download_url": f"/download/export/{export_id}/{filename}",
        "filename": filename,
        "format": export_format,
        "reductus_url": _reductus_url(instrument_id, _reductus_folder(node_files)),
        "reductus_template_id": _save_template_payload(template_def, config),
    }

_INTENT_KEYS = ("intent", "analysis.intent")
_FILENAME_KEYS = ("filename", "run.filename", "name")


def _first_present(metadata: dict, keys: tuple[str, ...]):
    """Return the first non-empty value found in metadata under any of keys.

    Different instrument data classes expose the same concept under different
    keys: reflectometer/CANDOR loaders return a clean {"intent": ...} field,
    while SANS/VSANS loaders return the raw NeXus metadata dict verbatim,
    where the equivalent field is "analysis.intent"."""
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return value
    return None


# Keys worth keeping when a dict has to be truncated: identity/role fields
# first, so a squeezed dataset still says what it is.
_PRIORITY_KEYS = frozenset(
    _FILENAME_KEYS + _INTENT_KEYS
    + ("datatype", "values", "points", "path", "entry", "date", "instrument",
       "polarization", "description", "duration")
)


def _compact_metadata(value, max_items: int = 8, max_str: int = 2000, max_keys: int | None = None):
    """Recursively truncate long lists/tuples/strings (e.g. per-detector-channel
    arrays like x/v/Ld/Li, or column-text export blobs) so a reductus result
    stays small enough to round-trip through an LLM's context window.

    Reflectometer/CANDOR metadata and reduction outputs are raw Data.todict()/
    get_export() output, which embed full per-point arrays or column-text --
    one file can pretty-print to 100KB+. That whole blob used to be dumped
    verbatim into the tool response and re-sent to the model on every
    subsequent turn, which was blowing out small context windows (observed as
    a negative computed max_tokens).

    max_keys (when set) also truncates wide dicts: NeXus/Data.todict() dumps
    carry 59+ keys per dataset, which array truncation alone never shrinks.
    Keys in _PRIORITY_KEYS are kept first; a "_truncated_dict_keys" marker
    records how many were dropped."""
    if isinstance(value, dict):
        keys = list(value)
        if max_keys is not None and len(keys) > max_keys:
            keys = sorted(keys, key=lambda k: k not in _PRIORITY_KEYS)[:max_keys]
            compacted = {k: _compact_metadata(value[k], max_items, max_str, max_keys) for k in keys}
            compacted["_truncated_dict_keys"] = len(value) - len(keys)
            return compacted
        return {k: _compact_metadata(v, max_items, max_str, max_keys) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if len(value) > max_items:
            return {
                "_truncated_array_length": len(value),
                "_sample": [_compact_metadata(v, max_items, max_str, max_keys) for v in value[:max_items]],
            }
        return [_compact_metadata(v, max_items, max_str, max_keys) for v in value]
    if isinstance(value, str) and len(value) > max_str:
        return value[:max_str] + f"... [truncated, {len(value)} chars total]"
    return value


def _summarize_node_output(result):
    """Collapse one calc_terminal metadata result to datatype + one line per
    dataset (filename/intent/points), for whole-graph reduce_files responses
    where per-node full metadata is available separately via target_node."""
    if not isinstance(result, dict):
        return _compact_metadata(result)
    summary = {}
    for key, val in result.items():
        if key == "values" and isinstance(val, list):
            datasets = []
            for v in val:
                if isinstance(v, dict):
                    line = {
                        "filename": _first_present(v, _FILENAME_KEYS),
                        "intent": _first_present(v, _INTENT_KEYS),
                    }
                    if v.get("points") is not None:
                        line["points"] = v["points"]
                    datasets.append(line)
                else:
                    datasets.append(_compact_metadata(v))
            summary["values"] = datasets
        else:
            summary[key] = _compact_metadata(val)
    return summary


# ~24KB of JSON is roughly 6k tokens: large enough for a full single-node
# metadata dump, small enough that a multi-turn conversation re-sending every
# tool result doesn't drive the backend's computed max_tokens negative.
_MAX_RESULT_CHARS = 24_000

# Progressively harsher (max_items, max_str, max_keys) compaction settings.
_COMPACTION_TIERS = ((8, 2000, None), (5, 500, 48), (3, 200, 24), (2, 80, 12))


def _fit_result(value, max_chars: int = _MAX_RESULT_CHARS):
    """Compact a tool result until its JSON fits max_chars, hardening each
    retry (shorter array samples/strings, then dropping non-priority dict
    keys). Guarantees a bounded response no matter what reductus returns."""
    compacted, text = value, None
    for max_items, max_str, max_keys in _COMPACTION_TIERS:
        compacted = _compact_metadata(value, max_items, max_str, max_keys)
        text = json.dumps(compacted, default=str)
        if len(text) <= max_chars:
            return compacted
    return {
        "_truncated_result": text[:max_chars],
        "_note": (
            f"result still {len(text)} chars after maximum compaction; "
            "shown as truncated JSON. Request a narrower slice (e.g. a "
            "specific target_node/target_terminal) for full detail."
        ),
    }


@mcp.tool()
def get_file_intent(
    instrument_id: str,
    path: str,
    mtime: int,
    source: str = "ncnr",
    template_name: str | None = None,
) -> list[dict]:
    """Determine the measurement intent of a single raw data file without a full
    reduction. Intents are instrument-specific, e.g. 'specular'/'background+'/
    'intensity'/'rock sample' for reflectometers/CANDOR, or 'sample'/'empty'/
    'blocked beam' for SANS/VSANS. Handles ONE file per call — for several, issue
    calls in parallel. path/mtime/source come from find_raw_data_paths;
    template_name picks the loader when an instrument has multiple raw formats.
    Returns {"filename","intent","metadata"} per dataset."""
    fast = _search_intent_via_metadata(path, source)
    if fast is not None:
        return fast

    instrument = reductus_api.get_instrument(instrument_id)
    templates = instrument.get("templates", {})
    if template_name:
        candidate_names = [template_name]
    elif "load" in templates:
        # Prefer a template literally named "load" (e.g. ncnr.sans, ncnr.vsans):
        # it does nothing but load raw files, so it's cheaper and less brittle
        # than reduction templates that happen to have a load node too.
        candidate_names = ["load"] + [n for n in templates if n != "load"]
    else:
        candidate_names = list(templates)

    template_def = load_node = resolved_name = None
    for name in candidate_names:
        if name not in templates:
            raise ValueError(
                f"Unknown template {name!r} for {instrument_id!r}; "
                f"available: {sorted(templates)}"
            )
        candidate_def, load_nodes = _load_file_nodes(instrument_id, name)
        if load_nodes:
            template_def, load_node, resolved_name = candidate_def, load_nodes[0], name
            break

    if load_node is None:
        raise ValueError(
            f"No file-loading module found for instrument {instrument_id!r}"
            + (f", template {template_name!r}" if template_name else "")
        )

    template_def["name"] = resolved_name
    template_def.setdefault("description", resolved_name)
    template_def["instrument"] = instrument_id

    # Reduction templates bake a fixed intent into each load node's config so
    # that node reduces one measurement role: e.g. ncnr.refl's 'candor'
    # template pins node 0 to intent='intensity', and other nodes to
    # 'specular'/'background+'/'background-'. If we inherit that, the loader
    # overwrites the file's own intent (from trajectoryData/_scanType) with the
    # node's role, so every file would just echo the config (all 'intensity').
    # Reset the resolved load node to intent='auto' so it reports the file's
    # actual measured intent instead. Only touches nodes that already carry an
    # intent field, so load-only templates (ncnr.sans/vsans) are unaffected.
    load_cfg = template_def["modules"][load_node["node"]].setdefault("config", {})
    if "intent" in load_cfg:
        load_cfg["intent"] = "auto"

    config = {
        str(load_node["node"]): {
            "filelist": [_sanitize_fileinfo({"path": path, "mtime": mtime, "source": source})]
        }
    }
    metadata = reductus_api.calc_terminal(
        template_def, config, load_node["node"], "output", return_type="metadata",
    )
    result = _fit_result([
        {
            "filename": _first_present(v, _FILENAME_KEYS),
            "intent": _first_present(v, _INTENT_KEYS),
            "metadata": v,
        }
        for v in metadata.get("values", [])
    ])
    # _fit_result's last-resort fallback is a dict; keep the declared list shape.
    return result if isinstance(result, list) else [result]


# NeXus/NCNR paths that commonly hold human-readable "what is this trial" info.
# Only those present in a given file are kept (layouts vary by instrument).
_CURATED_PATHS = (
    "title", "experiment_description", "experiment_identifier",
    "start_time", "end_time", "duration", "program_name",
    "sample/name", "sample/description", "sample/chemical_formula",
    "user/name", "user/email", "user/facility_user_id",
    "DAS_logs/trajectoryData/fileName",
    "DAS_logs/trajectoryData/experimentTitle",
    "DAS_logs/trajectoryData/experiment",
    "DAS_logs/trajectoryData/_scanType",
    "DAS_logs/trajectoryData/annotation",
    "DAS_logs/trajectoryData/description",
    "DAS_logs/experiment/title",
    "DAS_logs/experiment/proposalId",
    "DAS_logs/sample/name",
    "DAS_logs/sample/description",
)

# Dataset-name substrings that flag a free-text descriptive field, so the
# keyword scan captures descriptions whose exact path isn't in _CURATED_PATHS.
_H5_DESC_KEYWORDS = (
    "title", "description", "comment", "annotation", "note", "purpose",
    "identifier", "proposal", "sample", "user", "experiment",
)

_H5_MAX_STR = 2000            # cap a single decoded string
_H5_STRUCT_MAX_DEPTH = 4      # structure-outline depth cap
_H5_STRUCT_MAX_NODES = 400    # structure-outline node-count cap
_H5_SCAN_MAX_NODES = 2000     # keyword-scan node-count cap


def _h5_scalar(x):
    """Decode a single h5py element (bytes/str/number) to a JSON-friendly value."""
    import numpy as np
    if isinstance(x, bytes):
        return x.decode("utf-8", "replace")[:_H5_MAX_STR]
    if isinstance(x, np.bytes_):
        return bytes(x).decode("utf-8", "replace")[:_H5_MAX_STR]
    if isinstance(x, (str, np.str_)):
        return str(x)[:_H5_MAX_STR]
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, (int, float, bool)):
        return x
    return None


def _h5_read_value(node):
    """Decode an h5py dataset into a JSON-friendly scalar/string/short list.
    Length-1 arrays are unwrapped, longer arrays truncated to 8 items, and
    unreadable values return None. Used for curated fields and `fields` reads."""
    import numpy as np
    try:
        val = node[()] if hasattr(node, "shape") else node
    except Exception:
        return None
    if isinstance(val, np.ndarray):
        flat = val.ravel()
        if flat.size == 0:
            return None
        if flat.size == 1:
            return _h5_scalar(flat[0])
        items = [_h5_scalar(x) for x in flat[:8].tolist()]
        items = [i for i in items if i is not None]
        if flat.size > 8:
            items.append(f"...(+{int(flat.size) - 8} more)")
        return items or None
    return _h5_scalar(val)


def _h5_structure(root):
    """Compact outline of an h5py group, walked breadth-first so shallow (more
    useful) nodes are shown before deep ones -- otherwise one huge group like
    DAS_logs starves its top-level siblings. Bounded by a global node cap and a
    depth cap; datasets report only shape+dtype, never bulk values."""
    out = {}
    queue = [(root, out, 0)]  # (h5py group, dict to populate, depth)
    budget = _H5_STRUCT_MAX_NODES
    while queue and budget > 0:
        group, target, depth = queue.pop(0)
        for name in group.keys():
            if budget <= 0:
                target["..."] = "truncated"
                break
            budget -= 1
            child = group[name]
            if hasattr(child, "items"):  # group
                if depth + 1 >= _H5_STRUCT_MAX_DEPTH:
                    target[name] = f"<group: {len(child)} children>"
                else:
                    sub = {}
                    target[name] = sub
                    queue.append((child, sub, depth + 1))
            else:  # dataset
                shape = tuple(getattr(child, "shape", ()) or ())
                target[name] = f"dataset {shape} {child.dtype}"
    return out


def _h5_scan_descriptions(group, prefix="", found=None, budget=None, seen=None):
    """Walk a group collecting string-valued datasets whose name looks
    descriptive (title/comment/sample/...), so free-text fields are captured
    even when their NeXus path varies by instrument. Keeps strings only and
    dedupes by value, so repeated boilerplate (e.g. identical DAS error-log
    descriptions) is recorded once."""
    if found is None:
        found = {}
    if budget is None:
        budget = [_H5_SCAN_MAX_NODES]
    if seen is None:
        seen = set()
    for name, child in group.items():
        if budget[0] <= 0:
            break
        budget[0] -= 1
        path = f"{prefix}{name}"
        if hasattr(child, "items"):
            _h5_scan_descriptions(child, path + "/", found, budget, seen)
        elif any(k in name.lower() for k in _H5_DESC_KEYWORDS):
            val = _h5_read_value(child)
            if isinstance(val, str) and val.strip() and val not in seen:
                seen.add(val)
                found[path] = val
    return found


def _h5_curated(entry):
    """Curated dict of human-readable trial fields: hardcoded NeXus/NCNR paths
    that are present, supplemented by the keyword scan for anything missed."""
    desc = {}
    for path in _CURATED_PATHS:
        try:
            node = entry.get(path)
        except Exception:
            node = None
        if node is None or hasattr(node, "items"):  # missing, or a group
            continue
        val = _h5_read_value(node)
        if val is not None and val != "":
            desc[path] = val
    for path, val in _h5_scan_descriptions(entry).items():
        desc.setdefault(path, val)
    return desc


@mcp.tool()
def inspect_raw_file(
    path: str,
    mtime: int,
    source: str = "ncnr",
    fields: list[str] | None = None,
) -> list[dict]:
    """Read information from INSIDE a raw NeXus/HDF5 data file -- the free-text
    descriptions, run comments/annotations, sample name/description, user and
    proposal, and any logged field -- that the harvested NCNR metadata DB does
    not expose (find_raw_data_paths/get_file_intent only see the DB's subset).

    path/mtime/source come straight from find_raw_data_paths. Handles ONE file
    per call -- for several, issue calls in parallel. Returns one dict per NeXus
    entry with "entry", a curated "description" of human-readable trial fields,
    and a compact "structure" outline of the file's groups/datasets. Pass
    `fields` with NeXus paths (e.g. from a prior structure, like
    "DAS_logs/trajectoryData/_scanType") to read those exact values back under
    "requested_fields"."""
    fileinfo = _sanitize_fileinfo({"path": path, "mtime": mtime, "source": source})
    raw = reductus_fetch.url_get(fileinfo)
    handle = h5_open_zip(os.path.basename(path), io.BytesIO(raw))
    try:
        # NeXus files hold one or more NXentry groups at the top level; when the
        # NX_class attr is present, keep only those, else treat every top-level
        # group as an entry (mirrors reflred/nexusref.py's load_nexus_entries).
        entries = []
        for name, group in handle.items():
            if not hasattr(group, "items"):
                continue
            nxclass = group.attrs.get("NX_class")
            if isinstance(nxclass, bytes):
                nxclass = nxclass.decode("utf-8", "replace")
            if nxclass and nxclass != "NXentry":
                continue
            entries.append((name, group))
        if not entries:
            entries = [(n, g) for n, g in handle.items() if hasattr(g, "items")]

        results = []
        for name, group in entries:
            record = {
                "entry": name,
                "description": _h5_curated(group),
                "structure": _h5_structure(group),
            }
            if fields:
                requested = {}
                for fpath in fields:
                    try:
                        node = group.get(fpath)
                        if node is None:
                            node = handle.get(fpath)
                    except Exception:
                        node = None
                    if node is None:
                        requested[fpath] = None
                    elif hasattr(node, "items"):
                        requested[fpath] = _h5_structure(node)
                    else:
                        requested[fpath] = _h5_read_value(node)
                record["requested_fields"] = requested
            results.append(record)
    finally:
        try:
            handle.close()
        except Exception:
            pass

    result = _fit_result(results)
    # _fit_result's last-resort fallback is a dict; keep the declared list shape.
    return result if isinstance(result, list) else [result]


if __name__ == "__main__":
    mcp.run(transport="stdio")