"""
Retrieve top-k chunks from the NCNR RAG Chroma vectorstore and print them.
No LLM call is made — use this to inspect raw retrieval results or pipe
chunk text into another tool.

Prerequisites:
  1. Ollama running locally with nomic-embed-text pulled (ollama pull nomic-embed-text)
  2. Chroma DB populated (python scripts/embed_and_ingest.py)
  3. pip install -r requirements.txt

Usage:
  python scripts/gen_chunks.py "<question>"
  python scripts/gen_chunks.py "<question>" --pack candor --top 6
  python scripts/gen_chunks.py "<question>" --max-distance 0.4 --access-level internal
"""

import argparse

try:
    from rag.scripts._common import (
        CHROMA_PATH, COLLECTION, EMBED_MODEL, EMBED_BASE_URL,
        QUERY_PREFIX, open_vectorstore, ensure_ollama,
    )
except ImportError as exc:
    raise SystemExit(
        f"Missing dependency: {exc}\n"
        "Run: pip install -r requirements.txt"
    )
DEFAULT_TOP    = 3

ACCESS_LEVEL_MAP = {
    "public":     ["public"],
    "internal":   ["public", "internal"],
    "restricted": ["public", "internal", "restricted"],
}


def build_chroma_filter(access_level: str, pack: str | None) -> dict:
    conditions = [
        {"status": {"$eq": "current"}},
        {"access_level": {"$in": ACCESS_LEVEL_MAP[access_level]}},
    ]
    if pack:
        conditions.append({"instrument": {"$eq": pack.upper()}})
    return {"$and": conditions}


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve top-k chunks from the NCNR RAG vectorstore."
    )
    parser.add_argument("query", help="Natural-language question")
    parser.add_argument(
        "--pack",
        metavar="PACK",
        default=None,
        help="Filter by instrument pack: candor, vsans, nse, common (default: all)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP,
        metavar="N",
        help=f"Number of chunks to retrieve (default: {DEFAULT_TOP})",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=0.5,
        metavar="D",
        dest="max_distance",
        help="Drop chunks whose cosine distance exceeds this value. "
             "Cosine distance ranges 0 (identical) to 2 (opposite). "
             "Default 0.5. Pass 2 to disable.",
    )
    parser.add_argument(
        "--access-level",
        choices=list(ACCESS_LEVEL_MAP),
        default="public",
        dest="access_level",
        help="Maximum access level to include (default: public)",
    )
    args = parser.parse_args()

    ensure_ollama()

    if not CHROMA_PATH.exists():
        raise SystemExit(
            f"Chroma DB not found at {CHROMA_PATH}\n"
            "Run: python scripts/embed_and_ingest.py"
        )

    print("Connecting to Chroma ...")
    vectorstore, _embedder = open_vectorstore(base_url=EMBED_BASE_URL)
    try:
        vectorstore._collection.count()
    except Exception:
        raise SystemExit(
            f"Collection '{COLLECTION}' not found in {CHROMA_PATH}\n"
            "Run: python scripts/embed_and_ingest.py"
        )

    where_filter = build_chroma_filter(args.access_level, args.pack)
    print(f"Embedding query via Ollama ({EMBED_MODEL}) ...")
    print(f"Retrieving top {args.top} chunks ...")
    docs_with_scores = vectorstore.similarity_search_with_score(
        QUERY_PREFIX + args.query, k=args.top, filter=where_filter,
    )

    if not docs_with_scores:
        raise SystemExit("No chunks matched the query and filters. Try relaxing --access-level or --pack.")

    best_doc, best_distance = docs_with_scores[0]
    print(f"Closest match distance: {best_distance:.3f} (--max-distance {args.max_distance})\n")

    kept = [(d, s) for d, s in docs_with_scores if s <= args.max_distance]
    if not kept:
        raise SystemExit(
            f"No chunks within --max-distance {args.max_distance} "
            f"(closest was [{best_doc.metadata.get('source_id', 'unknown')}] "
            f"at {best_distance:.3f}). Try relaxing --max-distance."
        )

    print(f"Returning {len(kept)} of {len(docs_with_scores)} chunks (distance <= {args.max_distance}):\n")
    chunks: list[str] = []
    for i, (doc, score) in enumerate(kept, 1):
        source_id = doc.metadata.get("source_id", "unknown")
        section   = doc.metadata.get("section", "")
        url       = doc.metadata.get("source_url_or_path", "")
        header    = f"[{i}] [{source_id}]"
        if section:
            header += f" {section}"
        if url:
            header += f" — {url}"
        print(f"{header}  (distance: {score:.3f})")
        print("-" * 60)
        print(doc.page_content)
        print()
        chunks.append(doc.page_content)

    return chunks


if __name__ == "__main__":
    main()