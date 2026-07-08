from fastmcp import FastMCP
import copy
import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path

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
    return f"{REDUCTUS_APP_URL}?{urlencode(params)}"


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
) -> str:
    """Build an interactive Plotly figure from Python plotting code, save it as
    a Plotly figure-JSON file, and return an HTML placeholder the UI renders
    into a live, zoomable chart. Use this to visualize numeric data — e.g.
    reduced reflectivity/SANS curves from reduce_files, a scan's intensity vs.
    angle, or any x/y arrays the user provides or that another tool returned.

    `code` is a snippet of Python that builds ONE Plotly figure and assigns it
    to a variable named `fig`. It runs with these names already imported, so do
    not re-import them:
      - `go`   -> plotly.graph_objects
      - `px`   -> plotly.express
      - `np`   -> numpy
    Put the data to plot inline in the code (as literal lists/arrays). Do NOT
    call fig.show() or write any file — the figure is serialized for you.
    Example:

        x = [0.01, 0.02, 0.03, 0.04]
        y = [1.0, 0.42, 0.11, 0.03]
        fig = go.Figure(go.Scatter(x=x, y=y, mode='lines+markers'))
        fig.update_xaxes(title_text='Q (1/Å)')
        fig.update_yaxes(title_text='Reflectivity', type='log')

    `title` (optional) is set as the figure title.

    When the plotted data comes from reduction/raw NCNR data, pass the reductus
    context so the UI can deep-link the chart to the reductus web app:
      - `reductus_instrument` — instrument_id like 'ncnr.refl' or 'ncnr.candor'
        (the same value you passed to reduce_files/find_raw_data_paths).
      - `reductus_path` — the directory the raw files live in (the parent path
        from find_raw_data_paths), so reductus opens that folder in its browser.
      - `reductus_source` — datasource name, defaults to 'ncnr'.
    Omit these for ad-hoc/user-supplied data; the link then points at the
    reductus homepage.

    Returns an HTML placeholder like
    <div class="plotly-figure" data-src="/static/generated/<id>.json"></div>.
    Include that exact snippet verbatim in your reply so the user sees the plot.
    """
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
    """Find the raw data files belonging to an NCNR experiment, given its
    experiment_id (and optionally an instrument alias, e.g. 'candor', 'macs',
    'bt1', to narrow the search if the experiment_id alone is ambiguous).

    Queries the NCNR metadata API (/datafiles), which reports the authoritative
    "localdir" for each file, then looks up each directory's real file mtimes
    via list_data_files (reductus requires an exact mtime on every file
    descriptor it loads). Returns a list of
    {"path", "source", "mtime", "filename", "instrument", "rxcycle_id",
    "start_date", "intent", "download_url"} per file, ready to use directly as a
    file descriptor in reduce_files' node_files, or as a pathlist prefix for
    list_data_files. only display 20 files unless the user specifies otherwise.

    "download_url" is a relative link (served by the app's /download/raw proxy)
    that streams the original raw file to the browser as a download. Surface it
    as a Markdown link when the user wants to download raw data files.

    "intent" is the file's measurement role read straight from the metadata DB
    (no file load): reflectometer/CANDOR files report a mapped intent like
    'specular'/'intensity'/'background+'/'background-'/'rock sample'; VSANS files
    report their file_purpose ('scattering'/'transmission') as a hint. It is null
    when the DB has not harvested an intent for the file (e.g. findpeak/alignment
    scans, or instruments like BT1) -- use get_file_intent to load those, and for
    the true VSANS Sample/Empty/Blocked/Open intent."""
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
    Try to not use the general template whenever possible. Prompt the user to provide the template name or instrument.

    If target_node is omitted, every node's output terminal(s) are computed and
    returned as compact per-node summaries (datatype plus filename/intent per
    dataset) -- call again with target_node to get a single node's full
    (compacted) output. return_type applies in both cases:
    'full' | 'plottable' | 'metadata' | 'export'. Results are always truncated
    to a fixed size budget so they fit in a model context window.

    Returns {"reduction": <node output(s) as described above>, "reductus_url":
    <deep link>}. `reductus_url` opens this instrument + data folder directly in
    the reductus web app; when you then plot this data with generate_plot, pass
    reductus_instrument=instrument_id and reductus_path (the files' folder) so
    the chart's "Open in Reductus" link matches.
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
        reduction = _fit_result(_all_node_outputs(instrument_id, template_def, config, return_type))
    else:
        reduction = _fit_result(reductus_api.calc_terminal(
            template_def, config, target_node, target_terminal, return_type=return_type,
        ))
    return {
        "reduction": reduction,
        "reductus_url": _reductus_url(instrument_id, _reductus_folder(node_files)),
    }


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
    """Export a reduced dataset to a downloadable ORSO file and return its
    download URL.

    Reduce files exactly as reduce_files does — same instrument_id,
    template_name, node_files (each load node index as a string mapping to a
    list of {"path","mtime","source"} descriptors), and target_node /
    target_terminal — then write that node's reduced output to an ORSO file the
    user can save:

      - export_format='orso_text'  -> ORSO text  (.ort)
      - export_format='orso_nexus' -> ORSO Nexus (.orb, HDF5)

    target_node must be the FINAL reduced node (the one whose curve you'd plot),
    not a raw load node — an ORSO reflectivity file needs the reduced R(Q), not
    unreduced input. Returns {"download_url", "filename", "format",
    "reductus_url"}; render download_url as a Markdown link, e.g.
    [<filename>](<download_url>), so the user can download the export, and offer
    reductus_url as an "Open in reductus" link so they can inspect/re-reduce the
    same data in the web app. Do not invent the URLs — use the ones returned."""
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
    """Determine the measurement intent of a single raw data file by loading
    just its header, without running a full reduction. Intent values are
    instrument-family specific, e.g. 'specular'/'background+'/'background-'/
    'intensity'/'rock sample'/'rock detector'/'slit'/'scan' for reflectometers
    and CANDOR, or 'sample'/'empty'/'open beam'/'blocked beam' for SANS/VSANS.

    Use this to figure out what a raw data file IS -- e.g. to answer "what is
    the intent of this file?" -- or to decide which reduce_files node/role a
    file belongs in, before calling reduce_files.

    Handles ONE file per call. For several files, get all their path/mtime in a
    single find_raw_data_paths call, then issue one get_file_intent call per
    file all together in the same turn — the calls are independent and run in
    parallel, so do not wait for one to return before issuing the next.

    instrument_id is like 'ncnr.refl' or 'ncnr.sans' (see list_instruments).
    path/mtime/source identify the file the same way as in
    find_raw_data_paths/list_data_files output (mtime is required by reductus).

    template_name picks which loader module to use, in case an instrument_id
    has multiple incompatible raw-file formats/loaders across its templates
    (e.g. 'ncnr.refl' has a 'candor' template with a CANDOR-specific loader,
    separate from the generic NeXus loader used by its other templates). If
    omitted, the first template with a file-loading node is used -- pass an
    explicit template_name (see list_reduction_templates) if that guess loads
    the wrong kind of file.

    Returns one {"filename", "intent", "metadata"} dict per dataset found in
    the file (usually one, but polarized/multi-part files can yield several).
    "metadata" is the rest of that dataset's metadata, in case the caller
    needs a field beyond filename/intent; long per-point arrays inside it
    (e.g. angle/intensity arrays) are truncated to a short sample so the
    response stays small.

    Fast path: the file's intent is first looked up in the NCNR metadata DB
    (by filename, no file load). If the DB has a non-empty intent, it is
    returned directly as a single-entry list, with "metadata" being the DB's
    harvested fields. The DB carries one intent per file, so this path does not
    split polarized/multi-part files into per-dataset entries (their intent is
    uniform anyway). When the DB has no intent for the file (e.g. findpeak/
    alignment scans, un-harvested instruments like BT1, or the true VSANS
    Sample/Empty/Blocked/Open intent, which the DB does not store), it falls
    back to loading the file through reductus as described above. template_name
    only affects that fallback load.
    """
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


if __name__ == "__main__":
    mcp.run(transport="stdio")