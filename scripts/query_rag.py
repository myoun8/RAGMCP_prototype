"""
Query the NCNR RAG knowledge pack with an LLM — local Ollama (default) or
any OpenAI-compatible chat-completions endpoint (e.g. an NVIDIA NIM
container) reached over a manually-established SSH tunnel.

Prerequisites (Ollama backend, default):
  1. Ollama installed and running  (ollama serve)
  2. A model pulled               (ollama pull llama3.2)
  3. Chroma DB populated          (python scripts/embed_and_ingest.py)
  4. pip install sentence-transformers chromadb

Prerequisites (OpenAI-compatible backend, e.g. NIM on a remote GB10 box):
  1. Chroma DB populated          (python scripts/embed_and_ingest.py)
  2. pip install sentence-transformers chromadb
  3. SSH tunnel opened manually in another terminal, e.g.:
       ssh -L 8001:localhost:8001 user@gb10-host
     (the NIM container must already be serving on that remote port)

Prerequisites (SSH remote-exec backend, e.g. NIM on a remote GB10 box,
no local port-forward needed):
  1. Chroma DB populated          (python scripts/embed_and_ingest.py)
  2. pip install sentence-transformers chromadb paramiko
  3. NIM container already serving on the remote host's own loopback
     (this runs the same curl pattern as test.py, but over SSH exec
     instead of from a local tunnel, and with credentials read from
     env vars instead of hardcoded)

Usage (Ollama, default):
  python scripts/query_rag.py "<question>"
  python scripts/query_rag.py "<question>" --pack candor --top 6 --model llama3.2
  python scripts/query_rag.py "<question>" --access-level internal

Usage (OpenAI-compatible, e.g. NVIDIA NIM via local tunnel):
  python scripts/query_rag.py "<question>" --backend openai \\
      --base-url http://localhost:8001/v1 \\
      --model nvidia/llama-3.3-nemotron-super-49b-v1.5
  # optional auth, if the NIM container requires it:
  python scripts/query_rag.py "<question>" --backend openai \\
      --base-url http://localhost:8001/v1 \\
      --model nvidia/llama-3.3-nemotron-super-49b-v1.5 \\
      --api-key sk-...           # or: export NIM_API_KEY=sk-...

Usage (SSH remote-exec, e.g. NVIDIA NIM on GB10, no tunnel):
  export GB10_SSH_HOST=nmatgb10-1.campus.nist.gov
  export GB10_SSH_USER=myuser
  export GB10_SSH_PASSWORD=...      # or: export GB10_SSH_KEY_FILE=~/.ssh/id_ed25519
  python scripts/query_rag.py "<question>" --backend ssh \\
      --model nvidia/llama-3.3-nemotron-super-49b-v1.5
  # --ssh-host/--ssh-user/--ssh-password/--ssh-key-file flags override the
  # env vars above if passed, but avoid --ssh-password on the command line
  # where it would land in shell history.
"""

import argparse
import json
import os
import re
import shlex
import urllib.request
import urllib.error
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
except ImportError as exc:
    raise SystemExit(
        f"Missing dependency: {exc}\n"
        "Run: pip install sentence-transformers chromadb"
    )

# ── Config ───────────────────────────────────────────────────────────────────
EMBED_MODEL         = "BAAI/bge-large-en-v1.5"
DEVICE              = "cpu"
CHROMA_PATH         = Path(__file__).parent.parent / "chroma_db"
COLLECTION          = "ncnr_rag"
DEFAULT_BACKEND     = "ollama"
OLLAMA_BASE_URL     = "http://localhost:11434"
DEFAULT_MODEL       = "llama3.2"          # default for --backend ollama only
NIM_API_KEY_ENV_VAR = "NIM_API_KEY"
DEFAULT_TOP         = 5

# --backend ssh: remote-exec curl against the NIM container's own loopback,
# mirroring test.py's pattern instead of a local SSH port-forward.
GB10_SSH_HOST_ENV_VAR     = "GB10_SSH_HOST"
GB10_SSH_USER_ENV_VAR     = "GB10_SSH_USER"
GB10_SSH_PASSWORD_ENV_VAR = "GB10_SSH_PASSWORD"
GB10_SSH_KEY_FILE_ENV_VAR = "GB10_SSH_KEY_FILE"
DEFAULT_SSH_PORT          = 22
DEFAULT_REMOTE_NIM_PORT   = 8001

