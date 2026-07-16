# NCNR Instrument Agent

An AI agent for NIST NCNR neutron scattering. It answers questions about the instruments, finds and inspects raw experiment data, runs reductions through the Reductus backend, and plots or exports the results — all through natural-language conversation in a browser or a terminal.

Every capability the agent has is a tool served over the **Model Context Protocol (MCP)**. [`scripts/mcpServer.py`](scripts/mcpServer.py) is a FastMCP server exposing sixteen tools; the two front-ends ([`app.py`](scripts/app.py) web UI and [`agent.py`](scripts/agent.py) CLI REPL) are LangGraph agents that bind those tools, and a second MCP server (`@ivotoby/openapi-mcp-server`) adds the NCNR metadata REST API on top. Because the tool layer is MCP, any MCP-compatible client — Claude Desktop, Claude Code, your own agent — can use the same tools without going through this repo's front-ends.

Retrieval-augmented generation over the instrument documentation is **one of those tools** (`gen_chunks`), not the whole system. The knowledge packs and the ingestion pipeline that build it live under [`rag/`](rag/) and are documented in [Knowledge base (RAG)](#knowledge-base-rag) below.

## Quick start

1. Create a `.env` file in the repo root:
   ```
   RCHAT_API_KEY=...      # required for the CLI agent and the ingestion pipeline
   ```
   The web UI is bring-your-own-key — each browser session supplies its own key per provider (OpenAI / Anthropic / Google / RChat) in a modal, so a server-side key is only an optional fallback.
2. `pip install -r requirements.txt`
3. Start Ollama with `nomic-embed-text` pulled (`ollama pull nomic-embed-text`) — the RAG tool embeds queries locally. Scripts auto-start `ollama serve` if it isn't running.
4. Run an agent:
   - **Web UI** — `python scripts/app.py`, then open [http://127.0.0.1:8000](http://127.0.0.1:8000). Enter your API key and pick a model in the browser; each tab gets its own conversation thread.
   - **CLI** — `python scripts/agent.py` for a terminal REPL, fixed to RChat's `gpt-oss-120b`.

To (re)build the knowledge base the `gen_chunks` tool retrieves from, see [Ingestion pipeline](#ingestion-pipeline).

## The agent

Both front-ends share the same MCP tool set, system prompt, and `MemorySaver`-backed per-session conversation memory. They differ only in how the model is chosen:

- **[`app.py`](scripts/app.py)** — FastAPI server at [http://127.0.0.1:8000](http://127.0.0.1:8000) serving [`static/index.html`](static/index.html), a `/chat` + `/chat/stream` (SSE) API, and `/download/raw`, `/download/export`, `/download/logsheet` proxies. Bring-your-own-key: `_provider_for_model` routes the chosen model to OpenAI/Anthropic/Google/RChat and builds a fresh agent per request. It also does **per-request tool scoping** — tools are grouped by workflow (knowledge_base / search / reduction / plot / admin) and only the groups a message implicates get bound, which trims the token cost of re-sending every schema on every model step; ambiguous messages fall back to the full set. **Context-editing middleware** clears old tool outputs from the model's view once the running token total gets large, and a `ReasoningChatOpenAI` subclass preserves the `reasoning_content` delta so the UI can show live thinking.
- **[`agent.py`](scripts/agent.py)** — terminal REPL, fixed to `gpt-oss-120b`, no BYOK or scoping. Needs `RCHAT_API_KEY`.

> **Model note:** RChat's `gemma-4-31B-it` cannot disambiguate between tools under `tool_choice="auto"` once 2+ tools are bound (it returns a blank tool call with no name/id, crashing `ToolMessage` construction). `gpt-oss-120b` and `NVIDIA-Nemotron-3-Super-120B-A12B-FP8` handle multi-tool selection correctly.

> **Adding a tool:** neither front-end auto-discovers tools. Each builds its LangChain tool set from a hand-maintained `MCP_TOOL_NAMES` allowlist, so a new `@mcp.tool` must be added to that list in **both** [`app.py`](scripts/app.py) and [`agent.py`](scripts/agent.py) (the lists are maintained separately and are not identical). For `app.py`, also add it to the right `TOOL_GROUPS` bucket. Return a `dict` or `str`, never a bare `list` — langchain-core passes a returned list through as message-content blocks un-stringified, which the OpenAI/RChat API rejects. See [`CLAUDE.md`](CLAUDE.md) for the full rationale.

## MCP tools ([`scripts/mcpServer.py`](scripts/mcpServer.py))

Run standalone as `python scripts/mcpServer.py` (stdio transport) to use from any MCP client, or let [`app.py`](scripts/app.py) / [`agent.py`](scripts/agent.py) load the same functions in-process.

### Knowledge base (RAG)

- `gen_chunks` — semantic retrieval from the `ncnr_rag` Chroma vectorstore, filtered by status/access level/instrument. Runs in-process against a cached Chroma handle opened at startup. Answers *how an instrument works*.
- `run_pipeline` — triggers the full ingestion pipeline as a subprocess.

### Finding & inspecting data

- `find_raw_data_paths` — looks up an experiment's raw files by experiment ID/instrument via the NCNR metadata API, attaching each file's real mtime (required by Reductus), a `download_url`, and a best-effort `intent`.
- `get_file_intent` — determines a single raw file's measurement intent. Fast path reads the harvested intent from the metadata DB by filename; falls back to loading just the file header through Reductus.
- `inspect_raw_file` — opens a raw NeXus/HDF5 file and reads the free-text descriptions, run comments, sample info, and logged fields that live *inside* the file — richer than the harvested metadata DB. Returns a curated `description`, a breadth-first `structure` outline, and any explicitly requested NeXus paths.
- `find_experiment_logsheet` — searches the NG7 / NGB30 experiment log-sheet PDF archives on the `charlotte.ncnr.nist.gov` SANS data share (2009 onwards) and returns download links. Files are named by date + PI surname (`YYYYMMDD_NG7_<PI>.pdf`), **not** by experiment number — search by PI or date.
- `search_instrument_schedule` — the historical experiment schedule for NG7, NGB30, or BT5: who ran what, and when. The only source for past beam time, experimenter names, and experiment titles.
- `list_instruments`, `get_instrument`, `list_datasources`, `list_data_files` — thin wrappers over `reductus.web_gui.api` for browsing instruments and data sources.

### Reduction

- `list_reduction_templates` — lists an instrument's reduction templates and their file-input nodes/intents.
- `reduce_files` — runs selected files through a named reduction template without hand-building the module graph. Results are compacted and truncated to a fixed size budget so they fit an LLM context window. The system prompt requires the agent to confirm the file list (and, for multi-node templates, the file-to-node assignment) with the user first.
- `export_reduction` — reduces as `reduce_files` does, then writes the target node's output to a downloadable ORSO file (`.ort` / `.orb`), served by `app.py`'s `/download/export`.

### Plotting

- `plot_reduction` — the correct way to plot a reduced curve: reduces as `reduce_files` does, then builds the figure server-side from the **full** Q/intensity arrays. (`reduce_files` truncates its arrays to an ~8-sample summary, so plotting *its* output yields an empty chart.)
- `generate_plot` — `exec`s model-authored Plotly code for **ad-hoc or user-supplied** x/y data only. Both plot tools return a `<div class="plotly-figure">` placeholder the web UI renders.

### External MCP server

- **NCNR metadata API** — [`openAPI.json`](openAPI.json) (OpenAPI 3.0 spec for the CHRNS metadata search API) is served through `@ivotoby/openapi-mcp-server`, invoked automatically via `npx` at agent startup. Adds `search-instruments`, `search-experiments`, and `search-datafiles`.

### Tool tests

- [`test_reductus_tools.py`](scripts/test_reductus_tools.py) — smoke-tests the Reductus tools directly (no MCP transport) against the real Reductus API and live NCNR servers. Needs network.
- [`test_get_file_intent.py`](scripts/test_get_file_intent.py) — tests `get_file_intent` accuracy against real NCNR reflectometry/CANDOR data, using the metadata API's trajectory-intent as ground truth. Needs network.

## Knowledge base (RAG)

The `gen_chunks` tool retrieves from a Chroma vectorstore ([`rag/chroma_db/`](rag/chroma_db/), collection `ncnr_rag`) built from six knowledge packs under [`rag/context_database/`](rag/context_database/):

```text
common/   Shared NCNR resources such as NICE, data access, sample environments, glossary terms
candor/   CANDOR-specific documentation and examples
vsans/    VSANS-specific documentation and examples
nse/      NSE-specific documentation and examples
magik/    MAGIK-specific documentation and examples
bt7/      BT7-specific documentation and examples
```

A RAG-ready pack is more than a folder of PDFs. Each contains original source snapshots (`originals/`), normalized Markdown with frontmatter metadata (`normalized/`), chunked JSONL records (`chunks/`), source inventory tracking (`source_inventory.csv`), manifests (`manifest.jsonl`), access-control labels (`access_policy.yaml`), a glossary (`glossary.yaml`), evaluation questions (`eval/`), and review artifacts (`review/`).

See [`PACK_STRUCTURE.md`](PACK_STRUCTURE.md) for the full layout and required metadata fields, and [`schemas/`](schemas/) for the JSON schemas backing chunks, eval questions, and manifests.

### Ingestion pipeline

To add content: list the source in `<pack>/source_inventory.csv`, drop the unmodified file under `<pack>/originals/`, then run

```
python rag/scripts/run_pipeline.py [--pack <pack>]
```

which chains normalize → chunk → validate → embed. Individual steps:

- [`run_pipeline.py`](rag/scripts/run_pipeline.py) — **main entry point**. Reads `RCHAT_API_KEY` from `.env` or the environment. Flags: `--pack`, `--model` (default `gemma-4-31B-it`), `--skip-normalize`, `--skip-validate`, `--dry-run`.
- [`full_document_ingestion.py`](rag/scripts/full_document_ingestion.py) — converts `originals/` to normalized Markdown via the RChat API. Interactive: streams each file's output and asks you to confirm the workflow stage before writing. PDF support needs `pypdf`.
- [`chunk_markdown.py`](rag/scripts/chunk_markdown.py) `<pack>` — stdlib-only heading-based chunker; splits `normalized/**/*.md` by H2 into `<pack>_chunks.generated.jsonl`.
- [`validate_pack.py`](rag/scripts/validate_pack.py) `<pack>` — validates required files/dirs, JSONL syntax, chunk/metadata completeness, and cross-references chunk `source_id`s against `source_inventory.csv`. Exits non-zero on error, aborting the pipeline.
- [`embed_and_ingest.py`](rag/scripts/embed_and_ingest.py) — embeds every pack's `chunks/*_chunks.jsonl` with `nomic-embed-text` via Ollama into the Chroma store.
- [`_common.py`](rag/scripts/_common.py) — shared helpers: pack list, Chroma bootstrap, JSONL loading, Ollama health-check/auto-start, eval CSV writer.

### Retrieval evaluation

- [`gen_chunks.py`](rag/scripts/gen_chunks.py) `"<question>"` — retrieval only, no LLM call; prints the top-k matching chunks. Backs the `gen_chunks` MCP tool. Flags: `--pack`, `--top`, `--max-distance`, `--access-level`.
- [`test_retrieval_embedding.py`](rag/scripts/test_retrieval_embedding.py) — runs each pack's `eval/*.jsonl` questions against Chroma; reports top-1/top-k accuracy and MRR.
- [`evaluate_retrieval_ragas.py`](rag/scripts/evaluate_retrieval_ragas.py) — RAGAS-standard Context Precision@K and Context Recall against each eval question's `expected_sources`.

### Templates ([`templates/`](templates/))

Starter files for adding pack content: [`normalized_document_template.md`](templates/normalized_document_template.md) (required YAML frontmatter), [`chunk_record_template.json`](templates/chunk_record_template.json), [`eval_question_template.json`](templates/eval_question_template.json), [`source_inventory_columns.md`](templates/source_inventory_columns.md), and [`doc_review_checklist.md`](templates/doc_review_checklist.md). [`source_inventory_template.xlsx`](source_inventory_template.xlsx) is a spreadsheet version of the source inventory.

### Content principles

**Source authority** — prefer current, reviewed, instrument-owner-approved documents over older tutorials, archived pages, or unreviewed notes. Mark old material `legacy`, `deprecated`, or `needs_review` rather than deleting it immediately.

**Access control** — every source, document, and chunk must carry an access level (`public`, `internal`, or `restricted`). Do not rely on folder location alone.

## Dependencies

[`requirements.txt`](requirements.txt) pins the agent layer (`fastmcp`, `reductus`, `langgraph`, `langchain-mcp-adapters`, `plotly`, `numpy`, `fastapi`, `uvicorn`, `python-dotenv`), the LangChain packages (`langchain`, `langchain-core`, `langchain-ollama`, `langchain-chroma`, `langchain-openai`, `langchain-anthropic`, `langchain-google-genai`), and the ingestion layer (`chromadb`, `pypdf`, `requests`, `openai`). None pull in `sentence_transformers` or PyTorch.

Run any script with `--help`, or see [`CLAUDE.md`](CLAUDE.md) for full per-script usage and flags.
