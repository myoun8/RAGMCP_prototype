"""End-to-end demo of the Part-2 orchestration engine against live Llama 3.2.

Run:  python -m chatapp.demo_part2

Flow:
  1. Re-seed Part 1's example data (user, profile, conversation, vectors).
  2. Turn A — a question that should pull Layer 4 (file chunks) and
     Layer 3 (history summary) into the system prompt.
  3. Turn B — an exchange containing a durable fact; the memory-extraction
     worker should add it to the Layer 2 profile.
  4. Force the compaction worker with a tiny token budget and show the
     Layer 1 -> Layer 3 migration (messages deleted, watermark advanced,
     summary retrievable by semantic search).
"""

from __future__ import annotations

import asyncio
import json

from sqlalchemy import func, select

from chatapp.db import Conversation, Message, SessionLocal, UserProfile
from chatapp.orchestrator import generate_chat_response, get_vector_store
from chatapp.seed import seed_relational, seed_vectors
from chatapp.workers import run_compaction, run_memory_extraction


def _message_count(conversation_id) -> int:
    with SessionLocal() as session:
        return session.execute(
            select(func.count()).select_from(Message).where(
                Message.conversation_id == conversation_id
            )
        ).scalar_one()


async def main() -> None:
    print(">> Seeding Part 1 example data...")
    user_id, conversation_id = seed_relational()
    seed_vectors(user_id, conversation_id)

    # ---- Turn A: retrieval-heavy question --------------------------------
    print("\n>> Turn A: question that should hit Layers 2/3/4")
    result = await generate_chat_response(
        "Quick recap: where do we keep user preferences, and what marks how "
        "far compaction has progressed?",
        conversation_id,
        run_hooks_inline=True,
    )
    print(f"history hits used: {len(result['retrieval']['history_hits'])}, "
          f"file hits used: {len(result['retrieval']['file_hits'])}")
    print(f"assistant> {result['reply']}\n")

    # ---- Turn B: exchange containing a durable fact -----------------------
    print(">> Turn B: statement containing a durable fact")
    result = await generate_chat_response(
        "Good. By the way, I've switched our ingestion service to Rust, so "
        "future code examples for that service should be Rust.",
        conversation_id,
        run_hooks_inline=True,
    )
    print(f"assistant> {result['reply']}")
    compaction_result, learned = result["hook_results"]
    print(f"compaction (default 3000-token budget): {compaction_result}")
    print(f"facts learned by extraction worker: {learned}")

    with SessionLocal() as session:
        row = session.get(UserProfile, user_id)
        print(f"profile version now: {row.version}")
        print("profile facts now:")
        for fact in row.data["facts"]:
            print(f"  - [{fact['category']}] {fact['fact']} "
                  f"(confidence {fact['confidence']})")

    # ---- Forced compaction ------------------------------------------------
    before = _message_count(conversation_id)
    print(f"\n>> Forcing compaction (tiny budget). Messages before: {before}")
    stats = await run_compaction(conversation_id, token_limit=100, keep_recent=2)
    print(json.dumps(stats, indent=2))
    after = _message_count(conversation_id)
    with SessionLocal() as session:
        convo = session.get(Conversation, conversation_id)
        watermark = convo.compacted_through_seq
    print(f"messages after: {after}, compacted_through_seq: {watermark}")

    print("\n>> Semantic search over compacted history for 'Rust ingestion':")
    hits = get_vector_store().search_history(
        user_id=str(user_id), query="Rust ingestion service", top_k=1
    )
    for hit in hits:
        print(f"  [{hit['id']}] (distance {hit['distance']:.3f})\n  {hit['text']}")


if __name__ == "__main__":
    asyncio.run(main())
