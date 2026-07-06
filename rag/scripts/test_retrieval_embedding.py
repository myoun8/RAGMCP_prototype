#!/usr/bin/env python3
"""Evaluate embedding-based retrieval (Chroma + Ollama nomic-embed-text) against the
same eval questions used by test_retrieval.py, for apples-to-apples comparison
with the TF-IDF baseline.

Requires scripts/embed_and_ingest.py to have been run first (populates ./chroma_db).

Usage:
  python scripts/test_retrieval_embedding.py --evaluate-all --output-csv retrieval_results_embedding.csv
  python scripts/test_retrieval_embedding.py candor --detail
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from _common import PACKS, QUERY_PREFIX, add_eval_cli_args, load_eval_questions, load_pack_chunk_ids, open_vectorstore, write_csv

EVAL_CSV_FIELDS = [
    "pack", "top_n", "queries", "top1_accuracy", "topk_accuracy",
    "mrr", "avg_query_time", "total_query_time", "num_questions",
]


def evaluate_pack(pack_name: str, root: Path, vectorstore, embedder, top_n: int) -> dict[str, object]:
    pack_dir = root / "context_database" / pack_name
    questions = load_eval_questions(pack_dir)
    pack_chunk_ids = load_pack_chunk_ids(pack_dir)
    # over-fetch from the global collection, then filter down to this pack's
    # own chunk_ids so scoping matches test_retrieval.py exactly
    fetch_n = max(top_n * 2, 10)

    metrics = {"queries": 0, "top1_hits": 0, "topk_hits": 0, "mrr": 0.0, "total_query_time": 0.0, "details": []}

    for question in questions:
        query_text = question.get("question", "")
        expected_sources = set(question.get("expected_sources", []))

        start = time.perf_counter()
        query_vec = embedder.embed_query(QUERY_PREFIX + query_text)
        docs = vectorstore.similarity_search_by_vector(query_vec, k=fetch_n)
        # chunk_id is carried in metadata (set by embed_and_ingest.py) since
        # LangChain Document objects don't reliably expose the Chroma id itself.
        filtered_metas = [d.metadata for d in docs if d.metadata.get("chunk_id") in pack_chunk_ids][:top_n]
        elapsed = time.perf_counter() - start

        retrieved_source_ids = [m.get("source_id") for m in filtered_metas]

        metrics["queries"] += 1
        metrics["total_query_time"] += elapsed

        hit_rank = 0
        for rank, sid in enumerate(retrieved_source_ids, start=1):
            if sid in expected_sources:
                hit_rank = rank
                break

        if hit_rank:
            metrics["topk_hits"] += 1
            if hit_rank == 1:
                metrics["top1_hits"] += 1
            metrics["mrr"] += 1.0 / hit_rank

        metrics["details"].append({
            "question_id": question.get("question_id"),
            "query": query_text,
            "expected_sources": list(expected_sources),
            "top_hit_rank": hit_rank,
            "retrieved_source_ids": retrieved_source_ids,
            "elapsed_seconds": elapsed,
        })

    q = metrics["queries"]
    metrics["accuracy_topk"] = metrics["topk_hits"] / q if q else 0.0
    metrics["accuracy_top1"] = metrics["top1_hits"] / q if q else 0.0
    metrics["mrr"] = metrics["mrr"] / q if q else 0.0
    metrics["avg_query_time"] = metrics["total_query_time"] / q if q else 0.0
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate embedding-based retrieval against pack eval questions.")
    add_eval_cli_args(parser, "retrieval_results_embedding.csv")
    args = parser.parse_args()

    root = Path.cwd()
    vectorstore, embedder = open_vectorstore()

    if args.evaluate_all:
        rows = []
        for pack_name in PACKS:
            metrics = evaluate_pack(pack_name, root, vectorstore, embedder, args.top)
            rows.append({
                "pack": pack_name,
                "top_n": args.top,
                "queries": metrics["queries"],
                "top1_accuracy": metrics["accuracy_top1"],
                "topk_accuracy": metrics["accuracy_topk"],
                "mrr": metrics["mrr"],
                "avg_query_time": metrics["avg_query_time"],
                "total_query_time": metrics["total_query_time"],
                "num_questions": metrics["queries"],
            })
            print(f"{pack_name}: top1={metrics['accuracy_top1']:.3f} top{args.top}={metrics['accuracy_topk']:.3f} mrr={metrics['mrr']:.3f}")
        write_csv(rows, EVAL_CSV_FIELDS, Path(args.output_csv))
        print(f"Wrote {args.output_csv}")
        return 0

    if not args.pack:
        print("ERROR: pack is required unless --evaluate-all is used.")
        return 2

    metrics = evaluate_pack(args.pack, root, vectorstore, embedder, args.top)
    print(f"Evaluation results for top {args.top}")
    print(f"  queries: {metrics['queries']}")
    print(f"  top-1 accuracy: {metrics['accuracy_top1']:.3f}")
    print(f"  top-{args.top} accuracy: {metrics['accuracy_topk']:.3f}")
    print(f"  mean reciprocal rank: {metrics['mrr']:.3f}")
    if args.detail:
        print("-" * 80)
        for d in metrics["details"]:
            print(f"question_id: {d['question_id']}")
            print(f"  query: {d['query']}")
            print(f"  expected_sources: {d['expected_sources']}")
            print(f"  top_hit_rank: {d['top_hit_rank']}")
            print(f"  retrieved_source_ids: {d['retrieved_source_ids']}")
            print("-" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
