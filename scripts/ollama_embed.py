"""
Shared helper for embedding text via a local Ollama server, replacing the
sentence_transformers/PyTorch dependency previously used to run
nomic-ai/nomic-embed-text-v2-moe locally.

Ollama's nomic-embed-text follows the same Nomic Embed v1 instruction-prefix
convention ("search_document: " / "search_query: ") as the HF model, so
callers keep using those prefixes unchanged.
"""

import json
import urllib.error
import urllib.request

DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_BASE_URL = "http://localhost:11434"


def embed(texts: list[str], model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> list[list[float]]:
    """Embed a batch of texts via Ollama's /api/embed endpoint."""
    payload = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Cannot reach Ollama at {base_url}\n"
            f"Is it running? Try: ollama serve\n"
            f"Is the model pulled? Try: ollama pull {model}\n{exc}"
        )
    if "error" in body:
        raise SystemExit(
            f"Ollama embed request failed: {body['error']}\n"
            f"Is the model pulled? Try: ollama pull {model}"
        )
    return body["embeddings"]
