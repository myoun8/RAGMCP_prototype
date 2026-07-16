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

## 7. Developing and connecting a tool

A tool is a plain Python function in [`scripts/mcpServer.py`](scripts/mcpServer.py). Writing it is the easy part; **connecting it to the agents is four hand-maintained lists, none of which are auto-discovered.** If you only do step 1, the tool exists over the MCP stdio transport and is invisible to both front-ends.

### Step 1 — write the function

```python
@mcp.tool()
def find_experiment_logsheet(instrument: str, query: str = "", top: int = 15) -> dict:
    """Searches the NG7 / NGB30 experiment log-sheet PDF archives and returns
    download links. Log sheets are named by date + PI surname, NOT by
    experiment number — search by PI or date."""
    ...
```

Three things carry real weight here:

- **The docstring is the tool's prompt.** Both front-ends pass `getattr(mcpServer, name).__doc__` straight to the model as the tool description — it is the only thing the model reads when deciding whether to call your tool. Say what it does, and say when *not* to use it; the existing docstrings do exactly this (`gen_chunks` ends with "Do NOT use this tool to answer questions about raw data files"). A vague docstring shows up as the model calling the wrong tool.
- **Type-annotate every parameter.** `StructuredTool.from_function` derives the JSON schema the model fills in from the signature. An un-annotated parameter gives the model no idea what to pass.
- **Return a `dict` or a `str` — never a bare `list`.** See the gotcha below; this one bites at runtime, not at import.

If your tool returns anything large (metadata blobs, reduction output, file structure), pass it through `_fit_result()` on the way out, like the reduction tools do. It compacts and truncates to a fixed character budget so a single result can't blow the context window.

### Step 2 — register it in both front-ends

Add the function name to the `MCP_TOOL_NAMES` list in **both** [`app.py`](scripts/app.py#L113) and [`agent.py`](scripts/agent.py#L24). Each front-end builds its LangChain tool set by looping that list and doing `getattr(mcpServer, name)` — a name that isn't in the list is never loaded.

The two lists are maintained separately and **are not identical today**: `agent.py` omits `search_instrument_schedule`. That's the normal failure mode — someone adds a tool to one list and not the other, and it works in the web UI and silently doesn't exist in the CLI. Update both unless you deliberately want the tool in only one.

### Step 3 — put it in a tool group (`app.py` only)

[`app.py`](scripts/app.py#L219) doesn't bind all sixteen tools on every request. `_select_tool_names` matches the user's message against `GROUP_SIGNALS` keywords, picks the implicated groups out of `TOOL_GROUPS` (plus anything they chain into via `GROUP_DEPENDENCIES`), and binds only those — every model step re-sends every bound tool's full JSON schema, so this is a real input-token saving on the hot path.

So add your tool to the right `TOOL_GROUPS` bucket (`knowledge_base` / `search` / `reduction` / `plot` / `admin`), and add trigger words to that group's `GROUP_SIGNALS` entry if the existing ones wouldn't catch a question aimed at your tool. Keep signals broad — a false positive just re-adds a schema, while a false negative drops a tool the run needed.

Two safety valves mean scoping can't silently hide your tool: a message with no recognized signal at all falls back to the full set, and any loaded tool that isn't in `_KNOWN_TOOL_NAMES` (i.e. any tool you forgot to group) is always kept. So skipping this step is *safe* — it just means your tool is always bound and never pulls in its workflow's companion tools.

### Step 4 — give it a status label (optional, `app.py` only)

`TOOL_STATUS` at [`app.py:780`](scripts/app.py#L780) maps a tool name to the text the UI shows while it runs (`"Searching experiment log sheets…"`). Without an entry the UI falls back to `Using <tool_name>…`, which works but reads like debug output. (`search_instrument_schedule` currently has no entry.)

### What you get for free

- **Exceptions won't kill the run.** `app.py` wraps every tool in `_safe_tool`, which catches anything your function raises and returns it as a `TOOL ERROR in <name>: ...` string, so the model can report that one item as failed and carry on with the rest of a multi-file request. Don't add defensive try/except just to keep the agent alive — do add one where you can return a *useful* message instead of a traceback.
- **Parallel fan-out.** The MULTI-ITEM system prompt tells the model to issue per-item tool calls in a single turn, and LangGraph's `ToolNode` runs them concurrently. Your function should be safe to call several times at once.
- **Timing.** `_TurnMetrics` records per-tool durations and streams them to the UI and the `ncnr.timing` logger with no work on your side.

### Testing it

Call the function directly — no MCP transport, no agent — the way [`test_reductus_tools.py`](scripts/test_reductus_tools.py) does:

```python
import mcpServer
print(mcpServer.find_experiment_logsheet("ng7", "smith"))
```

Note that importing `mcpServer` starts Ollama and opens Chroma, so a bare import takes a few seconds. Then check the wiring end-to-end by asking the web UI a question phrased the way a user would — if the model never calls your tool, the problem is almost always the docstring (step 1) or a missing `GROUP_SIGNALS` keyword (step 3).

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

*Full walkthrough in [step 7](#7-developing-and-connecting-a-tool); these are the two that bite hardest.*

- **Neither front-end auto-discovers tools.** Registering `@mcp.tool()` alone only exposes it over stdio. To make it usable in the agents you must add the name to the hand-maintained `MCP_TOOL_NAMES` list in **both** [`app.py`](scripts/app.py) and [`agent.py`](scripts/agent.py) — the two lists are maintained separately and are not identical (`agent.py` omits `search_instrument_schedule`).
- **Never return a bare `list` from a tool.** langchain-core keeps a returned list as message-content blocks instead of JSON-stringifying it whenever every element looks like a content block — vacuously true for an empty list — and the un-stringified list is then rejected by the OpenAI/RChat API (`content.0 is not a valid Content`). Wrap results in a dict, e.g. `{"count": n, "matches": [...]}`.

### Environment

- **Ollama must be reachable or nothing retrieves.** Scripts auto-start `ollama serve` and pull `nomic-embed-text`, but a first run with no model pulled is slow and looks like a hang.
- **`npx` must be on PATH.** Without Node, the metadata-API MCP server fails to start at agent startup. Windows is handled (`npx.cmd`).
- **Most tools need live NCNR network access.** Reduction, raw-file inspection, log sheets, and the schedule all hit NCNR servers; off-network they fail rather than degrade.
- **`setup.sh` is macOS/Linux only** — bash, `python3`, and `source .venv/bin/activate`. Use the manual steps on Windows.