# BGE-large-en-v1.5: documents use no prefix; queries use this instruction prefix
# to align asymmetric retrieval (see BAAI/bge-large-en-v1.5 model card).
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# access_level cascade: each level includes all levels below it
ACCESS_LEVEL_MAP = {
    "public":     ["public"],
    "internal":   ["public", "internal"],
    "restricted": ["public", "internal", "restricted"],
}

SYSTEM_PROMPT = (
    "You are an expert assistant for NIST NCNR neutron-scattering instruments. "
    "Answer questions using ONLY the facts in the context provided below — do not invent "
    "facts that aren't there. The context may describe the relevant information using "
    "different terminology than the question (e.g. a question about \"beamline parameters\" "
    "may be answered by a \"Specifications / Capabilities\" section) — use your judgment to "
    "connect the question to relevant context even when exact wording differs. "
    "Only say the information isn't available if no context chunk is actually relevant. "
    "Cite your sources inline using [source_id] notation after relevant statements."
)
# ─────────────────────────────────────────────────────────────────────────────


def embed_query(model, query: str) -> list:
    return model.encode(
        BGE_QUERY_PREFIX + query,
        normalize_embeddings=True,
    ).tolist()


def build_chroma_filter(access_level: str, pack: str | None) -> dict:
    conditions = [
        {"status": {"$eq": "current"}},
        {"access_level": {"$in": ACCESS_LEVEL_MAP[access_level]}},
    ]
    if pack:
        conditions.append({"instrument": {"$eq": pack.upper()}})
    return {"$and": conditions}


def build_context(results: dict) -> tuple[str, list[dict]]:
    chunks = []
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({
            "source_id": meta.get("source_id", "unknown"),
            "section":   meta.get("section", ""),
            "url":       meta.get("source_url_or_path", ""),
            "text":      text,
        })
    context_str = "\n\n---\n\n".join(
        f"[{c['source_id']}] {c['section']}\n{c['text']}" for c in chunks
    )
    return context_str, chunks


def strip_thinking(answer: str) -> str:
    """Drop a leading <think>...</think> reasoning block (Nemotron/R1-style models)."""
    return re.sub(r"^\s*<think>.*?</think>\s*", "", answer, count=1, flags=re.DOTALL)


def call_llm(
    backend: str,
    base_url: str,
    model_name: str,
    user_message: str,
    api_key: str | None = None,
) -> str:
    headers = {"Content-Type": "application/json"}
    payload = json.dumps({
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
    }).encode()

    if backend == "ollama":
        url = f"{base_url.rstrip('/')}/api/chat"
    else:  # openai
        url = f"{base_url.rstrip('/')}/chat/completions"
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as exc:
        if backend == "ollama":
            raise SystemExit(
                f"Cannot reach Ollama at {url}\n"
                f"Is it running? Try: ollama serve\n{exc}"
            )
        raise SystemExit(
            f"Cannot reach OpenAI-compatible endpoint at {url}\n"
            "Is the SSH tunnel to the GB10 box open? Try something like:\n"
            "  ssh -L 8001:localhost:8001 user@gb10-host\n"
            f"{exc}"
        )

    if backend == "ollama":
        return body["message"]["content"]
    return body["choices"][0]["message"]["content"]


def call_llm_via_ssh(
    ssh_host: str,
    ssh_port: int,
    ssh_user: str,
    ssh_password: str | None,
    ssh_key_file: str | None,
    remote_port: int,
    model_name: str,
    user_message: str,
) -> str:
    try:
        import paramiko
    except ImportError as exc:
        raise SystemExit(
            f"Missing dependency: {exc}\n"
            "Run: pip install paramiko"
        )

    payload = json.dumps({
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
    })

    # Same curl-against-loopback pattern as test.py, but shlex-quoted: the
    # payload embeds the user's question and retrieved context verbatim, so
    # naive string interpolation into a shell command would be a command
    # injection risk.
    curl_cmd = " ".join([
        "curl", "-sS", "-X", "POST",
        shlex.quote(f"http://0.0.0.0:{remote_port}/v1/chat/completions"),
        "-H", shlex.quote("accept: application/json"),
        "-H", shlex.quote("Content-Type: application/json"),
        "-d", shlex.quote(payload),
    ])

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            ssh_host,
            port=ssh_port,
            username=ssh_user,
            password=ssh_password,
            key_filename=ssh_key_file,
            timeout=30,
        )
    except Exception as exc:
        raise SystemExit(f"Cannot SSH to {ssh_user}@{ssh_host}:{ssh_port}\n{exc}")

    try:
        _stdin, stdout, stderr = client.exec_command(curl_cmd, timeout=180)
        out = stdout.read().decode()
        err = stderr.read().decode()
        exit_status = stdout.channel.recv_exit_status()
    finally:
        client.close()

    if exit_status != 0 or not out.strip():
        raise SystemExit(
            f"Remote curl against http://0.0.0.0:{remote_port} on {ssh_host} "
            f"failed (exit {exit_status}). Is the NIM container running there?\n"
            f"stderr:\n{err}"
        )

    try:
        body = json.loads(out)
    except json.JSONDecodeError:
        raise SystemExit(
            f"Could not parse remote curl output as JSON:\n{out}\nstderr:\n{err}"
        )

    return body["choices"][0]["message"]["content"]


