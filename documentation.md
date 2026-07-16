# Getting started

A step-by-step walkthrough of getting the NCNR Instrument Agent running from a fresh clone: prerequisites, getting an RChat API key, wiring the key into the project, starting the server, rebuilding the knowledge base, and the bugs and gotchas worth knowing before you hit them.

For what the system *is* and what each tool does, see [`README.md`](README.md). For per-script flags, see [`CLAUDE.md`](CLAUDE.md).

---

## 1. Prerequisites

| Requirement | Why | Check |
|---|---|---|
| **Python 3.10+** | Everything | `python --version` |
| **Ollama** | `gen_chunks` embeds queries locally with `nomic-embed-text` | `ollama --version` |
| **Node.js / `npx`** | The NCNR metadata API is served through `@ivotoby/openapi-mcp-server`, launched via `npx` at agent startup | `npx --version` |
| **An LLM API key** | RChat (NIST-hosted), or OpenAI / Anthropic / Google | see step 2 |
| **Network access to NCNR** | Reduction, raw-file, log-sheet, and schedule tools all call live NCNR servers | — |

Ollama needs the embedding model pulled once:

```bash
ollama pull nomic-embed-text
```

You do not need to start `ollama serve` yourself — `rag/scripts/_common.py`'s `ensure_ollama()` starts it and pulls the model if it's missing. Pulling ahead of time just avoids a slow first run.

## 2. Getting an RChat API key

RChat is NIST's internally-hosted, OpenAI-compatible LLM proxy at `https://rchat.nist.gov/api/v1`. It fronts several models (`gpt-oss-120b`, `gemma-4-31B-it`, `Llama-4-Maverick-17B-128E-Instruct-FP8`, `NVIDIA-Nemotron-3-Super-120B-A12B-FP8`) and is what the CLI agent and the ingestion pipeline use by default.

1. Open <https://rchat.nist.gov> from a NIST-networked machine (or on VPN) and sign in with your NIST credentials.
2. Open your account settings and find the **API keys** section.
3. Create a new key and copy it immediately — the full value is typically shown only once.

> The exact menu wording in the RChat UI changes from time to time; if you can't find the API-key page, or your NIST account doesn't have RChat access yet, ask the RChat/CHRNS admins rather than guessing. This repo never provisions keys — it only reads one you already have.

RChat is not required. If you'd rather use a commercial provider, skip to the web UI (step 5) and enter an OpenAI, Anthropic, or Google key in the browser instead. RChat *is* required for [`scripts/agent.py`](scripts/agent.py) (hardcoded to RChat) and for the ingestion pipeline's normalization step.

## 3. Linking the key into the project

Create a file named `.env` in the **repo root** (next to `README.md`):

```bash
RCHAT_API_KEY=sk-...
```

Optional server-side fallback keys for the web UI, if you want it to work without anyone typing a key into the browser:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

How each entry point finds it:

- **[`scripts/app.py`](scripts/app.py)** and **[`scripts/agent.py`](scripts/agent.py)** call `load_dotenv()` at import, so the root `.env` is loaded into the environment automatically.
- **[`rag/scripts/run_pipeline.py`](rag/scripts/run_pipeline.py)** has its own small `_load_dotenv()` that reads the same root `.env`. It **skips keys already set in the environment**, so a real environment variable always wins over the file.
- An `.env` value is a *fallback*, not an override — exporting `RCHAT_API_KEY` in your shell takes precedence.

`.env` is already in [`.gitignore`](.gitignore). Don't commit it, and don't paste a key into `CLAUDE.md`, a script default, or a chat transcript.

Verify the key is visible to the app once it's running:

```bash
curl http://127.0.0.1:8000/api/key-status
```

## 4. Installing dependencies

On macOS/Linux, [`setup.sh`](setup.sh) does the whole thing — creates `.venv`, installs [`requirements.txt`](requirements.txt), and installs the Playwright Chromium browser:

```bash
bash setup.sh
# then: .venv/bin/python scripts/app.py
```

On Windows, do it by hand (`setup.sh` is a bash script and assumes `python3`):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

## 5. Starting the server

**Web UI** — the normal way to use this:

```bash
python scripts/app.py
```

Then open <http://127.0.0.1:8000>. On first load, a modal asks for an API key per provider and a model. The key lives in your browser session; a fresh agent is built per request from that key + model, and each tab gets its own conversation thread.

What you should see in the terminal on a healthy start: Ollama being reached (or auto-started), the Chroma collection opening once, `npx` fetching `@ivotoby/openapi-mcp-server`, then uvicorn listening on `127.0.0.1:8000`. Per-turn timing lines (`[timing]`) print for every message — model calls, time-to-first-token, wall time, token counts, per-tool durations.

The host and port are hardcoded (`uvicorn.run(app, host="127.0.0.1", port=8000)` at the bottom of [`app.py`](scripts/app.py)) — it is loopback-only by design, so edit that line if you need to expose it.

