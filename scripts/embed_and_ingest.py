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
import chromadb
from ollama_embed import embed as ollama_embed

# ---- config ---------------------------------------------------------------
OLLAMA_MODEL    = "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11434"
CHUNK_GLOB   = "*/chunks/*_chunks.jsonl"   # adjust to where your JSONL live
CHROMA_PATH  = "./chroma_db"
COLLECTION   = "ncnr_rag"
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
        # carry doc_id / source_id into metadata so they're filterable too
        meta.setdefault("doc_id", r.get("doc_id", ""))
        meta.setdefault("source_id", r.get("source_id", ""))

        ids.append(cid)
        docs_store.append(r["text"])  # store the clean text for retrieval
        docs_for_embed.append(
            embed_text_for_doc(r["text"], meta.get("doc_id"), meta.get("section"))
        )
        metas.append(meta)

    # ---- embed (document side: search_document: prefix, normalized) ----
    print(f"Embedding via Ollama ({OLLAMA_MODEL}) ...")
    vectors = []
    for i in range(0, len(docs_for_embed), BATCH):
        batch = docs_for_embed[i:i + BATCH]
        vectors.extend(ollama_embed(batch, model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL))
        print(f"  embedded {min(i + BATCH, len(docs_for_embed))}/{len(docs_for_embed)}")

    # sanity: dimension must match what the collection will expect
    dim = len(vectors[0])
    print(f"Embedding dimension: {dim}")

    # ---- create collection (cosine) and add ----
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # delete-and-recreate so re-runs are clean (TEST index, safe to wipe)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    coll = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},   # match normalized Nomic Embed vectors
    )

    print("Adding to Chroma ...")
    for i in range(0, len(ids), BATCH):
        sl = slice(i, i + BATCH)
        coll.add(
            ids=ids[sl],
            embeddings=vectors[sl],
            documents=docs_store[sl],
            metadatas=metas[sl],
        )
    print(f"Done. Collection '{COLLECTION}' now holds {coll.count()} chunks.")


if __name__ == "__main__":
    main()