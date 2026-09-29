#!/usr/bin/env python3
"""Evaluate embedding-based retrieval (Chroma + Ollama embeddinggemma) using the
RAGAS-standard retrieval metrics: Context Precision@K and Context Recall.

Unlike the ragas package's non-LLM metrics (which infer relevance via fuzzy
text similarity between retrieved and reference context strings), this
implementation uses the exact `source_id` ground truth already present in
each pack's eval/*.jsonl `expected_sources` field -- stricter and simpler
than approximating the same judgment with string similarity.

Context Precision@K = sum_k(precision@k * relevant_k) / (num relevant in top K)
  where precision@k = (# relevant in top k) / k, relevant_k in {0, 1}
  defined as 0 if no relevant chunk appears in the top K
Context Recall = (# distinct expected_sources found in top K) / (# expected_sources)

Shares its retrieval pass with test_retrieval_embedding.py via eval_core.py
(see evaluate_pack_questions) so both scripts don't independently re-query
Chroma/Ollama for the same questions.

Requires scripts/embed_and_ingest.py to have been run first (populates ./chroma_db).

Usage:
  python scripts/evaluate_retrieval_ragas.py --evaluate-all --output-csv retrieval_results_ragas.csv
  python scripts/evaluate_retrieval_ragas.py candor --top 5 --detail
  python scripts/evaluate_retrieval_ragas.py candor --by workflow_stage
"""

from __future__ import annotations

import argparse
import datetime
from pathlib import Path

from _common import PACKS, add_eval_cli_args, append_csv_rows, git_commit_short, open_vectorstore, write_csv
from eval_core import evaluate_pack_questions, ragas_metrics, slice_breakdown

EVAL_CSV_FIELDS = [
    "run_date", "git_commit", "embed_model", "pack", "top_n", "queries",
    "mean_context_precision", "mean_context_recall",
]
SLICE_CSV_FIELDS = [
    "run_date", "git_commit", "pack", "slice_type", "slice_value",
    "queries", "mean_context_precision", "mean_context_recall",
]


def _slice_rows(pack_name: str, details: list, slice_type: str, run_date: str, commit: str) -> list[dict]:
    rows = []
    for value, group in sorted(slice_breakdown(details, slice_type).items()):
        m = ragas_metrics(group)
        rows.append({
            "run_date": run_date, "git_commit": commit, "pack": pack_name,
            "slice_type": slice_type, "slice_value": value, "queries": m["queries"],
            "mean_context_precision": m["mean_context_precision"], "mean_context_recall": m["mean_context_recall"],
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval using RAGAS-standard Context Precision/Recall.")
    add_eval_cli_args(parser, "retrieval_results_ragas.csv")
    parser.add_argument("--by", choices=["workflow_stage", "software"], default=None,
                         help="Print a breakdown by expected_workflow_stage or expected_software instead of one aggregate.")
    parser.add_argument("--slices-csv", default=None,
                         help="CSV path for per-slice breakdown rows (default: <output-csv stem>_slices.csv; written whenever --evaluate-all is used).")
    parser.add_argument("--overwrite-csv", action="store_true",
                         help="Overwrite the output CSV instead of appending a new run's rows to it.")
    parser.add_argument("--use-production-retrieval", action="store_true", dest="use_prod",
                         help="Exercise gen_chunks.retrieve() (the real path mcpServer.py calls) instead of a "
                              "hand-rolled fetch/filter, so max-distance/access-level behavior is measured too.")
    parser.add_argument("--max-distance", type=float, default=0.5, dest="max_distance",
                         help="Only used with --use-production-retrieval (default: 0.5).")
    parser.add_argument("--access-level", default="public", dest="access_level",
                         choices=["public", "internal", "restricted"],
                         help="Only used with --use-production-retrieval (default: public).")
    args = parser.parse_args()

    root = Path.cwd()
    vectorstore, embedder = open_vectorstore()

    retrieve_fn = None
    if args.use_prod:
        from gen_chunks import retrieve as retrieve_fn  # noqa: F811 (deliberate shadow)

    run_date = datetime.date.today().isoformat()
    commit = git_commit_short()

    def run_pack(pack_name: str) -> list[dict]:
        return evaluate_pack_questions(
            pack_name, root, vectorstore, embedder, args.top,
            retrieve_fn=retrieve_fn, max_distance=args.max_distance, access_level=args.access_level,
        )

    if args.evaluate_all:
        rows, slice_rows = [], []
        for pack_name in PACKS:
            details = run_pack(pack_name)
            if not details:
                print(f"{pack_name}: no eval questions — skipped")
                continue
            m = ragas_metrics(details)
            rows.append({
                "run_date": run_date, "git_commit": commit, "embed_model": "embeddinggemma",
                "pack": pack_name, "top_n": args.top, "queries": m["queries"],
                "mean_context_precision": m["mean_context_precision"], "mean_context_recall": m["mean_context_recall"],
            })
            slice_rows += _slice_rows(pack_name, details, "expected_workflow_stage", run_date, commit)
            slice_rows += _slice_rows(pack_name, details, "expected_software", run_date, commit)
            print(f"{pack_name}: context_precision@{args.top}={m['mean_context_precision']:.3f} "
                  f"context_recall={m['mean_context_recall']:.3f} (n={m['queries']})")

        writer = write_csv if args.overwrite_csv else append_csv_rows
        writer(rows, EVAL_CSV_FIELDS, Path(args.output_csv))
        print(f"{'Wrote' if args.overwrite_csv else 'Appended'} {args.output_csv}")

        slices_csv = Path(args.slices_csv) if args.slices_csv else Path(args.output_csv).with_name(Path(args.output_csv).stem + "_slices.csv")
        writer(slice_rows, SLICE_CSV_FIELDS, slices_csv)
        print(f"{'Wrote' if args.overwrite_csv else 'Appended'} {slices_csv}")
        return 0

    if not args.pack:
        print("ERROR: pack is required unless --evaluate-all is used.")
        return 2

    details = run_pack(args.pack)
    if not details:
        print(f"{args.pack}: no eval questions found.")
        return 0
    m = ragas_metrics(details)
    print(f"RAGAS-standard retrieval evaluation for top {args.top}")
    print(f"  queries: {m['queries']}")
    print(f"  mean Context Precision@{args.top}: {m['mean_context_precision']:.3f}")
    print(f"  mean Context Recall: {m['mean_context_recall']:.3f}")

    if args.by:
        slice_key = "expected_workflow_stage" if args.by == "workflow_stage" else "expected_software"
        print("-" * 80)
        for value, group in sorted(slice_breakdown(details, slice_key).items()):
            gm = ragas_metrics(group)
            print(f"  [{value}] n={gm['queries']} precision={gm['mean_context_precision']:.3f} recall={gm['mean_context_recall']:.3f}")

    if args.detail:
        print("-" * 80)
        for d in details:
            precision = ragas_metrics([d])["mean_context_precision"]
            recall = ragas_metrics([d])["mean_context_recall"]
            matched = sorted(set(d["expected_sources"]) & set(d["retrieved_source_ids"]))
            missed = sorted(set(d["expected_sources"]) - set(d["retrieved_source_ids"]))
            print(f"question_id: {d['question_id']}")
            print(f"  query: {d['query']}")
            print(f"  expected_sources: {d['expected_sources']}")
            print(f"  retrieved_source_ids: {d['retrieved_source_ids']}")
            print(f"  matched: {matched}  missed: {missed}")
            print(f"  context_precision: {precision:.3f}  context_recall: {recall:.3f}")
            print("-" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
