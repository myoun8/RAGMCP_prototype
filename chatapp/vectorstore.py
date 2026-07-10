"""Vector storage for memory Layers 3 & 4 (ChromaDB, persistent client).

Two collections:

  compacted_history  — semantically searchable summaries of past conversation
                       segments. Record id: "summary::<conversation_id>::<seq_start>-<seq_end>"
  indexed_files      — chunks of user-uploaded files.
                       Record id: "file::<file_id>::<chunk_index>"

Deterministic ids make every write an idempotent upsert (re-summarizing a
segment or re-indexing a file overwrites in place instead of duplicating).

All records carry a ``user_id`` in metadata and every query filters on it —
vector search is always tenant-scoped.

The embedding function is injectable; by default Chroma's built-in
all-MiniLM-L6-v2 (ONNX, local) is used. Swap in an OpenAI/Ollama embedder by
passing any ``chromadb.EmbeddingFunction`` to ``VectorStore(...)``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import chromadb

from chatapp.config import (
    COMPACTED_HISTORY_COLLECTION,
    INDEXED_FILES_COLLECTION,
    VECTOR_DB_PATH,
)
from chatapp.schemas import FileChunkMetadata, SummaryMetadata


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VectorStore:
    def __init__(
        self,
        path: str = VECTOR_DB_PATH,
        embedding_function: Any | None = None,
    ) -> None:
        self._client = chromadb.PersistentClient(path=path)
        kwargs: dict[str, Any] = {"metadata": {"hnsw:space": "cosine"}}
        if embedding_function is not None:
            kwargs["embedding_function"] = embedding_function

        self.compacted_history = self._client.get_or_create_collection(
            name=COMPACTED_HISTORY_COLLECTION, **kwargs
        )
        self.indexed_files = self._client.get_or_create_collection(
            name=INDEXED_FILES_COLLECTION, **kwargs
        )

    # ------------------------------------------------------------------
    # Layer 3 — Compacted History
    # ------------------------------------------------------------------

    def upsert_summary(
        self,
        *,
        user_id: str,
        conversation_id: str,
        summary_text: str,
        seq_start: int,
        seq_end: int,
    ) -> str:
        """Store (or overwrite) the summary of messages [seq_start, seq_end]."""
        meta = SummaryMetadata(
            user_id=user_id,
            conversation_id=conversation_id,
            seq_start=seq_start,
            seq_end=seq_end,
            message_count=seq_end - seq_start + 1,
            created_at=_utcnow_iso(),
        )
        record_id = f"summary::{conversation_id}::{seq_start}-{seq_end}"
        self.compacted_history.upsert(
            ids=[record_id],
            documents=[summary_text],
            metadatas=[meta.model_dump()],
        )
        return record_id

    def search_history(
        self,
        *,
        user_id: str,
        query: str,
        top_k: int = 5,
        conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search over past-conversation summaries for one user."""
        where: dict[str, Any] = {"user_id": user_id}
        if conversation_id is not None:
            where = {"$and": [where, {"conversation_id": conversation_id}]}
        return self._query(self.compacted_history, query, top_k, where)

    # ------------------------------------------------------------------
    # Layer 4 — Indexed Files
    # ------------------------------------------------------------------

    def upsert_file_chunks(
        self,
        *,
        user_id: str,
        file_id: str,
        filename: str,
        chunks: list[str],
        description: str = "",
    ) -> list[str]:
        """Index all chunks of one uploaded file (idempotent per file_id)."""
        uploaded_at = _utcnow_iso()
        ids, metadatas = [], []
        for i in range(len(chunks)):
            ids.append(f"file::{file_id}::{i}")
            metadatas.append(
                FileChunkMetadata(
                    user_id=user_id,
                    file_id=file_id,
                    filename=filename,
                    chunk_index=i,
                    total_chunks=len(chunks),
                    description=description,
                    uploaded_at=uploaded_at,
                ).model_dump()
            )
        self.indexed_files.upsert(ids=ids, documents=chunks, metadatas=metadatas)
        return ids

    def delete_file(self, *, user_id: str, file_id: str) -> None:
        """Remove every chunk of a file (e.g. user deleted the upload)."""
        self.indexed_files.delete(
            where={"$and": [{"user_id": user_id}, {"file_id": file_id}]}
        )

    def search_files(
        self,
        *,
        user_id: str,
        query: str,
        top_k: int = 5,
        file_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search over a user's uploaded-file chunks."""
        where: dict[str, Any] = {"user_id": user_id}
        if file_id is not None:
            where = {"$and": [where, {"file_id": file_id}]}
        return self._query(self.indexed_files, query, top_k, where)

    # ------------------------------------------------------------------

    @staticmethod
    def _query(
        collection: chromadb.Collection,
        query: str,
        top_k: int,
        where: dict[str, Any],
    ) -> list[dict[str, Any]]:
        res = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        return [
            {
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],  # cosine distance, lower = closer
            }
            for i in range(len(res["ids"][0]))
        ]
