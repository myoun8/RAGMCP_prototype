"""Test mcpServer.get_file_intent against real NCNR reflectometry data.

Calls get_file_intent directly (bypassing the MCP/stdio transport) against the
real reductus API and the live NCNR metadata API / data server, so it needs
network access. Importing mcpServer.py also runs ensure_ollama(), so Ollama
must be installed (it will be started automatically if not running).

Scoped to reflectometer/CANDOR (ncnr.refl), whose loader returns a clean
top-level "intent"/"filename" plus large per-point arrays that must be
truncated by _compact_metadata.

Also checks intent *accuracy*, not just presence: the NCNR metadata API
reports a per-file trajectory intent code (SPEC/SLIT/BGP/BGM/ROCK) that is
derived independently of reductus' loader, so it serves as ground truth.
get_file_intent's returned intent must match it via reductus' own
TRAJECTORY_INTENTS mapping. (Regression guard: the 'candor' reduction template
pins each load node to a fixed intent in its config -- node 0 to 'intensity' --
which used to leak through and make every file report 'intensity'.)

Also covers the two error paths: unknown instrument_id and unknown template_name.

Usage:
  python scripts/test_get_file_intent.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = REPO_ROOT / "scripts" / "mcpServer.py"

_spec = importlib.util.spec_from_file_location("mcpServer", MCP_SERVER)
mcpServer = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["mcpServer"] = mcpServer
_spec.loader.exec_module(mcpServer)  # type: ignore[union-attr]

get_file_intent = mcpServer.get_file_intent
find_raw_data_paths = mcpServer.find_raw_data_paths

# Real, published fixture: a CANDOR reflectometry experiment (cycle 2020/09).
REFL_EXPERIMENT_ID = "26362"
REFL_INSTRUMENT = "candor"

NCNR_METADATA_API = "https://ncnr.nist.gov/ncnrdata/metadata/api/v1"

# Ground-truth map from the NCNR metadata API's per-file trajectory intent code
# to the human-readable intent reductus' loader assigns. This mirrors reductus'
# own reflred/nexusref.py TRAJECTORY_INTENTS -- duplicated here on purpose so
# the test pins the expected values independently of the code under test.
API_INTENT_TO_REDUCTUS = {
    "SPEC": "specular",
    "SLIT": "intensity",
    "BGP": "background+",
    "BGM": "background-",
    "ROCK": "rock sample",
}

results: list[tuple[str, bool, str]] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    results.append((label, bool(condition), detail))
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail else ""))


def run_case(label: str, fn):
    print(f"\n--- {label} ---")
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - want to report any failure
        print(f"  raised {type(exc).__name__}: {exc}")
        traceback.print_exc(limit=3)
        results.append((label, False, f"unexpected exception: {exc!r}"))
        return None


def run_case_expect_error(label, fn, expected_types=(ValueError,)) -> None:
    names = "/".join(t.__name__ for t in expected_types)
    print(f"\n--- {label} (expect {names}) ---")
    try:
        out = fn()
    except expected_types as exc:
        check(label, True, f"raised {type(exc).__name__}: {str(exc)[:160]}")
    except Exception as exc:  # noqa: BLE001
        check(label, False, f"raised {type(exc).__name__} instead of {names}: {exc}")
    else:
        check(label, False, f"expected an exception, got: {str(out)[:160]}")


def api_intent_fixtures(file_descriptors):
    """Map each ground-truth API intent code to one representative file.

    Queries the NCNR metadata API for the experiment's datafiles, reads each
    file's own trajectory `intent` code (independent of reductus' loader), and
    returns {api_code: file_descriptor} picking one file per code we know how
    to map (see API_INTENT_TO_REDUCTUS). file_descriptors is the
    find_raw_data_paths output, used to recover path/mtime/source by filename.
    """
    resp = requests.get(
        f"{NCNR_METADATA_API}/datafiles",
        params={"experiment_id": REFL_EXPERIMENT_ID, "instrument": REFL_INSTRUMENT, "limit": 500},
        timeout=30,
    )
    resp.raise_for_status()
    by_name = {d["filename"]: d for d in file_descriptors}

    fixtures = {}
    for row in resp.json():
        name = row["filename"]
        if name not in by_name or not row.get("metadata"):
            continue
        code = json.loads(row["metadata"]).get("intent")
        if code in API_INTENT_TO_REDUCTUS and code not in fixtures:
            fixtures[code] = by_name[name]
    return fixtures


def main() -> int:
    # 1. CANDOR/reflectometer file. instrument_id 'ncnr.refl' has no template
    #    literally named "load", so the default auto-pick must land on the
    #    'candor' template's dedicated loader on its own.
    refl_files = run_case(
        f"find_raw_data_paths({REFL_EXPERIMENT_ID!r}, instrument={REFL_INSTRUMENT!r})",
        lambda: find_raw_data_paths(REFL_EXPERIMENT_ID, instrument=REFL_INSTRUMENT),
    )
    if refl_files:
        # find_raw_data_paths returns every file under the experiment, including
        # non-data entries like queue/queue and queue_page.N that aren't loadable
        # NeXus files -- pick a real CANDOR data file (.nxs.cdr under /data/).
        f = next(
            (x for x in refl_files if "/data/" in x["path"] and x["path"].endswith(".nxs.cdr")),
            None,
        )
        if f is None:
            check("found a .nxs.cdr data file in experiment", False, f"none among {len(refl_files)} files")
            refl_files = None
    if refl_files:
        print(f"  using file: {f['path']} (mtime={f['mtime']})")

        out = run_case(
            "get_file_intent on CANDOR file, default template",
            lambda: get_file_intent("ncnr.refl", f["path"], f["mtime"], f["source"]),
        )
        if out is not None:
            check("returns non-empty list", isinstance(out, list) and len(out) > 0, str(out)[:160])
            if out:
                check("first result has 'intent' set", out[0].get("intent") is not None, json.dumps(out[0])[:200])
                check("first result has 'filename' set", out[0].get("filename") is not None)
                # _compact_metadata truncates individual long arrays/strings;
                # raw CANDOR metadata for one file is 100KB+, so anything well
                # under that confirms truncation is actually happening.
                mlen = len(json.dumps(out[0]["metadata"]))
                check("metadata is compacted (well under raw ~100KB+ size)", mlen < 50_000, f"metadata json length={mlen}")

        out2 = run_case(
            "get_file_intent on CANDOR file, explicit template_name='candor'",
            lambda: get_file_intent("ncnr.refl", f["path"], f["mtime"], f["source"], template_name="candor"),
        )
        if out2 is not None and out is not None:
            # dict `==` can spuriously differ on float('nan') fields (nan != nan)
            # even when the JSON representation is identical, so compare as JSON.
            check(
                "explicit template_name='candor' matches auto-picked default",
                json.dumps(out2, sort_keys=True) == json.dumps(out, sort_keys=True),
            )

    # 2. Intent ACCURACY. For each intent code the metadata API reports on a
    #    real file (SPEC/SLIT/BGP/BGM/ROCK), get_file_intent must return the
    #    matching human-readable intent. This is what caught the reduction-
    #    template intent leak, where every file wrongly reported 'intensity'.
    if refl_files:
        fixtures = run_case(
            "fetch API ground-truth intents for experiment",
            lambda: api_intent_fixtures(refl_files),
        )
        if fixtures:
            missing = sorted(set(API_INTENT_TO_REDUCTUS) - set(fixtures))
            if missing:
                print(f"  (note: no files with API intent(s) {missing} in this experiment)")
            for code, fd in sorted(fixtures.items()):
                expected = API_INTENT_TO_REDUCTUS[code]
                out = run_case(
                    f"get_file_intent intent == {expected!r} for API {code!r} ({fd['filename']})",
                    lambda fd=fd: get_file_intent("ncnr.refl", fd["path"], fd["mtime"], fd["source"]),
                )
                if out is not None:
                    got = {r.get("intent") for r in out}
                    # A file yields >=1 dataset; every one should carry the
                    # file's single true intent (multi-entry files repeat it).
                    check(
                        f"API {code!r} -> intent {expected!r}",
                        got == {expected},
                        f"got {sorted(got)!r}",
                    )

    # 3. Unknown instrument_id. reductus_api.get_instrument() does a raw dict
    #    lookup with no validation, so this surfaces as KeyError, not the
    #    ValueError get_file_intent raises for a bad template_name. Documenting
    #    actual behavior, not asserting KeyError is the ideal contract.
    run_case_expect_error(
        "get_file_intent with bogus instrument_id",
        lambda: get_file_intent("ncnr.doesnotexist", "some/path", 123456, "ncnr"),
        expected_types=(KeyError, ValueError),
    )

    # 4. Unknown explicit template_name should raise ValueError naming the
    #    available templates.
    run_case_expect_error(
        "get_file_intent with bogus template_name",
        lambda: get_file_intent("ncnr.refl", "some/path", 123456, "ncnr", template_name="not_a_real_template"),
        expected_types=(ValueError,),
    )

    # Summary
    print("\n=== SUMMARY ===")
    width = max(len(label) for label, _, _ in results)
    failed = 0
    for label, passed, _ in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {label.ljust(width)}")
        if not passed:
            failed += 1
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
