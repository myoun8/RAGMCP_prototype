# RAG Knowledge Pack Template

This repository is a set of RAG-ready knowledge packs for NIST NCNR neutron-scattering instrument documentation: [`candor/`](rag/context_database/candor/), [`vsans/`](rag/context_database/vsans/), [`nse/`](rag/context_database/nse/), [`magik/`](rag/context_database/magik/), [`bt7/`](rag/context_database/bt7/) (instrument-specific) and [`common/`](rag/context_database/common/) (shared NICE/NCNR-wide docs). The packs live under [`rag/context_database/`](rag/context_database/).

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
RCHAT_API_KEY=...             # required for full_document_ingestion.py / run_pipeline.py / agent.py (CLI)
```

`app.py` (the web UI) is bring-your-own-key instead: each browser session enters its own API key(s) per provider (OpenAI/Anthropic/Google/RChat) in the UI, so no server-side `.env` key is needed for it.

## Recommended workflow

1. Add sources to `<pack>/source_inventory.csv`.
2. Save unmodified source files under `<pack>/originals/`.
3. Add your API key to `.env`: `RCHAT_API_KEY=...`
4. Run `python [rag/scripts/run_pipeline.py](rag/scripts/run_pipeline.py) [--pack <pack>]` — this chains all four steps automatically:
   - Converts originals to normalized Markdown via the RChat API (interactive: confirms stage per file)
   - Chunks `normalized/**/*.md` into JSONL
   - Validates pack structure, JSONL syntax, and metadata
   - Embeds all chunks and loads them into the local Chroma vector store (at [`rag/chroma_db/`](rag/chroma_db/))
5. Query the knowledge base:
   - **Web UI** — `python [scripts/app.py](scripts/app.py)` then open [http://127.0.0.1:8000](http://127.0.0.1:8000) for a browser chat interface.
   - **CLI** — `python [scripts/agent.py](scripts/agent.py)` for a terminal REPL.

Individual steps can also be run directly — see **Scripts** below.

## Scripts

The scripts are split across two directories: the RAG ingestion/evaluation pipeline lives in [`rag/scripts/`](rag/scripts/), and the agent/serving layer lives in [`scripts/`](scripts/).

### Ingestion & evaluation ([`rag/scripts/`](rag/scripts/))

- [`run_pipeline.py`](rag/scripts/run_pipeline.py) — **main entry point**; chains all four ingestion steps in order. Reads `RCHAT_API_KEY` from `.env` or the environment. Flags: `--pack`, `--model` (default: `gemma-4-31B-it`), `--skip-normalize`, `--skip-validate`, `--dry-run`.
- [`full_document_ingestion.py`](rag/scripts/full_document_ingestion.py) — converts files in `originals/` to normalized Markdown using the RChat API (via the `openai` SDK against the RChat OpenAI-compatible endpoint). Interactive: streams each file's output and asks you to confirm the workflow stage before writing. Args: `--model NAME` (required), `[--api-key KEY]`, `[--pack PACK]`, `[--dry-run]`. API key falls back to `RCHAT_API_KEY` env var. PDF support requires `pypdf`.
- [`chunk_markdown.py`](rag/scripts/chunk_markdown.py) `<pack>` — stdlib-only heading-based chunker; splits `normalized/**/*.md` by H2 headings into `<pack>_chunks.generated.jsonl`.
- [`validate_pack.py`](rag/scripts/validate_pack.py) `<pack>` — validates a pack's required files/dirs, JSONL syntax, chunk/metadata completeness, and cross-references chunk `source_id`s against `source_inventory.csv`.
- [`embed_and_ingest.py`](rag/scripts/embed_and_ingest.py) — embeds every pack's `chunks/*_chunks.jsonl` with `nomic-embed-text` via Ollama and loads them into a Chroma `PersistentClient` at [`rag/chroma_db/`](rag/chroma_db/) (collection `ncnr_rag`). Requires Ollama running with `nomic-embed-text` pulled.
- [`gen_chunks.py`](rag/scripts/gen_chunks.py) `"<question>"` — retrieval-only script; queries the Chroma vectorstore and prints the top-k matching chunks without calling an LLM. Useful for inspecting raw retrieval results or piping chunk text into another tool. Flags: `[--pack PACK]`, `[--top N]`, `[--max-distance D]`, `[--access-level public|internal|restricted]`.
- [`test_retrieval_embedding.py`](rag/scripts/test_retrieval_embedding.py) — embedding-based retrieval evaluation against the Chroma collection from [`embed_and_ingest.py`](rag/scripts/embed_and_ingest.py); reports top-1/top-k accuracy and MRR.
- [`evaluate_retrieval_ragas.py`](rag/scripts/evaluate_retrieval_ragas.py) — embedding-based retrieval evaluation using RAGAS-standard Context Precision@K and Context Recall against each eval question's `expected_sources`.
- [`_common.py`](rag/scripts/_common.py) — shared helpers (pack list, Chroma bootstrap, JSONL loading, Ollama health-check/auto-start, eval CSV writer) imported by the other scripts.

### Agent & serving layer ([`scripts/`](scripts/))

- [`mcpServer.py`](scripts/mcpServer.py) — **FastMCP server** exposing ten tools over stdio: `run_pipeline` (full ingestion pipeline), `gen_chunks` (semantic retrieval from the Chroma vectorstore), and eight Reductus tools backed by `reductus.web_gui.api` — `list_instruments`, `get_instrument`, `list_datasources`, `list_data_files` (browse a data source by path), `find_raw_data_paths` (look up an NCNR experiment's raw files by experiment ID/instrument via the NCNR metadata API, with real path/mtime attached), `list_reduction_templates` (find a template's file-input nodes and their intent), `reduce_files` (run selected files through a named reduction template without hand-building the module graph), and `get_file_intent` (determine a single raw file's measurement intent from just its header, without a full reduction). Run as `python scripts/mcpServer.py`; consumed by [`agent.py`](scripts/agent.py), [`app.py`](scripts/app.py), and any MCP-compatible client.
- [`agent.py`](scripts/agent.py) — CLI REPL agent, fixed to the NIST RChat `gpt-oss-120b` model. Run as `python scripts/agent.py`.
- [`app.py`](scripts/app.py) — FastAPI web-UI server (bring-your-own-key). Run as `python scripts/app.py`.
- [`test_reductus_tools.py`](scripts/test_reductus_tools.py) — smoke-tests the Reductus tools above directly (no MCP transport) against the real reductus API and live NCNR servers. Run as `python scripts/test_reductus_tools.py` (needs network access; importing `mcpServer.py` also starts Ollama if it isn't running).
- [`test_get_file_intent.py`](scripts/test_get_file_intent.py) — tests `get_file_intent` against real NCNR reflectometry/CANDOR data, checking intent *accuracy* against the NCNR metadata API's trajectory-intent ground truth (plus the two error paths). Run as `python scripts/test_get_file_intent.py` (needs network access).

Run any script with `--help` or see [`CLAUDE.md`](CLAUDE.md) for full per-script usage and flags.

[`requirements.txt`](requirements.txt) pins `chromadb`, `pypdf`, `requests`, `openai`, the LangChain packages (`langchain`, `langchain-core`, `langchain-ollama`, `langchain-chroma`, `langchain-openai`, `langchain-anthropic`, `langchain-google-genai`), and the agent-layer packages (`fastmcp`, `reductus`, `langgraph`, `langchain-mcp-adapters`, `python-dotenv`, `fastapi`, `uvicorn`).

## Agent interfaces

Both interfaces share the same LangGraph tool set — structured NCNR API access + local RAG knowledge base + Reductus reduction tools — but differ in how the underlying LLM is chosen:

- **`agent.py`** (CLI) is fixed to the NIST RChat `gpt-oss-120b` model. Set `RCHAT_API_KEY` in `.env`.
- **`app.py`** (web UI) is bring-your-own-key: the browser lets you pick a model from a small per-provider catalog (OpenAI, Anthropic, Google, or RChat) and supply that provider's API key yourself; a fresh agent is built per request from your chosen model/key, sharing the same tools, system prompt, and `MemorySaver`-backed conversation memory.

> **Model note:** the RChat-hosted `gemma-4-31B-it` model cannot disambiguate between tools under `tool_choice="auto"` once 2+ tools are bound (it returns a blank tool call with no name/id, which crashes `ToolMessage` construction). `gpt-oss-120b` and `NVIDIA-Nemotron-3-Super-120B-A12B-FP8` both handle multi-tool selection correctly; `agent.py` uses `gpt-oss-120b`.

The agent connects to three data sources:

- **Structured API** — the NCNR CHRNS metadata REST API ([`openAPI.json`](openAPI.json)) via an OpenAPI MCP server (`@ivotoby/openapi-mcp-server`, invoked automatically via `npx`). Exposes `search-instruments`, `search-experiments`, and `search-datafiles` tools.
- **RAG knowledge base** — `gen_chunks` (semantic retrieval from Chroma) and `run_pipeline` (ingestion trigger) surfaced as LangChain `StructuredTool`s backed by [`mcpServer.py`](scripts/mcpServer.py).
- **Reductus reduction service** — `list_instruments`, `get_instrument`, `list_datasources`, `list_data_files`, `find_raw_data_paths`, `list_reduction_templates`, `reduce_files`, and `get_file_intent`, also surfaced as `StructuredTool`s backed by [`mcpServer.py`](scripts/mcpServer.py). The system prompt requires the agent to confirm which files (and, for multi-node templates, which file-to-node/intent assignment) with the user before calling `reduce_files`.

Conversation memory is maintained within a session via LangGraph's `MemorySaver`. [`openAPI.json`](openAPI.json) contains the OpenAPI 3.0 spec for the NCNR CHRNS metadata search API and is read at agent startup.

### Web UI ([`app.py`](scripts/app.py))

```
python scripts/app.py
```

Starts a FastAPI server at [http://127.0.0.1:8000](http://127.0.0.1:8000) serving a minimal browser chat interface ([`static/index.html`](static/index.html)). Enter your API key(s) and pick a model in the browser; each tab gets its own conversation thread.

### CLI ([`agent.py`](scripts/agent.py))

```
python scripts/agent.py
```

Interactive terminal REPL — same tools, fixed to `gpt-oss-120b`, no browser required.

## Pack folders

All packs live under [`rag/context_database/`](rag/context_database/):

```text
common/   Shared NCNR resources such as NICE, data access, sample environments, glossary terms
candor/   CANDOR-specific documentation and examples
vsans/    VSANS-specific documentation and examples
nse/      NSE-specific documentation and examples
magik/    MAGIK-specific documentation and examples
bt7/      BT7-specific documentation and examples
```

([`common/`](rag/context_database/common/), [`candor/`](rag/context_database/candor/), [`vsans/`](rag/context_database/vsans/), [`nse/`](rag/context_database/nse/), [`magik/`](rag/context_database/magik/), [`bt7/`](rag/context_database/bt7/))

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
