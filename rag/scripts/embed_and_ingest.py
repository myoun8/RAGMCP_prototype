"""
Embed normalized RAG chunks with Ollama's nomic-embed-text model and load into Chroma.

Assumptions (change at top if different):
  - Model:   nomic-embed-text via Ollama (768-dim, cosine)
  - Ollama:  running locally, model pulled (`ollama pull nomic-embed-text`)
  - Chroma:  PersistentClient -> ./chroma_db
  - Input:   per-pack *_chunks.jsonl files, one JSON object per line
  - Output:  ONE collection "ncnr_rag", filter by metadata

Each input chunk line is expected to look roughly like:
  {
    "chunk_id": "candor_overview__0003",
    "doc_id":   "candor_overview",
    "source_id":"CANDOR-001",
    "text":     "....",
    "metadata": {
        "instrument": "CANDOR",
        "workflow_stage": "overview",
        "source_type": "web_page",
        "access_level": "public",
        "status": "current",
        "title": "CHRNS CANDOR - White-Beam Reflectometer",
        "section": "Specifications / Capabilities",
        "deprecation_notice": false,
        "external_source": false,
        "source_url_or_path": "https://www.nist.gov/ncnr/chrns-candor-white-beam-reflectometer"
        # may also contain list-valued fields like "related_source_ids"
    }
  }
Adjust the field access in load_chunks() to match your actual schema.
"""

import json
import glob

from rag.scripts._common import COLLECTION, open_vectorstore

# ---- config ---------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
CHUNK_GLOB   = "context_database/*/chunks/*_chunks.jsonl"   # adjust to where your JSONL live
BATCH        = 64
# ---------------------------------------------------------------------------


def load_chunks(glob_pattern):
    """Read all *_chunks.jsonl into a flat list of dicts."""
    rows = []
    for path in glob.glob(glob_pattern):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
    if not rows:
        raise SystemExit(f"No chunks found under {glob_pattern!r} -- check the path.")
    print(f"Loaded {len(rows)} chunks from {glob_pattern}")
    return rows


def sanitize_metadata(meta):
    """
    Chroma metadata values must be str | int | float | bool (no None, no lists).
    - lists  -> semicolon-joined strings
    - None   -> dropped
    - other  -> str()
    """
    clean = {}
    for k, v in (meta or {}).items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, (list, tuple)):
            clean[k] = ";".join(str(x) for x in v)
        else:
            clean[k] = str(v)
    return clean


DOC_PREFIX = "search_document: "


def embed_text_for_doc(text, doc_id=None, section=None):
    """
    Prepend lightweight context (doc_id / section) so terse technical chunks
    embed with semantic anchors, plus the search_document: instruction prefix
    nomic-embed-text-v2-moe requires on the document side.

    Uses doc_id rather than a "title" field -- no chunk metadata actually
    carries a title, and section names alone (e.g. "Overview", "Contacts")
    repeat verbatim across unrelated documents, which pulled unrelated docs'
    same-named sections closer together in embedding space instead of
    disambiguating them.
    """
    prefix_bits = [b for b in (doc_id, section) if b]
    if prefix_bits:
        body = " | ".join(prefix_bits) + "\n\n" + text
    else:
        body = text
    return DOC_PREFIX + body


def main():
    rows = load_chunks(CHUNK_GLOB)

    # Build parallel lists, keeping chunk_id aligned to everything else.
    ids, docs_for_embed, docs_store, metas = [], [], [], []
    seen = set()
    for r in rows:
        cid = r["chunk_id"]
        if cid in seen:
            raise SystemExit(f"Duplicate chunk_id {cid!r} -- ids must be unique.")
        seen.add(cid)

        meta = sanitize_metadata(r.get("metadata", {}))
        # carry doc_id / source_id / chunk_id into metadata so they're filterable too.
        # chunk_id in particular: LangChain's Document objects returned from Chroma
        # similarity search don't reliably expose the Chroma-assigned id, so callers
        # that need to scope results back to a pack's own chunk_ids (the eval scripts)
        # have to read it from metadata instead.
        meta.setdefault("doc_id", r.get("doc_id", ""))
        meta.setdefault("source_id", r.get("source_id", ""))
        meta.setdefault("chunk_id", cid)

        ids.append(cid)
        docs_store.append(r["text"])  # store the clean text for retrieval
        docs_for_embed.append(
            embed_text_for_doc(r["text"], meta.get("doc_id"), meta.get("section"))
        )
        metas.append(meta)

    # ---- embed (document side: search_document: prefix, normalized) ----
    # delete-and-recreate the collection so re-runs are clean (TEST index, safe to wipe).
    # Wrapped in langchain_chroma.Chroma so the collection this script produces is the
    # same vectorstore object query_rag.py / the eval scripts consume as a retriever.
    vectorstore, embedder = open_vectorstore(base_url=OLLAMA_BASE_URL, recreate=True)
    print(f"Embedding via Ollama ({embedder.model}) ...")
    vectors = []
    for i in range(0, len(docs_for_embed), BATCH):
        batch = docs_for_embed[i:i + BATCH]
        vectors.extend(embedder.embed_documents(batch))
        print(f"  embedded {min(i + BATCH, len(docs_for_embed))}/{len(docs_for_embed)}")

    # sanity: dimension must match what the collection will expect
    dim = len(vectors[0])
    print(f"Embedding dimension: {dim}")

    print("Adding to Chroma ...")
    # Chroma.add_texts()/from_documents() always re-embeds page_content themselves
    # (no precomputed-embeddings parameter), which would discard the search_document:
    # prefix + doc_id/section enrichment baked into docs_for_embed above and embed the
    # stored (unenriched) text instead. Reaching into the wrapped raw chromadb
    # collection preserves "embed enriched text, store/display original text",
    # identical to the add() call this replaces.
    for i in range(0, len(ids), BATCH):
        sl = slice(i, i + BATCH)
        vectorstore._collection.add(
            ids=ids[sl],
            embeddings=vectors[sl],
            documents=docs_store[sl],
            metadatas=metas[sl],
        )
    print(f"Done. Collection '{COLLECTION}' now holds {vectorstore._collection.count()} chunks.")


if __name__ == "__main__":
    main()