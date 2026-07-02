# RAG Knowledge Pack Template

This repository is a set of RAG-ready knowledge packs for NIST NCNR neutron-scattering instrument documentation: [`candor/`](context_database/candor/), [`vsans/`](context_database/vsans/), [`nse/`](context_database/nse/), [`magik/`](context_database/magik/) (instrument-specific) and [`common/`](context_database/common/) (shared NICE/NCNR-wide docs).

A RAG-ready pack is more than a folder of PDFs. It contains:

- Original source files or source snapshots (`originals/`)
- Normalized Markdown files with frontmatter metadata (`normalized/`)
- Chunked JSONL records for ingestion (`chunks/`)
- Source inventory tracking (`source_inventory.csv`)
- Manifest files (`manifest.jsonl`)
- Access-control labels (`access_policy.yaml`)
- Glossary and synonym files (`glossary.yaml`)
- Evaluation questions (`eval/`)
- Review artifacts (`review/`)

See [`PACK_STRUCTURE.md`](PACK_STRUCTURE.md) for the full folder layout and required metadata fields, and [`schemas/`](schemas/) for the JSON schemas backing chunks, eval questions, and manifests.

## Environment variables

**Create a `.env` file in the repo root** (loaded automatically by scripts that need it):

```
RCHAT_API_KEY=...             # required for full_document_ingestion.py / run_pipeline.py / agent.py
```

## Recommended workflow

1. Add sources to `<pack>/source_inventory.csv`.
2. Save unmodified source files under `<pack>/originals/`.
3. Add your API key to `.env`: `RCHAT_API_KEY=...`
4. Run `python [scripts/run_pipeline.py](scripts/run_pipeline.py) [--pack <pack>]` — this chains all four steps automatically:
   - Converts originals to normalized Markdown via the RChat API (interactive: confirms stage per file)
   - Chunks `normalized/**/*.md` into JSONL
   - Validates pack structure, JSONL syntax, and metadata
   - Embeds all chunks and loads them into the local Chroma vector store
