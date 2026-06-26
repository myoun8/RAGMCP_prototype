# rag-knowledge-pack-template

A RAG knowledge-pack template for NIST NCNR neutron-scattering instrument documentation. Four packs: `candor/`, `vsans/`, `nse/` (instrument-specific) and `common/` (shared NICE/NCNR-wide docs).

## Pack structure (per `PACK_STRUCTURE.md`)

Each pack (`<pack>/`) contains:
- `README.md`, `source_inventory.csv`, `manifest.jsonl`, `glossary.yaml`, `access_policy.yaml`, `ingest_config.yaml`
- `originals/` — unmodified source material (web_pages, pdfs, papers, manuals, notebooks, scripts, data_examples)
- `normalized/` — Markdown docs with YAML frontmatter (doc_id, source_id, instrument, workflow_stage, source_type, access_level, status, owner, last_reviewed, source_url_or_path, citation_required), organized into stage subfolders (overview, instrument_control, experiment_planning, data_access/raw_data, metadata, sample_environment, troubleshooting, citations_publications, etc.)
- `chunks/` — JSONL chunk records (chunk_id, doc_id, source_id, text, metadata) generated from `normalized/`
- `eval/` — JSONL evaluation questions for retrieval testing
- `review/` — review artifacts

Schemas for these record types live in `schemas/`.

## Scripts (`scripts/`)

- `chunk_markdown.py` — splits `normalized/**/*.md` by H2 headings into `<pack>_chunks.generated.jsonl`. Stdlib only.
- `embed_and_ingest.py` — embeds every pack's `chunks/*_chunks.jsonl` with `BAAI/bge-large-en-v1.5` (via `sentence_transformers`) and loads them into a Chroma `PersistentClient` at `./chroma_db` (collection `ncnr_rag`). Requires `sentence_transformers` and `chromadb` (not pinned anywhere — install manually).
- `test_retrieval.py` — stdlib-only TF-IDF retrieval/evaluation tool.
  - `python scripts/test_retrieval.py <pack> "<query>" [--top N]` — single query
  - `python scripts/test_retrieval.py <pack> --evaluate [--detail]` — evaluate one pack against its eval questions
  - `python scripts/test_retrieval.py --evaluate-all [--output-csv file.csv]` — evaluate all packs, writes `retrieval_results.csv`
  - Loads ALL `*.jsonl` files under a pack's `chunks/` dir, so a pack must not contain duplicate/derived chunk files alongside the canonical one.
- `validate_pack.py` — validates a pack's required files/dirs, JSONL syntax, chunk/metadata field completeness, and cross-references chunk `source_id`s against `source_inventory.csv`. Run as `python scripts/validate_pack.py <pack>`.
- `query_rag.py` — end-to-end RAG query against an LLM. Embeds the query with `BAAI/bge-large-en-v1.5`, retrieves from the Chroma `ncnr_rag` collection (filtered by `status=current`, `access_level` cascade, optional `instrument`/pack), then calls an LLM with the retrieved chunks as context. Three backends: `--backend ollama` (default) calls a local Ollama server (`ollama serve`); `--backend openai` calls any OpenAI-compatible chat-completions endpoint (e.g. an NVIDIA NIM container, such as `nvidia/llama-3.3-nemotron-super-49b-v1.5`) reached via a manually-established SSH tunnel (`ssh -L <port>:localhost:<port> user@host`) — requires `--base-url` and `--model`, with optional `--api-key`/`NIM_API_KEY` env var; `--backend ssh` instead SSHes into the remote host itself (via `paramiko`) and curls the NIM container's own loopback directly — no tunnel needed — requires `--model` plus `--ssh-host`/`--ssh-user` and `--ssh-password` or `--ssh-key-file` (or the `GB10_SSH_HOST`/`GB10_SSH_USER`/`GB10_SSH_PASSWORD`/`GB10_SSH_KEY_FILE` env vars). Requires `embed_and_ingest.py` to have been run first, plus `sentence_transformers` and `chromadb` (and `paramiko` for `--backend ssh`). Run as `python scripts/query_rag.py "<question>" [--pack candor] [--top N] [--backend ollama|openai|ssh] [--base-url URL] [--model NAME] [--api-key KEY] [--ssh-host HOST] [--ssh-user USER] [--access-level public|internal|restricted]`.
- `test_retrieval_embedding.py` — embedding-based counterpart to `test_retrieval.py`'s TF-IDF evaluation: runs each pack's `eval/*.jsonl` questions against the Chroma `ncnr_rag` collection (via `embed_and_ingest.py` output) and reports top-1/top-k accuracy and MRR, for apples-to-apples comparison with the TF-IDF baseline. Requires `chromadb` and `sentence_transformers`. Run as `python scripts/test_retrieval_embedding.py <pack> --evaluate [--detail]` or `--evaluate-all [--output-csv file.csv]`.
- `evaluate_retrieval_ragas.py` — embedding-based retrieval evaluation using RAGAS-standard Context Precision@K and Context Recall, computed directly from each eval question's `expected_sources` ground truth (no fuzzy text-similarity approximation). Requires `embed_and_ingest.py` to have been run first. Run as `python scripts/evaluate_retrieval_ragas.py <pack> [--top N] [--detail]` or `--evaluate-all [--output-csv file.csv]`.

`requirements.txt` pins `sentence_transformers` and `chromadb`, needed before running `embed_and_ingest.py`, `query_rag.py`, `test_retrieval_embedding.py`, or `evaluate_retrieval_ragas.py`. `query_rag.py`'s default `--backend ollama` additionally requires a running Ollama instance with a pulled model; `--backend openai` requires a reachable OpenAI-compatible endpoint instead (no Ollama needed).
