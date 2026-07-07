"""Smoke-test the reductus-related tools exposed by mcpServer.py.

Calls each tool function directly (bypassing the MCP/stdio transport) against
the real reductus API and the live NCNR metadata API / data server, so it
needs network access. Importing mcpServer.py also runs ensure_ollama(), so
Ollama must be installed (it will be started automatically if not running).

reduce_files is the most involved tool, so it gets the deepest coverage: beyond
the single-node SANS 'load' template (which only loads a file), the tests run a
genuine multi-node reflectometry reduction on a real CANDOR experiment --
routing a specular / background+ / background- / slit file set to the 'candor'
template's four load nodes and reducing all the way to the terminal rebin node
(exercising stitching, normalization, background subtraction, and rebinning).
That path also covers: sanitizing find_raw_data_paths' extra descriptor keys,
every return_type, whole-graph (target_node=None) vs. single-target
consistency, output compaction, and the template/node/mtime error paths.

Usage:
  python scripts/test_reductus_tools.py
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = REPO_ROOT / "scripts" / "mcpServer.py"

_spec = importlib.util.spec_from_file_location("mcpServer", MCP_SERVER)
mcpServer = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["mcpServer"] = mcpServer
_spec.loader.exec_module(mcpServer)  # type: ignore[union-attr]

# A real, published, small experiment used as a fixture for the network-backed tests.
FIXTURE_EXPERIMENT_ID = "nonims48"
FIXTURE_INSTRUMENT = "ng7sans"
FIXTURE_FILENAME = "sans50164.nxs.ng7"

# A real, published CANDOR reflectometry experiment (cycle 2020/09) with a
# complete specular + background + slit file set, used to drive a full
# multi-node reduction through the 'candor' template. The four files map to the
# template's four file-input nodes; their roles were verified against the NCNR
# metadata API's per-file trajectory intent codes (SLIT/SPEC/BGP/BGM), the same
# independent ground truth test_get_file_intent.py checks against.
REFL_EXPERIMENT_ID = "26362"
REFL_INSTRUMENT = "candor"
REFL_TEMPLATE = "candor"
REFL_NODE_FILES = {
    "0": "flowcell_si_popc_h2o2587.nxs.cdr",  # 'cdr slit'  (trajectory SLIT)
    "2": "flowcell_si_popc_h2o2584.nxs.cdr",  # 'cdr spec'  (trajectory SPEC)
    "3": "flowcell_si_popc_h2o2585.nxs.cdr",  # 'cdr back+' (trajectory BGP)
    "4": "flowcell_si_popc_h2o2586.nxs.cdr",  # 'cdr back-' (trajectory BGM)
}
# The 'candor' template's terminal node ('Candor Rebin'): reducing to it runs
# the entire graph (stitch -> join -> divide -> subtract background -> rebin).
REFL_FINAL_NODE = 12

results: list[tuple[str, bool, str]] = []

_refl_node_files_cache: dict[str, list[dict]] | None = None


def refl_node_files() -> dict[str, list[dict]]:
    """Build the candor template's node_files map from live file descriptors.

    Looks up the fixture experiment's files once (path/mtime/source are fetched
    fresh so the mtimes reductus requires are always current) and routes each
    fixture filename to its load node. The descriptors deliberately keep the
    extra keys find_raw_data_paths adds (filename/instrument/rxcycle_id/...), so
    passing them straight into reduce_files also exercises _sanitize_fileinfo.
    """
    global _refl_node_files_cache
    if _refl_node_files_cache is None:
        files = mcpServer.find_raw_data_paths(REFL_EXPERIMENT_ID, REFL_INSTRUMENT)
        by_name = {f["filename"]: f for f in files}
        node_files = {}
        for node, filename in REFL_NODE_FILES.items():
            assert filename in by_name, (
                f"fixture file {filename!r} not found in experiment "
                f"{REFL_EXPERIMENT_ID}; available e.g. {sorted(by_name)[:5]}"
            )
            node_files[node] = [by_name[filename]]
        _refl_node_files_cache = node_files
    return _refl_node_files_cache


def check(name):
    def decorator(fn):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - want to report any failure
            results.append((name, False, f"{exc!r}\n{traceback.format_exc(limit=3)}"))
        else:
            results.append((name, True, ""))
        return fn
    return decorator


@check("list_instruments returns known reductus instruments")
def _():
    instruments = mcpServer.list_instruments()
    assert isinstance(instruments, list) and instruments, "expected a non-empty list"
    assert "ncnr.sans" in instruments, instruments
    assert "ncnr.refl" in instruments, instruments


@check("get_instrument returns modules + templates")
def _():
    definition = mcpServer.get_instrument("ncnr.sans")
    assert "modules" in definition and definition["modules"]
    assert "templates" in definition and definition["templates"]


@check("list_datasources includes 'ncnr'")
def _():
    sources = mcpServer.list_datasources()
    names = [s["name"] for s in sources]
    assert "ncnr" in names, names


@check("list_data_files browses the top-level ncnr data source")
def _():
    metadata = mcpServer.list_data_files(source="ncnr", pathlist=[])
    assert "subdirs" in metadata and metadata["subdirs"], metadata


@check("find_raw_data_paths finds files with real path/source/mtime")
def _():
    files = mcpServer.find_raw_data_paths(FIXTURE_EXPERIMENT_ID, FIXTURE_INSTRUMENT)
    assert files, "expected at least one file"
    for f in files:
        assert isinstance(f["path"], str) and f["path"], f
        assert f["source"] == "ncnr", f
        assert isinstance(f["mtime"], int), f
    assert any(f["filename"] == FIXTURE_FILENAME for f in files), files


@check("list_reduction_templates finds the single-node 'load' template for ncnr.sans")
def _():
    templates = mcpServer.list_reduction_templates("ncnr.sans")
    assert "load" in templates, templates
    assert templates["load"] == [{"node": 0, "title": "Loadsans", "module": "ncnr.sans.LoadSANS", "intent": None}], \
        templates["load"]


@check("reduce_files rejects a node index that isn't a load node")
def _():
    try:
        mcpServer.reduce_files("ncnr.sans", "load", {"99": [{"path": "x", "source": "ncnr", "mtime": 1}]})
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for invalid node index")


@check("reduce_files rejects a file descriptor missing mtime")
def _():
    try:
        mcpServer.reduce_files("ncnr.sans", "load", {"0": [{"path": "x", "source": "ncnr"}]})
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for missing mtime")


@check("reduce_files runs a real end-to-end SANS load against the NCNR server")
def _():
    files = mcpServer.find_raw_data_paths(FIXTURE_EXPERIMENT_ID, FIXTURE_INSTRUMENT)
    sans_file = next(f for f in files if f["filename"] == FIXTURE_FILENAME)
    # find_raw_data_paths' output carries extra descriptive keys (filename,
    # instrument, ...); reduce_files must sanitize them down to what
    # reductus' fileinfo validator accepts, rather than erroring on them.
    output = mcpServer.reduce_files(
        "ncnr.sans", "load", {"0": [sans_file]},
        target_node=0, target_terminal="output", return_type="metadata",
    )
    assert output["datatype"] == "ncnr.sans.raw", output
    assert output["values"], "expected at least one loaded dataset"


@check("reduce_files with target_node=None (calc_template, whole-graph) works")
def _():
    # Regression test for a reductus bug: dataflow/calc.py's _key() returns
    # "module:terminal" strings, but web_gui/api.py's calc_template() used to
    # unpack each key as a 2-tuple (module_id, terminal_id = rkey), which
    # blew up with "too many values to unpack" for any multi-character key.
    # This path (target_node omitted) is exactly what reduce_files uses to
    # return every node's output, so it must exercise calc_template cleanly.
    files = mcpServer.find_raw_data_paths(FIXTURE_EXPERIMENT_ID, FIXTURE_INSTRUMENT)
    sans_file = next(f for f in files if f["filename"] == FIXTURE_FILENAME)
    output = mcpServer.reduce_files("ncnr.sans", "load", {"0": [sans_file]})
    assert output["0"]["output"]["datatype"] == "ncnr.sans.raw", output


@check("reduce_files rejects an unknown template_name")
def _():
    try:
        mcpServer.reduce_files(
            "ncnr.sans", "not_a_real_template",
            {"0": [{"path": "x", "source": "ncnr", "mtime": 1}]},
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for unknown template_name")


@check("reduce_files runs a full multi-node CANDOR reduction to the rebin node")
def _():
    # The real payoff: a genuine reduction, not just a file load. Route four
    # files (specular/background+/background-/slit) to the candor template's
    # load nodes and reduce all the way to the terminal 'Candor Rebin' node,
    # which forces the whole graph to run (stitch -> join -> divide ->
    # subtract background -> rebin). The final datatype is reduced reflectivity.
    output = mcpServer.reduce_files(
        "ncnr.refl", REFL_TEMPLATE, refl_node_files(),
        target_node=REFL_FINAL_NODE, target_terminal="output", return_type="metadata",
    )
    assert output["datatype"] == "ncnr.refl.refldata", output.get("datatype")
    assert output["values"], "expected at least one reduced dataset"


@check("reduce_files honors every return_type on the reduced output")
def _():
    node_files = refl_node_files()
    for return_type in ("metadata", "plottable", "export"):
        output = mcpServer.reduce_files(
            "ncnr.refl", REFL_TEMPLATE, node_files,
            target_node=REFL_FINAL_NODE, return_type=return_type,
        )
        assert isinstance(output, dict), (return_type, type(output))
        assert "datatype" in output and "values" in output, (return_type, sorted(output))
        assert output["values"], (return_type, "expected non-empty values")


@check("reduce_files compacts huge reduction arrays so the result stays small")
def _():
    # Reduced CANDOR reflectivity embeds full per-point Q/R/dR arrays that
    # pretty-print to 100KB+; every reduce_files response must come back under
    # _fit_result's fixed size budget or it blows out an LLM context window
    # (observed as the backend computing a negative max_tokens). The
    # whole-graph case is the worst offender: 13 nodes of 59-key metadata
    # dicts used to total ~420KB even with array truncation.
    import json
    budget = mcpServer._MAX_RESULT_CHARS + 1_000  # + wiggle for the fallback note
    output = mcpServer.reduce_files(
        "ncnr.refl", REFL_TEMPLATE, refl_node_files(),
        target_node=REFL_FINAL_NODE, return_type="metadata",
    )
    size = len(json.dumps(output, default=str))
    assert size < budget, f"single-target output not compacted: {size} chars"

    whole = mcpServer.reduce_files("ncnr.refl", REFL_TEMPLATE, refl_node_files())
    size = len(json.dumps(whole, default=str))
    assert size < budget, f"whole-graph output not compacted: {size} chars"


@check("reduce_files whole-graph reduction matches the single-target reduction")
def _():
    # target_node=None computes every node via _all_node_outputs (the path that
    # sidesteps reductus' broken calc_template); on a real multi-node template
    # it must (a) return an output for every node and (b) agree with the
    # single-target computation for the terminal node.
    node_files = refl_node_files()
    whole = mcpServer.reduce_files("ncnr.refl", REFL_TEMPLATE, node_files)
    assert set(whole) == {str(i) for i in range(13)}, sorted(whole, key=int)
    final = whole[str(REFL_FINAL_NODE)]["output"]
    assert final["datatype"] == "ncnr.refl.refldata", final.get("datatype")

    target = mcpServer.reduce_files(
        "ncnr.refl", REFL_TEMPLATE, node_files,
        target_node=REFL_FINAL_NODE, return_type="metadata",
    )
    assert final["datatype"] == target["datatype"], (final.get("datatype"), target.get("datatype"))
    assert len(final["values"]) == len(target["values"]), (len(final["values"]), len(target["values"]))


def main() -> int:
    width = max(len(name) for name, _, _ in results)
    failed = 0
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name.ljust(width)}")
        if not passed:
            failed += 1
            print(detail)

    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
