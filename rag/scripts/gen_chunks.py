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
    from _common import (
        CHROMA_PATH, COLLECTION, EMBED_MODEL, EMBED_BASE_URL,
        QUERY_PREFIX, open_vectorstore, ensure_ollama,
    )
except ImportError as exc:
    raise SystemExit(
        f"Missing dependency: {exc}\n"
        "Run: pip install -r requirements.txt"
    )
DEFAULT_TOP    = 3

# Down-weighting of publication/citation material. These chunks (papers,
# bibliographies, "cite this instrument as ..." pages) are semantically close to
# many queries but rarely the answer the user wants, so we penalise them in the
# ranking rather than excluding them outright.
DEFAULT_PUBLICATION_PENALTY = 0.2   # added to a publication chunk's cosine distance
FETCH_MULTIPLIER            = 4      # over-fetch factor so the penalty has room to re-rank

PUBLICATION_STAGES       = {"citations_publications", "citation", "bibliography"}
PUBLICATION_SOURCE_TYPES = {"paper"}

ACCESS_LEVEL_MAP = {
    "public":     ["public"],
    "internal":   ["public", "internal"],
    "restricted": ["public", "internal", "restricted"],
}


def is_publication(meta: dict) -> bool:
    """True if a chunk is publication/citation material (a paper, bibliography,
    or 'how to cite this instrument' page) that should be down-weighted."""
    stage = str(meta.get("workflow_stage", "")).lower()
    stype = str(meta.get("source_type", "")).lower()
    return stage in PUBLICATION_STAGES or stype in PUBLICATION_SOURCE_TYPES


def build_chroma_filter(access_level: str, pack: str | None) -> dict:
    conditions = [
        {"status": {"$eq": "current"}},
        {"access_level": {"$in": ACCESS_LEVEL_MAP[access_level]}},
    ]
    if pack:
        conditions.append({"instrument": {"$eq": pack.upper()}})
    return {"$and": conditions}


class RetrievalError(Exception):
    """Retrieval produced no usable chunks: no DB/collection, no vector match,
    or every match beyond the distance cutoff. Carries a human-readable message
    callers can surface directly (the MCP tool returns it as tool output; the
    CLI turns it into a SystemExit)."""


def retrieve(query, *, pack=None, top=DEFAULT_TOP, max_distance=0.5,
             access_level="public", vectorstore=None,
             publication_penalty=DEFAULT_PUBLICATION_PENALTY):
    """Return the kept (doc, score) pairs for `query`, nearest first.

    Pass an already-open Chroma handle as `vectorstore` to reuse it across calls
    (long-lived callers like mcpServer do this to avoid reconnecting every time);
    when None, a fresh one is opened -- the convenient path for the CLI and
    one-off use. Raises RetrievalError when nothing usable comes back.

    Publication/citation chunks (see `is_publication`) are down-weighted by adding
    `publication_penalty` to their cosine distance for the purpose of ranking and
    the `max_distance` cutoff, so they surface only when clearly the best match.
    The returned score is always the true (unpenalised) cosine distance. Pass
    `publication_penalty=0` to disable the down-weighting."""
    if vectorstore is None:
        ensure_ollama()
        if not CHROMA_PATH.exists():
            raise RetrievalError(
                f"Chroma DB not found at {CHROMA_PATH}. "
                "Run: python scripts/embed_and_ingest.py"
            )
        vectorstore, _ = open_vectorstore(base_url=EMBED_BASE_URL)

    where_filter = build_chroma_filter(access_level, pack)
    # Over-fetch so a strong non-publication chunk that Chroma ranked just outside
    # the top-k can overtake a penalised publication chunk after re-ranking.
    fetch_k = max(top * FETCH_MULTIPLIER, top)
    docs_with_scores = vectorstore.similarity_search_with_score(
        QUERY_PREFIX + query, k=fetch_k, filter=where_filter,
    )
    if not docs_with_scores:
        raise RetrievalError(
            "No chunks matched the query and filters. "
            "Try relaxing the access level or pack filter."
        )

    # Penalise publications, then re-rank by the adjusted distance. Keep the true
    # cosine distance as the reported score; use the adjusted value only to rank
    # and to apply the max_distance cutoff.
    ranked = sorted(
        (
            (doc, score, score + (publication_penalty if is_publication(doc.metadata) else 0.0))
            for doc, score in docs_with_scores
        ),
        key=lambda t: t[2],
    )

    kept = [(doc, score) for doc, score, adj in ranked if adj <= max_distance][:top]
    if not kept:
        best_doc, best_score, best_adj = ranked[0]
        raise RetrievalError(
            f"No chunks within max distance {max_distance} "
            f"(closest was [{best_doc.metadata.get('source_id', 'unknown')}] "
            f"at {best_score:.3f}"
            + (f", {best_adj:.3f} after publication penalty" if best_adj != best_score else "")
            + "). Try a larger max distance."
        )
    return kept


def format_chunks(kept):
    """Render kept (doc, score) pairs into a plain-text block -- one numbered,
    source-attributed section per chunk, nearest first."""
    blocks = []
    for i, (doc, score) in enumerate(kept, 1):
        source_id = doc.metadata.get("source_id", "unknown")
        section   = doc.metadata.get("section", "")
        url       = doc.metadata.get("source_url_or_path", "")
        header    = f"[{i}] [{source_id}]"
        if section:
            header += f" {section}"
        if url:
            header += f" — {url}"
        blocks.append(f"{header}  (distance: {score:.3f})\n" + "-" * 60 + f"\n{doc.page_content}")
    return "\n\n".join(blocks)


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
    parser.add_argument(
        "--publication-penalty",
        type=float,
        default=DEFAULT_PUBLICATION_PENALTY,
        metavar="P",
        dest="publication_penalty",
        help="Cosine-distance penalty added to publication/citation chunks so "
             "they rank lower than instrument docs of equal similarity. "
             f"Default {DEFAULT_PUBLICATION_PENALTY}. Pass 0 to disable.",
    )
    args = parser.parse_args()

    try:
        ensure_ollama()
        if not CHROMA_PATH.exists():
            raise RetrievalError(
                f"Chroma DB not found at {CHROMA_PATH}\n"
                "Run: python scripts/embed_and_ingest.py"
            )
        print("Connecting to Chroma ...")
        vectorstore, _embedder = open_vectorstore(base_url=EMBED_BASE_URL)
        try:
            vectorstore._collection.count()
        except Exception:
            raise RetrievalError(
                f"Collection '{COLLECTION}' not found in {CHROMA_PATH}\n"
                "Run: python scripts/embed_and_ingest.py"
            )
        print(f"Embedding query via Ollama ({EMBED_MODEL}) ...")
        print(f"Retrieving top {args.top} chunks ...")
        kept = retrieve(
            args.query, pack=args.pack, top=args.top,
            max_distance=args.max_distance, access_level=args.access_level,
            vectorstore=vectorstore, publication_penalty=args.publication_penalty,
        )
    except RetrievalError as exc:
        raise SystemExit(str(exc))

    print(f"Returning {len(kept)} chunks (distance <= {args.max_distance}):\n")
    print(format_chunks(kept))


if __name__ == "__main__":
    main()