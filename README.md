# RAG Knowledge Pack Template

This repository is a set of RAG-ready knowledge packs for NIST NCNR neutron-scattering instrument documentation: `candor/`, `vsans/`, `nse/` (instrument-specific) and `common/` (shared NICE/NCNR-wide docs).

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

See `PACK_STRUCTURE.md` for the full folder layout and required metadata fields, and `schemas/` for the JSON schemas backing chunks, eval questions, and manifests.

## Environment variables

**Create a `.env` file in the repo root** (loaded automatically by scripts that need it):

```
RCHAT_API_KEY=...             # required for full_document_ingestion.py / run_pipeline.py / agent.py
```

## Recommended workflow

1. Add sources to `<pack>/source_inventory.csv`.
2. Save unmodified source files under `<pack>/originals/`.
3. Add your API key to `.env`: `RCHAT_API_KEY=...`
4. Run `python scripts/run_pipeline.py [--pack <pack>]` — this chains all four steps automatically:
   - Converts originals to normalized Markdown via the Groq API (interactive: confirms stage per file)
   - Chunks `normalized/**/*.md` into JSONL
   - Validates pack structure, JSONL syntax, and metadata
   - Embeds all chunks and loads them into the local Chroma vector store
5. Use `python scripts/query_rag.py "<question>" [--pack <pack>]` for end-to-end RAG question answering, or start the interactive agent with `python agent.py`.

Individual steps can also be run directly — see **Scripts** below.

## Scripts (`scripts/`)

- `run_pipeline.py` — **main entry point**; chains all four ingestion steps in order. Reads `RCHAT_API_KEY` from `.env` or the environment. Flags: `--pack`, `--model` (default: `moonshotai/kimi-k2-instruct`), `--skip-normalize`, `--skip-validate`, `--dry-run`.
- `full_document_ingestion.py` — converts files in `originals/` to normalized Markdown using the Groq API. Interactive: streams each file's output and asks you to confirm the workflow stage before writing. Args: `--model NAME` (required), `[--api-key KEY]`, `[--pack PACK]`, `[--dry-run]`. API key falls back to `RCHAT_API_KEY` env var.
- `chunk_markdown.py <pack>` — stdlib-only heading-based chunker; splits `normalized/**/*.md` by H2 headings into `<pack>_chunks.generated.jsonl`.
- `validate_pack.py <pack>` — validates a pack's required files/dirs, JSONL syntax, chunk/metadata completeness, and cross-references chunk `source_id`s against `source_inventory.csv`.
- `embed_and_ingest.py` — embeds every pack's `chunks/*_chunks.jsonl` with `nomic-embed-text` via Ollama and loads them into a Chroma `PersistentClient` at `./chroma_db` (collection `ncnr_rag`). Requires Ollama running with `nomic-embed-text` pulled.
- `gen_chunks.py "<question>"` — retrieval-only script; queries the Chroma vectorstore and prints the top-k matching chunks without calling an LLM. Useful for inspecting raw retrieval results or piping chunk text into another tool. Flags: `[--pack PACK]`, `[--top N]`, `[--max-distance D]`, `[--access-level public|internal|restricted]`.
- `query_rag.py "<question>"` — end-to-end RAG query: embeds the question, retrieves filtered chunks from Chroma, and calls an LLM (`--backend ollama|openai|ssh`) with the retrieved context.
- `test_retrieval_embedding.py` — embedding-based retrieval evaluation against the Chroma collection from `embed_and_ingest.py`; reports top-1/top-k accuracy and MRR.
- `evaluate_retrieval_ragas.py` — embedding-based retrieval evaluation using RAGAS-standard Context Precision@K and Context Recall against each eval question's `expected_sources`.
- `mcpServer.py` — **FastMCP server** exposing two tools over stdio: `gen_chunks` (semantic retrieval from the Chroma vectorstore) and `run_pipeline` (full ingestion pipeline). Run as `python scripts/mcpServer.py`; consumed by `agent.py` and any MCP-compatible client.
- `_common.py` — shared helpers (Chroma bootstrap, JSONL loading, Ollama health-check/auto-start, eval CSV writer) imported by the other scripts.

Run any script with `--help` or see `CLAUDE.md` for full per-script usage and flags.

`requirements.txt` pins `chromadb`, `paramiko`, `groq`, `pypdf`, the LangChain integration packages (`langchain-core`, `langchain-ollama`, `langchain-chroma`, `langchain-openai`), and the agent-layer packages (`fastmcp`, `langgraph`, `langchain-mcp-adapters`, `python-dotenv`).

## Interactive agent (`agent.py`)

`agent.py` is a LangGraph-based conversational agent that combines structured NCNR API access with the local RAG knowledge base in a single interactive REPL.

```
python agent.py
```

The agent connects to two data sources:

- **Structured API** — the NCNR CHRNS metadata REST API (`openAPI.json`) is wired in via an OpenAPI MCP server (`@ivotoby/openapi-mcp-server`, invoked automatically via `npx`). Exposes `search-instruments`, `search-experiments`, and `search-datafiles` tools.
- **RAG knowledge base** — `gen_chunks` (semantic retrieval from the local Chroma vectorstore) and `run_pipeline` (full ingestion trigger) are surfaced as LangChain `StructuredTool`s backed by `mcpServer.py`.

The LLM backend is NIST's RChat endpoint (OpenAI-compatible, model `gemma-4-31B-it`). Set `RCHAT_API_KEY` in `.env`. Conversation memory is maintained within a session via LangGraph's `MemorySaver`.

`openAPI.json` contains the OpenAPI 3.0 spec for the NCNR CHRNS metadata search API and is read at agent startup.

## Pack folders

```text
common/   Shared NCNR resources such as NICE, data access, sample environments, glossary terms
candor/   CANDOR-specific documentation and examples
vsans/    VSANS-specific documentation and examples
nse/      NSE-specific documentation and examples
```

## Templates (`templates/`)

Starter files for adding content to a pack:

- `normalized_document_template.md` — Markdown template with required YAML frontmatter fields
- `chunk_record_template.json` — minimal chunk record matching `schemas/chunk.schema.json`
- `eval_question_template.json` — eval question record matching `schemas/eval_question.schema.json`
- `source_inventory_columns.md` — column definitions for `source_inventory.csv`
- `doc_review_checklist.md` — checklist for reviewing a normalized document before marking it `current`

`source_inventory_template.xlsx` at the repo root is a spreadsheet version of the source inventory for teams that prefer Excel.

## Source authority principle

Prefer current, reviewed, instrument-owner-approved documents over older tutorials, archived pages, or unreviewed notes. Mark old material as `legacy`, `deprecated`, or `needs_review` rather than deleting it immediately.

## Access-control principle

Every source, document, and chunk must have an access level. Do not rely on folder location alone.

Suggested levels:

- `public`
- `internal`
- `restricted`
