# chatapp — 4-layer memory chat application (Parts 1–3)

Multi-thread chat application with a 4-layer cognitive memory architecture.
Part 1 is the storage foundation; Part 2 is the core orchestration engine
(live LLM path + async memory-maintenance workers) running Llama 3.2 locally
via Ollama's OpenAI-compatible endpoint; Part 3 is the HTTP/SSE API plus a
React + Zustand multi-thread UI.

| Layer | Name | Backend | Where |
|---|---|---|---|
| 1 | Working Context | Relational (`conversations`, `messages`) | `db/models.py` |
| 2 | Persistent Memory | Relational (`user_profiles`, JSONB doc) | `db/models.py` + `schemas.PersistentProfile` |
| 3 | Compacted History | ChromaDB collection `compacted_history` | `vectorstore.py` |
| 4 | Indexed Files | ChromaDB collection `indexed_files` | `vectorstore.py` |

## Layout

- `config.py` — storage URLs/paths from env vars (Postgres in prod, SQLite fallback for dev).
- `db/base.py` — engine, session factory, `init_db()`.
- `db/models.py` — `User`, `UserProfile`, `Conversation`, `Message` ORM models.
- `schemas.py` — Pydantic v2 schemas: the Layer-2 profile document shape, flat
  Chroma-safe metadata models for Layers 3/4, and API read models.
- `vectorstore.py` — `VectorStore` wrapping a `chromadb.PersistentClient` with
  tenant-scoped (per-`user_id`) upsert/search/delete for both collections.
- `seed.py` — populates all four layers with example data and prints the objects.
- `llm.py` — async `openai` SDK client against Ollama (`llama3.2`):
  `complete()` for the live path, `complete_json()` for worker calls,
  `estimate_tokens()` for the compaction budget.
- `orchestrator.py` — `generate_chat_response(user_input, conversation_id)`:
  persists the user turn, gathers all four layers, builds the prioritized
  system prompt (Profile > Files > History > Working context), runs the
  completion, persists the assistant turn, schedules the workers.
- `workers.py` — async background workers: `run_compaction` (Layer 1 → 3)
  and `run_memory_extraction` (Layer 1 → 2).
- `demo_part2.py` — live end-to-end demo of the whole pipeline.
- `api.py` — FastAPI surface: session/profile/conversations/messages routes
  plus the SSE chat route streaming `orchestrator.stream_chat_response`
  events (start / token / done / error). Serves `frontend/dist` at `/` when
  built.
- `frontend/` — Vite + React + Zustand UI:
  - `src/store/chatStore.js` — thread list, `activeConversationId`, and the
    active thread's message buffer (`switchConversation` clears + reloads;
    a load token discards stale fetches; mid-stream tokens for a
    backgrounded thread are dropped).
  - `src/store/userStore.js` — global Layer-2 state (session + profile),
    deliberately separate from all chat state.
  - `src/api/client.js` — fetch client + incremental SSE reader.
  - `src/components/Sidebar.jsx`, `src/components/ChatArea.jsx` — thread
    manager and message view / composer.

## Run

```bash
pip install -r chatapp/requirements.txt
ollama pull llama3.2          # local LLM (any OpenAI-compatible endpoint works)
python -m chatapp.seed        # Part 1: storage + example data
python -m chatapp.demo_part2  # Part 2: live orchestration demo

# Part 3 — web app
python -m uvicorn chatapp.api:app --port 8001
cd chatapp/frontend && npm install && npm run dev   # dev UI at :5173 (proxies /api)
# or serve a production build from FastAPI itself:
cd chatapp/frontend && npm run build                # then open http://127.0.0.1:8001
```

Configuration (optional):

```bash
export CHATAPP_DATABASE_URL="postgresql+psycopg2://user:pass@host/chatapp"
export CHATAPP_VECTOR_DB_PATH="/var/lib/chatapp/vector_db"
export CHATAPP_LLM_BASE_URL="http://localhost:11434/v1"   # any OpenAI-compatible API
export CHATAPP_CHAT_MODEL="llama3.2"
export CHATAPP_UTILITY_MODEL="llama3.2"                   # cheap worker model
export CHATAPP_COMPACTION_TOKEN_LIMIT="3000"
```

## Design notes

- **Message ordering** uses a per-conversation `seq` ordinal with a unique
  constraint on `(conversation_id, seq)` — unambiguous where timestamps can
  collide, and `Conversation.compacted_through_seq` marks how far Layer-3
  compaction has progressed.
- **Profile writes are validated**: `UserProfile.data` is schemaless in the DB
  (JSONB) but every write goes through `PersistentProfile.model_dump()`, and
  `version` supports optimistic locking for concurrent memory-update jobs.
- **Vector record ids are deterministic** (`summary::<convo>::<start>-<end>`,
  `file::<file_id>::<idx>`) so writes are idempotent upserts.
- **Every vector query filters on `user_id`** — retrieval is always
  tenant-scoped.
- The embedding function is injectable on `VectorStore(...)`; default is
  Chroma's built-in all-MiniLM-L6-v2 (local ONNX).
