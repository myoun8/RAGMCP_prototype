#!/usr/bin/env python3
"""Evaluate embedding-based retrieval (Chroma + Ollama embeddinggemma) against each
pack's eval/*.jsonl questions: top-1/top-k/all-sources accuracy and MRR.

Requires scripts/embed_and_ingest.py to have been run first (populates ./chroma_db).

Usage:
  python scripts/test_retrieval_embedding.py --evaluate-all --output-csv retrieval_results_embedding.csv
  python scripts/test_retrieval_embedding.py candor --detail
  python scripts/test_retrieval_embedding.py candor --by workflow_stage
  python scripts/test_retrieval_embedding.py --evaluate-all --use-production-retrieval --max-distance 0.5
"""

from __future__ import annotations

import argparse
import datetime
from pathlib import Path

from _common import PACKS, add_eval_cli_args, append_csv_rows, git_commit_short, open_vectorstore, write_csv
from eval_core import evaluate_pack_questions, slice_breakdown, topk_metrics

EVAL_CSV_FIELDS = [
    "run_date", "git_commit", "embed_model", "pack", "top_n", "queries",
    "top1_accuracy", "topk_accuracy", "all_sources_accuracy", "mrr",
    "avg_query_time", "p50_query_time", "p95_query_time", "total_query_time",
]
SLICE_CSV_FIELDS = [
    "run_date", "git_commit", "pack", "slice_type", "slice_value",
    "queries", "top1_accuracy", "topk_accuracy", "mrr",
]


def _print_metrics(label: str, m: dict) -> None:
    print(f"{label}: top1={m['top1_accuracy']:.3f} topk={m['topk_accuracy']:.3f} "
          f"all_sources={m['all_sources_accuracy']:.3f} mrr={m['mrr']:.3f} "
          f"(n={m['queries']}, p50={m['p50_query_time']*1000:.0f}ms, p95={m['p95_query_time']*1000:.0f}ms)")


def _slice_rows(pack_name: str, details: list, slice_type: str, run_date: str, commit: str) -> list[dict]:
    rows = []
    for value, group in sorted(slice_breakdown(details, slice_type).items()):
        m = topk_metrics(group)
        rows.append({
            "run_date": run_date, "git_commit": commit, "pack": pack_name,
            "slice_type": slice_type, "slice_value": value, "queries": m["queries"],
            "top1_accuracy": m["top1_accuracy"], "topk_accuracy": m["topk_accuracy"], "mrr": m["mrr"],
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate embedding-based retrieval against pack eval questions.")
    add_eval_cli_args(parser, "retrieval_results_embedding.csv")
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
            m = topk_metrics(details)
            rows.append({
                "run_date": run_date, "git_commit": commit, "embed_model": "embeddinggemma",
                "pack": pack_name, "top_n": args.top, "queries": m["queries"],
                "top1_accuracy": m["top1_accuracy"], "topk_accuracy": m["topk_accuracy"],
                "all_sources_accuracy": m["all_sources_accuracy"], "mrr": m["mrr"],
                "avg_query_time": m["avg_query_time"], "p50_query_time": m["p50_query_time"],
                "p95_query_time": m["p95_query_time"], "total_query_time": m["total_query_time"],
            })
            slice_rows += _slice_rows(pack_name, details, "expected_workflow_stage", run_date, commit)
            slice_rows += _slice_rows(pack_name, details, "expected_software", run_date, commit)
            _print_metrics(pack_name, m)

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
    m = topk_metrics(details)
    print(f"Evaluation results for top {args.top}")
    print(f"  queries: {m['queries']}")
    print(f"  top-1 accuracy: {m['top1_accuracy']:.3f}")
    print(f"  top-{args.top} accuracy: {m['topk_accuracy']:.3f}")
    print(f"  all-sources accuracy: {m['all_sources_accuracy']:.3f}")
    print(f"  mean reciprocal rank: {m['mrr']:.3f}")
    print(f"  query time avg/p50/p95: {m['avg_query_time']*1000:.0f}/{m['p50_query_time']*1000:.0f}/{m['p95_query_time']*1000:.0f} ms")

    if args.by:
        slice_key = "expected_workflow_stage" if args.by == "workflow_stage" else "expected_software"
        print("-" * 80)
        for value, group in sorted(slice_breakdown(details, slice_key).items()):
            gm = topk_metrics(group)
            print(f"  [{value}] n={gm['queries']} top1={gm['top1_accuracy']:.3f} topk={gm['topk_accuracy']:.3f} mrr={gm['mrr']:.3f}")

    if args.detail:
        print("-" * 80)
        for d in details:
            print(f"question_id: {d['question_id']}")
            print(f"  query: {d['query']}")
            print(f"  workflow_stage: {d['expected_workflow_stage']}  software: {d['expected_software']}")
            print(f"  expected_sources: {d['expected_sources']}")
            print(f"  top_hit_rank: {d['hit_rank']}  all_hit: {d['all_hit']}")
            print(f"  retrieved_source_ids: {d['retrieved_source_ids']}")
            print("-" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
