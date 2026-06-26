#!/usr/bin/env python3
"""Evaluate embedding-based retrieval (Chroma + nomic-embed-text-v2-moe) against the
same eval questions used by test_retrieval.py, for apples-to-apples comparison
with the TF-IDF baseline.

Requires scripts/embed_and_ingest.py to have been run first (populates ./chroma_db).

Usage:
  python scripts/test_retrieval_embedding.py --evaluate-all --output-csv retrieval_results_embedding.csv
  python scripts/test_retrieval_embedding.py candor --evaluate --detail
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder

MODEL_NAME = "nomic-ai/nomic-embed-text-v2-moe"
QUERY_PREFIX = "search_query: "
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CHROMA_PATH = "./chroma_db"
COLLECTION = "ncnr_rag"
PACK_INSTRUMENT = {
    "candor": "CANDOR",
    "vsans": "VSANS",
    "nse": "NSE",
    "common": "COMMON",
}


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
    Mirrors test_retrieval.py's scoping (by chunk file membership, not the
    chunk's own 'instrument' metadata field, which is sometimes mislabeled)."""
    chunk_dir = pack_dir / "chunks"
    ids: set[str] = set()
    for path in sorted(chunk_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ids.add(json.loads(line)["chunk_id"])
    return ids


def rerank(reranker: CrossEncoder, query: str, documents: list[str], metadatas: list[dict], top_n: int) -> list[dict]:
    """Cross-encoder rerank of the vector-search candidates down to top_n metadatas."""
    if not documents:
        return []
    scores = reranker.predict([(query, doc) for doc in documents])
    ranked = sorted(zip(scores, metadatas), key=lambda x: x[0], reverse=True)
    return [meta for _, meta in ranked[:top_n]]


def evaluate_pack(pack_name: str, root: Path, coll, model, reranker, top_n: int) -> dict[str, object]:
    pack_dir = root / pack_name
    questions = load_eval_questions(pack_dir)
    pack_chunk_ids = load_pack_chunk_ids(pack_dir)
    # over-fetch from the global collection, then filter down to this pack's
    # own chunk_ids so scoping matches test_retrieval.py exactly
    fetch_n = max(top_n * 4, 20)

    metrics = {"queries": 0, "top1_hits": 0, "topk_hits": 0, "mrr": 0.0, "total_query_time": 0.0, "details": []}

    for question in questions:
        query_text = question.get("question", "")
        expected_sources = set(question.get("expected_sources", []))

        start = time.perf_counter()
        query_vec = model.encode([QUERY_PREFIX + query_text], normalize_embeddings=True).tolist()
        result = coll.query(query_embeddings=query_vec, n_results=fetch_n, include=["documents", "metadatas"])
        ids = result["ids"][0]
        docs = result["documents"][0]
        metas = result["metadatas"][0]
        filtered_docs, filtered_metas = [], []
        for cid, doc, meta in zip(ids, docs, metas):
            if cid in pack_chunk_ids:
                filtered_docs.append(doc)
                filtered_metas.append(meta)
        filtered = rerank(reranker, query_text, filtered_docs, filtered_metas, top_n)
        elapsed = time.perf_counter() - start

        retrieved_source_ids = [m.get("source_id") for m in filtered]

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


def write_csv(rows: list[dict[str, object]], csv_path: Path) -> None:
    fieldnames = ["pack", "top_n", "queries", "top1_accuracy", "topk_accuracy", "mrr", "avg_query_time", "total_query_time", "num_questions"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate embedding-based retrieval against pack eval questions.")
    parser.add_argument("pack", nargs="?", help="Pack folder name (candor, vsans, nse, common)")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--evaluate-all", action="store_true")
    parser.add_argument("--output-csv", default="retrieval_results_embedding.csv")
    parser.add_argument("--detail", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    coll = client.get_collection(COLLECTION)
    print(f"Loading model {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME, device="cpu", trust_remote_code=True)
    print(f"Loading reranker {RERANK_MODEL} ...")
    reranker = CrossEncoder(RERANK_MODEL, device="cpu")

    if args.evaluate_all:
        rows = []
        for pack_name in ["candor", "common", "nse", "vsans"]:
            metrics = evaluate_pack(pack_name, root, coll, model, reranker, args.top)
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
        write_csv(rows, Path(args.output_csv))
        print(f"Wrote {args.output_csv}")
        return 0

    if not args.pack:
        print("ERROR: pack is required unless --evaluate-all is used.")
        return 2

    metrics = evaluate_pack(args.pack, root, coll, model, reranker, args.top)
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
