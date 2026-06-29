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
import csv
import json
from pathlib import Path

import chromadb
from ollama_embed import embed as ollama_embed

MODEL_NAME = "nomic-embed-text"
QUERY_PREFIX = "search_query: "
CHROMA_PATH = "./chroma_db"
COLLECTION = "ncnr_rag"
PACKS = ["candor", "common", "nse", "vsans"]


def load_eval_questions(pack_dir: Path) -> list[dict]:
    eval_dir = pack_dir / "eval"
    questions: list[dict] = []
    for path in sorted(eval_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    questions.append(json.loads(line))
    return questions


def load_pack_chunk_ids(pack_dir: Path) -> set[str]:
    """Chunk IDs that belong to this pack, per its own chunks/*.jsonl files.
    Mirrors test_retrieval_embedding.py's scoping (by chunk file membership,
    not the chunk's own 'instrument' metadata field, which is sometimes
    mislabeled)."""
    chunk_dir = pack_dir / "chunks"
    ids: set[str] = set()
    for path in sorted(chunk_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ids.add(json.loads(line)["chunk_id"])
    return ids


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


def evaluate_pack(pack_name: str, root: Path, coll, top_n: int) -> dict[str, object]:
    pack_dir = root / pack_name
    questions = load_eval_questions(pack_dir)
    pack_chunk_ids = load_pack_chunk_ids(pack_dir)
    # over-fetch from the global collection, then filter down to this pack's
    # own chunk_ids so scoping matches test_retrieval_embedding.py exactly
    fetch_n = max(top_n * 2, 10)

    metrics: dict[str, object] = {"queries": 0, "sum_precision": 0.0, "sum_recall": 0.0, "details": []}

    for question in questions:
        query_text = question.get("question", "")
        expected_sources = set(question.get("expected_sources", []))

        query_vec = ollama_embed([QUERY_PREFIX + query_text])
        result = coll.query(query_embeddings=query_vec, n_results=fetch_n, include=["documents", "metadatas"])

        ids = result["ids"][0]
        metas = result["metadatas"][0]
        filtered_metas = [meta for cid, meta in zip(ids, metas) if cid in pack_chunk_ids][:top_n]
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


def write_csv(rows: list[dict[str, object]], csv_path: Path) -> None:
    fieldnames = ["pack", "top_n", "queries", "mean_context_precision", "mean_context_recall"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval using RAGAS-standard Context Precision/Recall.")
    parser.add_argument("pack", nargs="?", help="Pack folder name (candor, vsans, nse, common)")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--evaluate-all", action="store_true")
    parser.add_argument("--output-csv", default="retrieval_results_ragas.csv")
    parser.add_argument("--detail", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    coll = client.get_collection(COLLECTION)

    if args.evaluate_all:
        rows = []
        for pack_name in PACKS:
            metrics = evaluate_pack(pack_name, root, coll, args.top)
            rows.append({
                "pack": pack_name,
                "top_n": args.top,
                "queries": metrics["queries"],
                "mean_context_precision": metrics["mean_context_precision"],
                "mean_context_recall": metrics["mean_context_recall"],
            })
            print(f"{pack_name}: context_precision@{args.top}={metrics['mean_context_precision']:.3f} context_recall={metrics['mean_context_recall']:.3f}")
        write_csv(rows, Path(args.output_csv))
        print(f"Wrote {args.output_csv}")
        return 0

    if not args.pack:
        print("ERROR: pack is required unless --evaluate-all is used.")
        return 2

    metrics = evaluate_pack(args.pack, root, coll, args.top)
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
