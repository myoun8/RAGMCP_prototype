"""Shared helpers for pack-scoped scripts: JSONL loading, eval CSV output,
Chroma bootstrap. Imported as a plain sibling module (relies on Python
adding the invoked script's own directory to sys.path), so it has no
heavy top-level imports -- chromadb/langchain are imported lazily inside
open_vectorstore() so test_retrieval.py's stdlib-only baseline stays that
way even though it imports this module for PACKS/write_csv.
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
import urllib.request
from pathlib import Path

PACKS = ["candor", "common", "nse", "vsans", "magik", "bt7"]

CHROMA_PATH = Path(__file__).parent.parent / "chroma_db"
COLLECTION = "ncnr_rag"
EMBED_MODEL = "nomic-embed-text"
EMBED_BASE_URL = "http://localhost:11434"
QUERY_PREFIX = "search_query: "


def _ollama_ready(timeout: float = 0.5) -> bool:
    try:
        urllib.request.urlopen(f"{EMBED_BASE_URL}/api/tags", timeout=timeout)
        return True
    except Exception:
        return False


def _model_loaded() -> bool:
    try:
        with urllib.request.urlopen(f"{EMBED_BASE_URL}/api/tags", timeout=2) as r:
            data = json.loads(r.read())
        return any(m.get("name", "").startswith(EMBED_MODEL) for m in data.get("models", []))
    except Exception:
        return False


def ensure_ollama() -> None:
    if not _ollama_ready():
        print("Ollama not running — starting 'ollama serve' ...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(20):
            time.sleep(0.5)
            if _ollama_ready():
                break
        else:
            raise SystemExit("Ollama did not start within 10 s. Is it installed?")

    if not _model_loaded():
        print(f"Pulling embedding model '{EMBED_MODEL}' ...")
        result = subprocess.run(["ollama", "pull", EMBED_MODEL])
        if result.returncode != 0:
            raise SystemExit(f"Failed to pull '{EMBED_MODEL}'.")


def load_jsonl_dir(dir_path: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(dir_path.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def load_eval_questions(pack_dir: Path) -> list[dict]:
    return load_jsonl_dir(pack_dir / "eval")


def load_pack_chunk_ids(pack_dir: Path) -> set[str]:
    """Chunk IDs belonging to this pack, per its own chunks/*.jsonl files
    (chunk file membership, not the chunk's own 'instrument' metadata field,
    which is sometimes mislabeled)."""
    return {row["chunk_id"] for row in load_jsonl_dir(pack_dir / "chunks")}


def write_csv(rows: list[dict], fieldnames: list[str], csv_path: Path) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def open_vectorstore(*, base_url: str | None = None, recreate: bool = False):
    """Connect to the shared Chroma collection populated by embed_and_ingest.py.
    `recreate=True` drops and recreates it (used only by embed_and_ingest.py's
    full re-ingest)."""
    import chromadb
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings

    embedder = OllamaEmbeddings(model=EMBED_MODEL, base_url=base_url) if base_url else OllamaEmbeddings(model=EMBED_MODEL)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    if recreate:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        vectorstore = Chroma(
            client=client, collection_name=COLLECTION, embedding_function=embedder,
            collection_metadata={"hnsw:space": "cosine"},  # match normalized Nomic Embed vectors
        )
    else:
        vectorstore = Chroma(client=client, collection_name=COLLECTION, embedding_function=embedder)
    return vectorstore, embedder


def add_eval_cli_args(parser, default_output_csv: str) -> None:
    parser.add_argument("pack", nargs="?", help="Pack folder name (candor, common, nse, vsans)")
    parser.add_argument("--top", type=int, default=5, help="Number of top chunks to retrieve")
    parser.add_argument("--evaluate-all", action="store_true", help="Run evaluation across all packs and save CSV")
    parser.add_argument("--output-csv", default=default_output_csv, help="CSV path for evaluation results")
    parser.add_argument("--detail", action="store_true", help="Print per-question evaluation details")
