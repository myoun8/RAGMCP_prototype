# Plan: Feed query_rag.py to a model on the GB10 (NIM/Nemotron) box

> Status: planned, not yet implemented.

## Context
`scripts/query_rag.py` currently only talks to a local Ollama server (`http://localhost:11434/api/chat`). The user has a GB10-based machine likely self-hosting an NVIDIA NIM container serving a Nemotron model (pulled from build.nvidia.com), reachable only via an SSH tunnel / port-forward — not on the same LAN. NIM's inference API is OpenAI-compatible (`POST {base_url}/chat/completions`, response in `choices[0].message.content`), which is a different request/response shape than Ollama's `/api/chat`. The goal is to let `query_rag.py` send its retrieval-augmented prompt to that remote model, without breaking the existing local-Ollama workflow that the script's docstring and CLAUDE.md document today.

## Approach
Add an opt-in backend flag rather than replacing Ollama support, so the default invocation (`python scripts/query_rag.py "<question>"`) keeps working exactly as before.

Use Paramiko to implement ssh connection

**File: `scripts/query_rag.py`**

1. Generalize `call_ollama(model_name, user_message)` into a backend-aware `call_llm(backend, base_url, model_name, api_key, user_message)`:
   - `backend="ollama"` (default): keep current behavior — `POST {base_url}/api/chat`, payload `{model, messages, stream: False}`, parse `["message"]["content"]`. Default `base_url` stays `http://localhost:11434`.
   - `backend="openai"`: `POST {base_url}/chat/completions`, payload `{model, messages, stream: False}` (same `messages` list, just a different envelope/endpoint), parse `resp["choices"][0]["message"]["content"]`. If `api_key` is set, add `Authorization: Bearer {api_key}` header; self-hosted NIM through a tunnel typically needs no key, so this stays optional.
   - Keep the existing `urllib.error.URLError` handling, but make the "can't reach" message mention checking the SSH tunnel/port-forward when `backend="openai"`.

2. New CLI args in `main()`:
   - `--backend {ollama,openai}` (default `ollama`)
   - `--base-url` (override; default depends on backend — `http://localhost:11434` for ollama, unset/required for openai since the tunnel's local port varies)
   - `--api-key` (optional; falls back to env var, e.g. `NIM_API_KEY`, if unset)

3. Update the module docstring (lines 1-14) to document the second workflow, e.g.:
   ```
   ssh -L 8000:localhost:8000 user@gb10-host
   python scripts/query_rag.py "<question>" --backend openai --base-url http://localhost:8000/v1 --model <nemotron-model-id>
   ```

4. No changes to retrieval/Chroma/embedding logic — only the LLM-call section and arg parsing are touched.

## Verification
- Regression: run `python scripts/query_rag.py "<question>"` with no new flags against local Ollama (as today) and confirm identical output — confirms default path is unchanged.
- New path: set up the SSH tunnel to the GB10 box's NIM port, run with `--backend openai --base-url http://localhost:<forwarded-port>/v1 --model <nemotron-model-id>`, and confirm the script prints a real answer plus the sources list.
- Confirm the error message is useful if the tunnel isn't up (connection refused) and if the model name doesn't match what NIM has loaded (4xx from the API).
