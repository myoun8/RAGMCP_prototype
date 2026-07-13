"""Central configuration for storage backends.

Environment variables (all optional — defaults give a working local setup):

  CHATAPP_DATABASE_URL    SQLAlchemy URL for the relational DB.
                          Production: postgresql+psycopg2://user:pass@host/chatapp
                          Default:    sqlite file next to this package.
  CHATAPP_VECTOR_DB_PATH  Directory for the ChromaDB persistent store.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL: str = os.getenv(
    "CHATAPP_DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'chatapp.db').as_posix()}",
)

VECTOR_DB_PATH: str = os.getenv(
    "CHATAPP_VECTOR_DB_PATH",
    str(BASE_DIR / "vector_db"),
)

# Collection names for the two vector-backed memory layers.
COMPACTED_HISTORY_COLLECTION = "compacted_history"
INDEXED_FILES_COLLECTION = "indexed_files"

# ---------------------------------------------------------------------------
# LLM (Part 2) — Llama 3.2 served locally by Ollama, spoken to through the
# official OpenAI SDK against Ollama's OpenAI-compatible endpoint.
# ---------------------------------------------------------------------------

LLM_BASE_URL: str = os.getenv("CHATAPP_LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY: str = os.getenv("CHATAPP_LLM_API_KEY", "ollama")  # Ollama ignores it
CHAT_MODEL: str = os.getenv("CHATAPP_CHAT_MODEL", "llama3.2")
# Cheap model for background workers (summaries, fact extraction). Same local
# model by default; point at a smaller/cheaper one in production if desired.
UTILITY_MODEL: str = os.getenv("CHATAPP_UTILITY_MODEL", "llama3.2")

# Orchestration knobs
WORKING_CONTEXT_MESSAGE_LIMIT = int(os.getenv("CHATAPP_LAST_N_MESSAGES", "20"))
RETRIEVAL_TOP_K = int(os.getenv("CHATAPP_RETRIEVAL_TOP_K", "3"))
# Vector hits with cosine distance beyond this are treated as irrelevant.
RETRIEVAL_MAX_DISTANCE = float(os.getenv("CHATAPP_RETRIEVAL_MAX_DISTANCE", "0.9"))

# Compaction worker
COMPACTION_TOKEN_LIMIT = int(os.getenv("CHATAPP_COMPACTION_TOKEN_LIMIT", "3000"))
# Never compact away the most recent K messages.
COMPACTION_KEEP_RECENT = int(os.getenv("CHATAPP_COMPACTION_KEEP_RECENT", "6"))
