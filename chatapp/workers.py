"""Async background memory-maintenance workers.

run_compaction        — Layer 1 -> Layer 3: when a thread's token footprint
                        exceeds the budget, summarize the oldest messages
                        into the compacted_history vector collection, then
                        delete them from the relational log.
run_memory_extraction — Layer 1 -> Layer 2: after each exchange, mine the
                        new turns for durable user facts and merge them into
                        the persistent profile (optimistically locked).

Both are safe to run fire-and-forget: they catch nothing on purpose (the
orchestrator's task wrapper logs failures) but every DB write is a single
transaction, and the compaction summary is written to the vector store
*before* any Layer-1 rows are deleted, so a crash can duplicate a summary
(idempotent upsert) but never lose history.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import delete, select, update

from chatapp.config import (
    COMPACTION_KEEP_RECENT,
    COMPACTION_TOKEN_LIMIT,
    UTILITY_MODEL,
)
from chatapp.db import Conversation, Message, SessionLocal, UserProfile
from chatapp.llm import complete, complete_json, estimate_tokens
from chatapp.schemas import PersistentProfile, ProfileFact

logger = logging.getLogger("chatapp.workers")


# ---------------------------------------------------------------------------
# Compaction worker (Layer 1 -> Layer 3)
# ---------------------------------------------------------------------------

SUMMARIZER_SYSTEM = (
    "You compress chat transcripts into dense memory summaries. Write a "
    "single paragraph (max ~150 words) capturing: what the user wanted, "
    "key facts stated, decisions made, and any unresolved threads. Write in "
    "third person ('the user asked...'). Output only the summary."
)


async def run_compaction(
    conversation_id: uuid.UUID,
    *,
    token_limit: int = COMPACTION_TOKEN_LIMIT,
    keep_recent: int = COMPACTION_KEEP_RECENT,
) -> dict[str, Any] | None:
    """Compact a conversation if it exceeds ``token_limit`` estimated tokens.

    Returns a stats dict when compaction ran, else None.
    """
    from chatapp.orchestrator import get_vector_store

    with SessionLocal() as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            return None
        messages = session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.seq)
        ).scalars().all()

        total_tokens = sum(estimate_tokens(m.content) for m in messages)
        if total_tokens <= token_limit or len(messages) <= keep_recent:
            return None

        to_compact = messages[:-keep_recent]
        transcript = "\n".join(f"{m.role.value}: {m.content}" for m in to_compact)
        seq_start, seq_end = to_compact[0].seq, to_compact[-1].seq
        user_id = conversation.user_id

    # Cheap LLM call — outside any open session/transaction.
    summary = await complete(
        SUMMARIZER_SYSTEM,
        [{"role": "user", "content": f"Transcript:\n\n{transcript}"}],
        model=UTILITY_MODEL,
        temperature=0.0,
        max_tokens=300,
    )
    summary = summary.strip()
    if not summary:
        logger.warning("Compaction summary came back empty; skipping.")
        return None

    # Write Layer 3 first, then delete from Layer 1 — never lose history.
    store = get_vector_store()
    record_id = store.upsert_summary(
        user_id=str(user_id),
        conversation_id=str(conversation_id),
        summary_text=summary,
        seq_start=seq_start,
        seq_end=seq_end,
    )

    with SessionLocal() as session:
        session.execute(
            delete(Message).where(
                Message.conversation_id == conversation_id,
                Message.seq <= seq_end,
            )
        )
        session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(compacted_through_seq=seq_end)
        )
        session.commit()

    result = {
        "compacted_messages": len(to_compact),
        "seq_range": [seq_start, seq_end],
        "estimated_tokens_before": total_tokens,
        "summary_record_id": record_id,
        "summary": summary,
    }
    logger.info("Compacted conversation %s: %s", conversation_id, result)
    return result


# ---------------------------------------------------------------------------
# Memory-extraction worker (Layer 1 -> Layer 2)
# ---------------------------------------------------------------------------

EXTRACTOR_SYSTEM = (
    "You mine chat exchanges for durable facts about THE USER AS A PERSON "
    "that would still matter in future, unrelated conversations: their "
    "identity, job, long-term preferences, constraints.\n"
    "Do NOT extract: knowledge about the topic being discussed, technical "
    "explanations, design decisions, small talk, one-off requests, or "
    "anything the assistant said.\n"
    'Respond with a JSON object: {"facts": [{"fact": "...", '
    '"category": "...", "confidence": 0.0-1.0}]} where category is exactly '
    "one word chosen from: work, project, personal, preference, general.\n"
    'Most exchanges contain NO durable facts - then return {"facts": []}.'
)

_FACT_CATEGORIES = {"work", "project", "personal", "preference", "general"}


async def run_memory_extraction(
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user_text: str,
    assistant_text: str,
) -> list[str]:
    """Extract permanent user facts from the latest exchange into Layer 2.

    Returns the list of newly added fact strings (often empty).
    """
    exchange = f"user: {user_text}\nassistant: {assistant_text}"
    parsed = await complete_json(EXTRACTOR_SYSTEM, exchange, model=UTILITY_MODEL)
    if not parsed:
        return []

    candidates: list[ProfileFact] = []
    for item in parsed.get("facts", []):
        if not isinstance(item, dict) or not str(item.get("fact", "")).strip():
            continue
        try:
            confidence = min(1.0, max(0.0, float(item.get("confidence", 0.8))))
        except (TypeError, ValueError):
            confidence = 0.8
        category = str(item.get("category", "general")).strip().lower()
        if category not in _FACT_CATEGORIES:
            category = "general"
        candidates.append(
            ProfileFact(
                fact=str(item["fact"]).strip(),
                category=category,
                confidence=confidence,
                source_conversation_id=str(conversation_id),
            )
        )
    if not candidates:
        return []

    with SessionLocal() as session:
        row = session.get(UserProfile, user_id)
        if row is None:
            row = UserProfile(user_id=user_id, data=PersistentProfile().model_dump(mode="json"))
            session.add(row)
            session.flush()

        profile = PersistentProfile.model_validate(row.data)
        known = {f.fact.strip().lower() for f in profile.facts}
        added = [c for c in candidates if c.fact.strip().lower() not in known]
        if not added:
            return []
        profile.facts.extend(added)

        # Optimistic lock: only write if nobody bumped the version meanwhile.
        current_version = row.version
        rows_hit = session.execute(
            update(UserProfile)
            .where(
                UserProfile.user_id == user_id,
                UserProfile.version == current_version,
            )
            .values(data=profile.model_dump(mode="json"), version=current_version + 1)
        ).rowcount
        if rows_hit == 0:
            session.rollback()
            logger.warning(
                "Profile version conflict for user %s; dropping %d facts "
                "(will be re-learned).", user_id, len(added)
            )
            return []
        session.commit()

    facts = [c.fact for c in added]
    logger.info("Learned %d new fact(s) for user %s: %s", len(facts), user_id, facts)
    return facts
