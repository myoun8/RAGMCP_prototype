"""Core orchestration engine: the 4-layer memory pipeline.

Two entry points, both built from the same prepare/finalize halves:

  generate_chat_response() — request/response: returns the complete reply
                             (Part 2's original contract, used by tests).
  stream_chat_response()   — async generator of UI events (start / token /
                             done) backing Part 3's SSE route.

Per turn the pipeline:

  1. persists the incoming user message (Layer 1 write),
  2. gathers all four memory layers,
  3. builds one structured system prompt with the priority hierarchy
     Layer 2 Profile > Layer 4 Files > Layer 3 History > Layer 1 Context,
  4. runs the live Llama 3.2 completion (buffered or streamed),
  5. persists the assistant message and kicks off the async background
     workers (compaction + memory extraction) without blocking the reply.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator

from sqlalchemy import select

from chatapp.config import (
    RETRIEVAL_MAX_DISTANCE,
    RETRIEVAL_TOP_K,
    WORKING_CONTEXT_MESSAGE_LIMIT,
)
from chatapp.db import Conversation, Message, MessageRole, SessionLocal, UserProfile
from chatapp.db.models import next_seq, utcnow
from chatapp.llm import complete, complete_stream
from chatapp.schemas import PersistentProfile
from chatapp.vectorstore import VectorStore

DEFAULT_CONVERSATION_TITLE = "New chat"

_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Process-wide VectorStore (Chroma client + embedder are heavy to open)."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


# ---------------------------------------------------------------------------
# System-prompt construction (the priority hierarchy lives here)
# ---------------------------------------------------------------------------

BASE_INSTRUCTIONS = (
    "You are a helpful assistant with layered long-term memory. Context "
    "sections below are ordered by priority; when they conflict, earlier "
    "sections win. Use the memory naturally - never recite these sections "
    "back to the user."
)


def build_system_prompt(
    profile: PersistentProfile | None,
    file_hits: list[dict[str, Any]],
    history_hits: list[dict[str, Any]],
) -> str:
    sections: list[str] = [BASE_INSTRUCTIONS]

    # -- Priority 1 · Layer 2: Persistent Memory ---------------------------
    if profile is not None:
        lines = ["## User profile (highest priority)"]
        ident = profile.identity
        id_bits = [b for b in (ident.name, ident.role, ident.organization) if b]
        if id_bits:
            lines.append(f"Identity: {', '.join(id_bits)}")
        if ident.timezone:
            lines.append(f"Timezone: {ident.timezone}")
        prefs = profile.preferences
        lines.append(
            f"Preferences: tone={prefs.tone}, language={prefs.response_language}, "
            f"expertise={prefs.expertise_level}"
        )
        for key, value in prefs.custom.items():
            lines.append(f"Preference ({key}): {value}")
        if profile.facts:
            lines.append("Known facts about the user:")
            lines.extend(f"- {f.fact}" for f in profile.facts)
        sections.append("\n".join(lines))

    # -- Priority 2 · Layer 4: Indexed Files -------------------------------
    if file_hits:
        lines = ["## Relevant excerpts from the user's uploaded files"]
        for hit in file_hits:
            meta = hit["metadata"]
            lines.append(
                f"[{meta['filename']} · chunk {meta['chunk_index'] + 1}/"
                f"{meta['total_chunks']}]\n{hit['text']}"
            )
        sections.append("\n\n".join(lines))

    # -- Priority 3 · Layer 3: Compacted History ---------------------------
    if history_hits:
        lines = ["## Summaries of relevant past conversation segments"]
        lines.extend(hit["text"] for hit in history_hits)
        sections.append("\n\n".join(lines))

    # -- Priority 4 · Layer 1 is delivered as the chat turns themselves ----
    sections.append(
        "## Working context\nThe most recent messages of the current "
        "conversation follow as normal chat turns."
    )
    return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Turn pipeline: prepare (layers in) -> completion -> finalize (persist out)
# ---------------------------------------------------------------------------

@dataclass
class _TurnContext:
    """Everything gathered before the LLM call, shared by both entry points."""

    conversation_id: uuid.UUID
    user_id: uuid.UUID
    user_input: str
    chat_turns: list[dict[str, str]]
    system_prompt: str
    history_hits: list[dict[str, Any]]
    file_hits: list[dict[str, Any]]


def _prepare_turn(user_input: str, conversation_id: uuid.UUID) -> _TurnContext:
    """Persist the user turn and gather all four layers into a prompt."""
    store = get_vector_store()

    # ---- Persist the user turn, load Layers 1 & 2 (relational) ----------
    with SessionLocal() as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            raise ValueError(f"Unknown conversation: {conversation_id}")
        user_id = conversation.user_id

        session.add(
            Message(
                conversation_id=conversation_id,
                seq=next_seq(session, conversation_id),
                role=MessageRole.user,
                content=user_input,
            )
        )
        conversation.updated_at = utcnow()
        # First message names the thread (the sidebar shows this title).
        if conversation.title == DEFAULT_CONVERSATION_TITLE:
            first_line = user_input.strip().splitlines()[0]
            conversation.title = (
                first_line[:57] + "..." if len(first_line) > 60 else first_line
            )
        session.commit()

        # Layer 1: last N messages (now including the new user turn).
        recent = session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.seq.desc())
            .limit(WORKING_CONTEXT_MESSAGE_LIMIT)
        ).scalars().all()
        recent = list(reversed(recent))
        chat_turns = [
            {"role": m.role.value, "content": m.content}
            for m in recent
            if m.role in (MessageRole.user, MessageRole.assistant)
        ]

        # Layer 2: persistent profile.
        profile_row = session.get(UserProfile, user_id)
        profile = (
            PersistentProfile.model_validate(profile_row.data)
            if profile_row is not None
            else None
        )

    # ---- Layers 3 & 4 (vector retrieval, keyed on the user's input) -----
    def _relevant(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [h for h in hits if h["distance"] <= RETRIEVAL_MAX_DISTANCE]

    history_hits = _relevant(
        store.search_history(
            user_id=str(user_id), query=user_input, top_k=RETRIEVAL_TOP_K
        )
    )
    file_hits = _relevant(
        store.search_files(
            user_id=str(user_id), query=user_input, top_k=RETRIEVAL_TOP_K
        )
    )

    return _TurnContext(
        conversation_id=conversation_id,
        user_id=user_id,
        user_input=user_input,
        chat_turns=chat_turns,
        system_prompt=build_system_prompt(profile, file_hits, history_hits),
        history_hits=history_hits,
        file_hits=file_hits,
    )


async def _finalize_turn(
    ctx: _TurnContext,
    assistant_text: str,
    *,
    run_hooks_inline: bool,
) -> dict[str, Any]:
    """Persist the assistant turn and schedule the memory-maintenance hooks."""
    from chatapp.workers import run_compaction, run_memory_extraction

    with SessionLocal() as session:
        assistant_msg = Message(
            conversation_id=ctx.conversation_id,
            seq=next_seq(session, ctx.conversation_id),
            role=MessageRole.assistant,
            content=assistant_text,
            meta={"system_prompt_chars": len(ctx.system_prompt)},
        )
        session.add(assistant_msg)
        conversation = session.get(Conversation, ctx.conversation_id)
        conversation.updated_at = utcnow()
        session.commit()
        assistant_message_id = assistant_msg.id

    hooks = (
        run_compaction(ctx.conversation_id),
        run_memory_extraction(
            user_id=ctx.user_id,
            conversation_id=ctx.conversation_id,
            user_text=ctx.user_input,
            assistant_text=assistant_text,
        ),
    )
    if run_hooks_inline:
        hook_results = list(await asyncio.gather(*hooks))
    else:
        for coro in hooks:
            task = asyncio.create_task(coro)
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)
        hook_results = None

    return {
        "conversation_id": str(ctx.conversation_id),
        "assistant_message_id": str(assistant_message_id),
        "reply": assistant_text,
        "retrieval": {
            "history_hits": ctx.history_hits,
            "file_hits": ctx.file_hits,
        },
        "hook_results": hook_results,
    }


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

async def generate_chat_response(
    user_input: str,
    conversation_id: uuid.UUID,
    *,
    run_hooks_inline: bool = False,
) -> dict[str, Any]:
    """Answer ``user_input`` inside a conversation, using all four layers.

    ``run_hooks_inline=True`` awaits the background workers before returning
    (useful in tests/demos); the default schedules them as fire-and-forget
    tasks so the user gets the reply immediately.
    """
    ctx = _prepare_turn(user_input, conversation_id)
    assistant_text = await complete(ctx.system_prompt, ctx.chat_turns)
    return await _finalize_turn(
        ctx, assistant_text, run_hooks_inline=run_hooks_inline
    )


async def stream_chat_response(
    user_input: str,
    conversation_id: uuid.UUID,
) -> AsyncIterator[dict[str, Any]]:
    """Same pipeline as ``generate_chat_response`` but yields UI events.

    Event shapes (each is one SSE ``data:`` frame in the API layer):
      {"type": "start", "conversation_id", "retrieval": {counts}}
      {"type": "token", "text": "<delta>"}          (repeated)
      {"type": "done",  "conversation_id", "assistant_message_id", "reply"}
    """
    ctx = _prepare_turn(user_input, conversation_id)
    yield {
        "type": "start",
        "conversation_id": str(conversation_id),
        "retrieval": {
            "history_hits": len(ctx.history_hits),
            "file_hits": len(ctx.file_hits),
        },
    }

    parts: list[str] = []
    async for delta in complete_stream(ctx.system_prompt, ctx.chat_turns):
        parts.append(delta)
        yield {"type": "token", "text": delta}

    result = await _finalize_turn(ctx, "".join(parts), run_hooks_inline=False)
    yield {
        "type": "done",
        "conversation_id": result["conversation_id"],
        "assistant_message_id": result["assistant_message_id"],
        "reply": result["reply"],
    }


# Keep strong references to fire-and-forget tasks so they aren't GC'd mid-run.
_background_tasks: set[asyncio.Task] = set()