5. Query the knowledge base:
   - **Web UI** — `python [app.py](app.py)` then open [http://127.0.0.1:8000](http://127.0.0.1:8000) for a browser chat interface.
   - **CLI** — `python [agent.py](agent.py)` for a terminal REPL.

Individual steps can also be run directly — see **Scripts** below.

## Scripts (`scripts/`)

- [`run_pipeline.py`](scripts/run_pipeline.py) — **main entry point**; chains all four ingestion steps in order. Reads `RCHAT_API_KEY` from `.env` or the environment. Flags: `--pack`, `--model` (default: `gemma-31b`), `--skip-normalize`, `--skip-validate`, `--dry-run`.
- [`full_document_ingestion.py`](scripts/full_document_ingestion.py) — converts files in `originals/` to normalized Markdown using the RChat API. Interactive: streams each file's output and asks you to confirm the workflow stage before writing. Args: `--model NAME` (required), `[--api-key KEY]`, `[--pack PACK]`, `[--dry-run]`. API key falls back to `RCHAT_API_KEY` env var.
- [`chunk_markdown.py`](scripts/chunk_markdown.py) `<pack>` — stdlib-only heading-based chunker; splits `normalized/**/*.md` by H2 headings into `<pack>_chunks.generated.jsonl`.
- [`validate_pack.py`](scripts/validate_pack.py) `<pack>` — validates a pack's required files/dirs, JSONL syntax, chunk/metadata completeness, and cross-references chunk `source_id`s against `source_inventory.csv`.
- [`embed_and_ingest.py`](scripts/embed_and_ingest.py) — embeds every pack's `chunks/*_chunks.jsonl` with `nomic-embed-text` via Ollama and loads them into a Chroma `PersistentClient` at `./chroma_db` (collection `ncnr_rag`). Requires Ollama running with `nomic-embed-text` pulled.
- [`gen_chunks.py`](scripts/gen_chunks.py) `"<question>"` — retrieval-only script; queries the Chroma vectorstore and prints the top-k matching chunks without calling an LLM. Useful for inspecting raw retrieval results or piping chunk text into another tool. Flags: `[--pack PACK]`, `[--top N]`, `[--max-distance D]`, `[--access-level public|internal|restricted]`.
- [`test_retrieval_embedding.py`](scripts/test_retrieval_embedding.py) — embedding-based retrieval evaluation against the Chroma collection from [`embed_and_ingest.py`](scripts/embed_and_ingest.py); reports top-1/top-k accuracy and MRR.
- [`evaluate_retrieval_ragas.py`](scripts/evaluate_retrieval_ragas.py) — embedding-based retrieval evaluation using RAGAS-standard Context Precision@K and Context Recall against each eval question's `expected_sources`.
- [`mcpServer.py`](scripts/mcpServer.py) — **FastMCP server** exposing two tools over stdio: `gen_chunks` (semantic retrieval from the Chroma vectorstore) and `run_pipeline` (full ingestion pipeline). Run as `python scripts/mcpServer.py`; consumed by [`agent.py`](agent.py) and any MCP-compatible client.
- [`_common.py`](scripts/_common.py) — shared helpers (Chroma bootstrap, JSONL loading, Ollama health-check/auto-start, eval CSV writer) imported by the other scripts.

Run any script with `--help` or see [`CLAUDE.md`](CLAUDE.md) for full per-script usage and flags.

[`requirements.txt`](requirements.txt) pins `chromadb`, `paramiko`, `pypdf`, the LangChain integration packages (`langchain-core`, `langchain-ollama`, `langchain-chroma`, `langchain-openai`), and the agent-layer packages (`fastmcp`, `langgraph`, `langchain-mcp-adapters`, `python-dotenv`, `fastapi`, `uvicorn`).

## Agent interfaces

Both interfaces share the same LangGraph agent: structured NCNR API access + local RAG knowledge base, backed by the NIST RChat LLM (`gemma-4-31B-it`, OpenAI-compatible). Set `RCHAT_API_KEY` in `.env`.

The agent connects to two data sources:

- **Structured API** — the NCNR CHRNS metadata REST API ([`openAPI.json`](openAPI.json)) via an OpenAPI MCP server (`@ivotoby/openapi-mcp-server`, invoked automatically via `npx`). Exposes `search-instruments`, `search-experiments`, and `search-datafiles` tools.
- **RAG knowledge base** — `gen_chunks` (semantic retrieval from Chroma) and `run_pipeline` (ingestion trigger) surfaced as LangChain `StructuredTool`s backed by [`mcpServer.py`](scripts/mcpServer.py).

Conversation memory is maintained within a session via LangGraph's `MemorySaver`. [`openAPI.json`](openAPI.json) contains the OpenAPI 3.0 spec for the NCNR CHRNS metadata search API and is read at agent startup.

### Web UI ([`app.py`](app.py))

```
python app.py
```

Starts a FastAPI server at [http://127.0.0.1:8000](http://127.0.0.1:8000) serving a minimal browser chat interface ([`static/index.html`](static/index.html)). The agent is initialized once on startup and shared across requests; each browser tab gets its own conversation thread.

### CLI ([`agent.py`](agent.py))

```
python agent.py
```

Interactive terminal REPL — identical agent, no browser required.

## Pack folders

```text
common/   Shared NCNR resources such as NICE, data access, sample environments, glossary terms
candor/   CANDOR-specific documentation and examples
vsans/    VSANS-specific documentation and examples
nse/      NSE-specific documentation and examples
magik/    MAGIK-specific documentation and examples
```

([`common/`](context_database/common/), [`candor/`](context_database/candor/), [`vsans/`](context_database/vsans/), [`nse/`](context_database/nse/), [`magik/`](context_database/magik/))

## Templates ([`templates/`](templates/))

Starter files for adding content to a pack:

- [`normalized_document_template.md`](templates/normalized_document_template.md) — Markdown template with required YAML frontmatter fields
- [`chunk_record_template.json`](templates/chunk_record_template.json) — minimal chunk record matching [`schemas/chunk.schema.json`](schemas/chunk.schema.json)
- [`eval_question_template.json`](templates/eval_question_template.json) — eval question record matching [`schemas/eval_question.schema.json`](schemas/eval_question.schema.json)
- [`source_inventory_columns.md`](templates/source_inventory_columns.md) — column definitions for `source_inventory.csv`
- [`doc_review_checklist.md`](templates/doc_review_checklist.md) — checklist for reviewing a normalized document before marking it `current`

[`source_inventory_template.xlsx`](source_inventory_template.xlsx) at the repo root is a spreadsheet version of the source inventory for teams that prefer Excel.

## Source authority principle

Prefer current, reviewed, instrument-owner-approved documents over older tutorials, archived pages, or unreviewed notes. Mark old material as `legacy`, `deprecated`, or `needs_review` rather than deleting it immediately.

## Access-control principle

Every source, document, and chunk must have an access level. Do not rely on folder location alone.

Suggested levels:

- `public`
- `internal`
- `restricted`
