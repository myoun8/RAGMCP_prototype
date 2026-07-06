#!/usr/bin/env python3
"""Evaluate embedding-based retrieval (Chroma + Ollama nomic-embed-text) using the
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

Requires scripts/embed_and_ingest.py to have been run first (populates ./chroma_db).

Usage:
  python scripts/evaluate_retrieval_ragas.py --evaluate-all --output-csv retrieval_results_ragas.csv
  python scripts/evaluate_retrieval_ragas.py candor --top 5 --detail
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rag.scripts._common import PACKS, QUERY_PREFIX, add_eval_cli_args, load_eval_questions, load_pack_chunk_ids, open_vectorstore, write_csv

EVAL_CSV_FIELDS = ["pack", "top_n", "queries", "mean_context_precision", "mean_context_recall"]


def context_precision_at_k(relevance: list[int]) -> float:
    num_relevant = sum(relevance)
    if num_relevant == 0:
        return 0.0
    total = 0.0
    hits = 0
    for k, rel in enumerate(relevance, start=1):
        hits += rel
        precision_at_k = hits / k
        total += precision_at_k * rel
    return total / num_relevant


def context_recall(retrieved_source_ids: list[str], expected_sources: set[str]) -> float:
    if not expected_sources:
        return 0.0
    found = {sid for sid in retrieved_source_ids if sid in expected_sources}
    return len(found) / len(expected_sources)


def evaluate_pack(pack_name: str, root: Path, vectorstore, embedder, top_n: int) -> dict[str, object]:
    pack_dir = root / "context_database" / pack_name
    questions = load_eval_questions(pack_dir)
    pack_chunk_ids = load_pack_chunk_ids(pack_dir)
    # over-fetch from the global collection, then filter down to this pack's
    # own chunk_ids so scoping matches test_retrieval_embedding.py exactly
    fetch_n = max(top_n * 2, 10)

    metrics: dict[str, object] = {"queries": 0, "sum_precision": 0.0, "sum_recall": 0.0, "details": []}

    for question in questions:
        query_text = question.get("question", "")
        expected_sources = set(question.get("expected_sources", []))

        query_vec = embedder.embed_query(QUERY_PREFIX + query_text)
        docs = vectorstore.similarity_search_by_vector(query_vec, k=fetch_n)
        # chunk_id is carried in metadata (set by embed_and_ingest.py) since
        # LangChain Document objects don't reliably expose the Chroma id itself.
        filtered_metas = [d.metadata for d in docs if d.metadata.get("chunk_id") in pack_chunk_ids][:top_n]
        retrieved_source_ids = [m.get("source_id") for m in filtered_metas]

        relevance = [1 if sid in expected_sources else 0 for sid in retrieved_source_ids]
        precision = context_precision_at_k(relevance)
        recall = context_recall(retrieved_source_ids, expected_sources)

        metrics["queries"] += 1
        metrics["sum_precision"] += precision
        metrics["sum_recall"] += recall

        matched = sorted(expected_sources & set(retrieved_source_ids))
        missed = sorted(expected_sources - set(retrieved_source_ids))
        metrics["details"].append({
            "question_id": question.get("question_id"),
            "query": query_text,
            "expected_sources": sorted(expected_sources),
            "retrieved_source_ids": retrieved_source_ids,
            "matched_sources": matched,
            "missed_sources": missed,
            "context_precision": precision,
            "context_recall": recall,
        })

    q = metrics["queries"]
    metrics["mean_context_precision"] = metrics["sum_precision"] / q if q else 0.0
    metrics["mean_context_recall"] = metrics["sum_recall"] / q if q else 0.0
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval using RAGAS-standard Context Precision/Recall.")
    add_eval_cli_args(parser, "retrieval_results_ragas.csv")
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
                "mean_context_precision": metrics["mean_context_precision"],
                "mean_context_recall": metrics["mean_context_recall"],
            })
            print(f"{pack_name}: context_precision@{args.top}={metrics['mean_context_precision']:.3f} context_recall={metrics['mean_context_recall']:.3f}")
        write_csv(rows, EVAL_CSV_FIELDS, Path(args.output_csv))
        print(f"Wrote {args.output_csv}")
        return 0

    if not args.pack:
        print("ERROR: pack is required unless --evaluate-all is used.")
        return 2

    metrics = evaluate_pack(args.pack, root, vectorstore, embedder, args.top)
    print(f"RAGAS-standard retrieval evaluation for top {args.top}")
    print(f"  queries: {metrics['queries']}")
    print(f"  mean Context Precision@{args.top}: {metrics['mean_context_precision']:.3f}")
    print(f"  mean Context Recall: {metrics['mean_context_recall']:.3f}")
    if args.detail:
        print("-" * 80)
        for d in metrics["details"]:
            print(f"question_id: {d['question_id']}")
            print(f"  query: {d['query']}")
            print(f"  expected_sources: {d['expected_sources']}")
            print(f"  retrieved_source_ids: {d['retrieved_source_ids']}")
            print(f"  matched: {d['matched_sources']}  missed: {d['missed_sources']}")
            print(f"  context_precision: {d['context_precision']:.3f}  context_recall: {d['context_recall']:.3f}")
            print("-" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