def main():
    parser = argparse.ArgumentParser(
        description="Query the NCNR RAG knowledge pack via a local Ollama LLM."
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
        "--backend",
        choices=["ollama", "openai", "ssh"],
        default=DEFAULT_BACKEND,
        help="LLM backend: 'ollama' for a local Ollama server (default), "
             "'openai' for an OpenAI-compatible API (e.g. NVIDIA NIM) reached "
             "via a manually-established SSH tunnel, 'ssh' to instead SSH "
             "into the remote host and curl the NIM container's own loopback "
             "directly (no tunnel needed).",
    )
    parser.add_argument(
        "--base-url",
        metavar="URL",
        default=None,
        help="Backend base URL. Default for --backend ollama: "
             f"{OLLAMA_BASE_URL}. Required for --backend openai "
             "(e.g. http://localhost:8001/v1 after "
             "`ssh -L 8001:localhost:8001 user@gb10-host`).",
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="NAME",
        help=f"Model name. Default for --backend ollama: {DEFAULT_MODEL}. "
             "Required for --backend openai "
             "(e.g. nvidia/llama-3.3-nemotron-super-49b-v1.5 for NVIDIA NIM).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="API key for --backend openai (optional; self-hosted NIM over an "
             f"SSH tunnel typically needs none). Falls back to the {NIM_API_KEY_ENV_VAR} "
             "env var if set. Ignored for --backend ollama.",
    )
    parser.add_argument(
        "--ssh-host",
        default=None,
        metavar="HOST",
        help="Remote host for --backend ssh (e.g. nmatgb10-1.campus.nist.gov). "
             f"Falls back to the {GB10_SSH_HOST_ENV_VAR} env var.",
    )
    parser.add_argument(
        "--ssh-port",
        type=int,
        default=DEFAULT_SSH_PORT,
        metavar="PORT",
        help=f"SSH port for --backend ssh (default: {DEFAULT_SSH_PORT}).",
    )
    parser.add_argument(
        "--ssh-user",
        default=None,
        metavar="USER",
        help=f"SSH username for --backend ssh. Falls back to the {GB10_SSH_USER_ENV_VAR} env var.",
    )
    parser.add_argument(
        "--ssh-password",
        default=None,
        metavar="PASSWORD",
        help="SSH password for --backend ssh (alternative to --ssh-key-file). "
             f"Falls back to the {GB10_SSH_PASSWORD_ENV_VAR} env var — prefer the env var "
             "over this flag to avoid leaving the password in shell history.",
    )
    parser.add_argument(
        "--ssh-key-file",
        default=None,
        metavar="PATH",
        help="SSH private key path for --backend ssh (alternative to --ssh-password). "
             f"Falls back to the {GB10_SSH_KEY_FILE_ENV_VAR} env var.",
    )
    parser.add_argument(
        "--remote-port",
        type=int,
        default=DEFAULT_REMOTE_NIM_PORT,
        metavar="PORT",
        help="Port the NIM container listens on, on the remote host's own "
             f"loopback (default: {DEFAULT_REMOTE_NIM_PORT}). Only used by --backend ssh.",
    )
    parser.add_argument(
        "--access-level",
        choices=list(ACCESS_LEVEL_MAP),
        default="public",
        dest="access_level",
        help="Maximum access level to include (default: public)",
    )
    args = parser.parse_args()

    ssh_host = ssh_user = ssh_password = ssh_key_file = None
    ssh_port = remote_port = None

    if args.backend == "ollama":
        base_url = args.base_url or OLLAMA_BASE_URL
        model_name = args.model or DEFAULT_MODEL
        api_key = None
    elif args.backend == "openai":
        if not args.base_url:
            raise SystemExit(
                "--base-url is required when --backend openai is used.\n"
                "Example: --base-url http://localhost:8001/v1\n"
                "(after manually opening a tunnel, e.g. "
                "ssh -L 8001:localhost:8001 user@gb10-host)"
            )
        if not args.model:
            raise SystemExit(
                "--model is required when --backend openai is used.\n"
                "Example: --model nvidia/llama-3.3-nemotron-super-49b-v1.5"
            )
        base_url = args.base_url
        model_name = args.model
        api_key = args.api_key or os.environ.get(NIM_API_KEY_ENV_VAR)
    else:  # ssh
        base_url = None
        api_key = None
        ssh_host = args.ssh_host or os.environ.get(GB10_SSH_HOST_ENV_VAR)
        ssh_user = args.ssh_user or os.environ.get(GB10_SSH_USER_ENV_VAR)
        ssh_password = args.ssh_password or os.environ.get(GB10_SSH_PASSWORD_ENV_VAR)
        ssh_key_file = args.ssh_key_file or os.environ.get(GB10_SSH_KEY_FILE_ENV_VAR)
        ssh_port = args.ssh_port
        remote_port = args.remote_port
        if not ssh_host:
            raise SystemExit(
                f"--ssh-host is required for --backend ssh (or set {GB10_SSH_HOST_ENV_VAR})."
            )
        if not ssh_user:
            raise SystemExit(
                f"--ssh-user is required for --backend ssh (or set {GB10_SSH_USER_ENV_VAR})."
            )
        if not ssh_password and not ssh_key_file:
            raise SystemExit(
                "--ssh-password or --ssh-key-file is required for --backend ssh "
                f"(or set {GB10_SSH_PASSWORD_ENV_VAR} / {GB10_SSH_KEY_FILE_ENV_VAR})."
            )
        if not args.model:
            raise SystemExit(
                "--model is required when --backend ssh is used.\n"
                "Example: --model nvidia/llama-3.3-nemotron-super-49b-v1.5"
            )
        model_name = args.model

    if not CHROMA_PATH.exists():
        raise SystemExit(
            f"Chroma DB not found at {CHROMA_PATH}\n"
            "Run: python scripts/embed_and_ingest.py"
        )

    print(f"Loading embedding model {EMBED_MODEL} ...")
    embed_model = SentenceTransformer(EMBED_MODEL, device=DEVICE)

    print("Connecting to Chroma ...")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        collection = client.get_collection(COLLECTION)
    except Exception:
        raise SystemExit(
            f"Collection '{COLLECTION}' not found in {CHROMA_PATH}\n"
            "Run: python scripts/embed_and_ingest.py"
        )

    where_filter = build_chroma_filter(args.access_level, args.pack)
    query_vec    = embed_query(embed_model, args.query)

    print(f"Retrieving top {args.top} chunks ...")
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=args.top,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"][0]:
        raise SystemExit("No chunks matched the query and filters. Try relaxing --access-level or --pack.")

    context_str, chunks = build_context(results)
    user_message = f"Context:\n{context_str}\n\nQuestion: {args.query}"

    if args.backend == "ollama":
        print(f"Calling Ollama ({model_name}) ...\n")
        answer = call_llm(args.backend, base_url, model_name, user_message, api_key)
    elif args.backend == "openai":
        print(f"Calling OpenAI-compatible endpoint ({model_name} @ {base_url}) ...\n")
        answer = call_llm(args.backend, base_url, model_name, user_message, api_key)
    else:  # ssh
        print(f"Calling NIM over SSH ({model_name} @ {ssh_user}@{ssh_host}:{remote_port}) ...\n")
        answer = call_llm_via_ssh(
            ssh_host, ssh_port, ssh_user, ssh_password, ssh_key_file,
            remote_port, model_name, user_message,
        )
    answer = strip_thinking(answer)

    print("=" * 60)
    print(answer)
    print("=" * 60)
    print("\nSources:")
    for c in chunks:
        label = f"  [{c['source_id']}]"
        if c["section"]:
            label += f" {c['section']}"
        if c["url"]:
            label += f" — {c['url']}"
        print(label)


if __name__ == "__main__":
    main()
