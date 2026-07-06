"""Smoke-test the reductus-related tools exposed by mcpServer.py.

Calls each tool function directly (bypassing the MCP/stdio transport) against
the real reductus API and the live NCNR metadata API / data server, so it
needs network access. Importing mcpServer.py also runs ensure_ollama(), so
Ollama must be installed (it will be started automatically if not running).

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

results: list[tuple[str, bool, str]] = []


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