**CLI REPL** — a terminal chat, fixed to RChat's `gpt-oss-120b`, no BYOK and no tool scoping:

```bash
python scripts/agent.py
```

**MCP server standalone** — to use the tools from Claude Desktop, Claude Code, or your own MCP client instead of this repo's front-ends:

```bash
python scripts/mcpServer.py     # stdio transport
```

## 6. Building the knowledge base

The `gen_chunks` tool retrieves from a Chroma vectorstore at `rag/chroma_db/` (collection `ncnr_rag`). **`chroma_db/` is gitignored**, so a fresh clone has no vectorstore — `gen_chunks` returns nothing until you build one:

```bash
python rag/scripts/run_pipeline.py            # all packs
python rag/scripts/run_pipeline.py --pack candor
```

That chains normalize → chunk → validate → embed. Two things to know before you run it:

- **`originals/` is gitignored too.** Source files aren't in the repo, so a fresh clone has nothing to normalize. If you only have the committed `normalized/` Markdown, skip the first step: `--skip-normalize`.
- **Normalization is interactive and costs RChat calls.** It streams each file's converted output, then asks you to confirm the workflow stage before writing. It is not a background job.

Sanity-check retrieval without an LLM in the loop:

```bash
python rag/scripts/gen_chunks.py "How do I align the CANDOR detector?" --pack candor
```

---

## Known bugs and gotchas

### Models

- **`gemma-4-31B-it` breaks with 2+ tools bound.** Under `tool_choice="auto"` it returns a blank tool call with no name or id, which crashes `ToolMessage` construction. It's in the UI dropdown and it's the ingestion pipeline's default `--model` (single-purpose, no tools — fine there), but **do not pick it for chat**. `gpt-oss-120b` and `NVIDIA-Nemotron-3-Super-120B-A12B-FP8` handle multi-tool selection correctly.
- **Long multi-item runs used to truncate.** LangGraph's default recursion limit of 25 cut off runs that fanned out over many files; `app.py` sets `AGENT_RECURSION_LIMIT = 100`. A run that legitimately needs more still stops there.

### Plotting

- **Plotting a reduced curve with `generate_plot` yields an empty chart.** `reduce_files` truncates its arrays to an ~8-sample summary to fit the context window, so there's nothing real to plot. Use **`plot_reduction`**, which re-reduces and builds the figure server-side from the full Q/intensity arrays. This is the single most common way to get a confusing empty result.

### Reduction

- **reductus' `calc_template` has a latent unpacking bug.** `dataflow/calc.py`'s `_key()` builds `"module:terminal"` strings, but `calc_template` unpacks each result key as a 2-tuple — `too many values to unpack` for any real multi-node template. [`mcpServer.py`](scripts/mcpServer.py) works around it by calling `calc_terminal` once per (node, output terminal); reductus' fingerprint cache makes the repeated upstream work cheap after the first call. Don't "simplify" that back to `calc_template`.

### Log sheets

- **Log sheets are named by date + PI surname** (`YYYYMMDD_NG7_<PI>.pdf`), **not** by experiment or proposal number. Searching for an experiment ID finds nothing — search by PI or date.
- **`size_kb` is approximate and can be null.** It's parsed from the Apache autoindex's rounded size cell; exact bytes would cost a HEAD request per file.
- The old `\\charlotte.ncnr.nist.gov\Sans Data\...` UNC roots only resolved on a NIST-networked host with the share mounted. The tool now reads charlotte's public HTTP mirror, which works anywhere.

### Adding a tool

- **Neither front-end auto-discovers tools.** Registering `@mcp.tool()` alone only exposes it over stdio. To make it usable in the agents you must add the name to the hand-maintained `MCP_TOOL_NAMES` list in **both** [`app.py`](scripts/app.py) and [`agent.py`](scripts/agent.py) — the two lists are maintained separately and are not identical (`agent.py` omits `export_reduction`). For `app.py`, also add it to the right `TOOL_GROUPS` bucket (and `GROUP_SIGNALS` if it needs new trigger words), or per-request scoping won't pull in its workflow group.
- **Never return a bare `list` from a tool.** langchain-core keeps a returned list as message-content blocks instead of JSON-stringifying it whenever every element looks like a content block — vacuously true for an empty list — and the un-stringified list is then rejected by the OpenAI/RChat API (`content.0 is not a valid Content`). Wrap results in a dict, e.g. `{"count": n, "matches": [...]}`.

### Environment

- **Ollama must be reachable or nothing retrieves.** Scripts auto-start `ollama serve` and pull `nomic-embed-text`, but a first run with no model pulled is slow and looks like a hang.
- **`npx` must be on PATH.** Without Node, the metadata-API MCP server fails to start at agent startup. Windows is handled (`npx.cmd`).
- **Most tools need live NCNR network access.** Reduction, raw-file inspection, log sheets, and the schedule all hit NCNR servers; off-network they fail rather than degrade.
- **`setup.sh` is macOS/Linux only** — bash, `python3`, and `source .venv/bin/activate`. Use the manual steps on Windows.
