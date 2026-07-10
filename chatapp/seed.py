"""Seed script: populates all four memory layers with realistic example data
and prints the resulting objects.

Run:  python -m chatapp.seed
"""

from __future__ import annotations

import json
import uuid

from chatapp.db import (
    Conversation,
    Message,
    MessageRole,
    SessionLocal,
    User,
    UserProfile,
    init_db,
)
from chatapp.db.models import next_seq
from chatapp.schemas import (
    ConversationOut,
    PersistentProfile,
    ProfileFact,
    ProfileIdentity,
    ProfilePreferences,
    UserProfileOut,
)
from chatapp.vectorstore import VectorStore


def seed_relational() -> tuple[uuid.UUID, uuid.UUID]:
    """Layers 1 & 2: user + validated profile document + one conversation."""
    init_db()
    with SessionLocal() as session:
        # Idempotency: wipe a previous seed run for this demo user.
        existing = session.query(User).filter_by(email="ada@example.com").first()
        if existing:
            session.delete(existing)
            session.commit()

        user = User(email="ada@example.com", display_name="Ada Lovelace")
        session.add(user)
        session.flush()  # assigns user.id

        # ---- Layer 2: Persistent Memory (validated before storage) ----
        profile_doc = PersistentProfile(
            identity=ProfileIdentity(
                name="Ada Lovelace",
                role="Backend engineer",
                organization="Analytical Engines Inc.",
                timezone="America/New_York",
            ),
            preferences=ProfilePreferences(
                tone="concise",
                response_language="en",
                expertise_level="expert",
                custom={"code_style": "type-annotated Python", "prefers_examples": True},
            ),
            facts=[
                ProfileFact(
                    fact="Is building a chat app with a 4-layer memory architecture.",
                    category="project",
                    confidence=1.0,
                ),
                ProfileFact(
                    fact="Deploys on PostgreSQL in production, SQLite locally.",
                    category="work",
                    confidence=0.9,
                ),
            ],
        )
        session.add(
            UserProfile(user_id=user.id, data=profile_doc.model_dump(mode="json"))
        )

        # ---- Layer 1: Working Context ----
        convo = Conversation(user_id=user.id, title="Designing the memory schema")
        session.add(convo)
        session.flush()

        turns = [
            (MessageRole.user, "How should I store long-term user memory in Postgres?"),
            (
                MessageRole.assistant,
                "Use a user_profiles table with a JSONB column holding a "
                "validated document: identity, preferences, and a list of "
                "facts with confidence scores.",
            ),
            (MessageRole.user, "And when a conversation gets too long for the context window?"),
            (
                MessageRole.assistant,
                "Compact it: summarize older message ranges into a vector "
                "collection and keep a compacted_through_seq watermark on the "
                "conversation row.",
            ),
        ]
        for role, content in turns:
            session.add(
                Message(
                    conversation_id=convo.id,
                    seq=next_seq(session, convo.id),
                    role=role,
                    content=content,
                    meta={"model": "claude-fable-5"} if role is MessageRole.assistant else {},
                )
            )
            session.flush()

        session.commit()
        return user.id, convo.id


def seed_vectors(user_id: uuid.UUID, conversation_id: uuid.UUID) -> VectorStore:
    """Layers 3 & 4: one conversation summary + one indexed file."""
    store = VectorStore()

    # ---- Layer 3: Compacted History ----
    store.upsert_summary(
        user_id=str(user_id),
        conversation_id=str(conversation_id),
        summary_text=(
            "User asked how to persist long-term user memory and handle "
            "context-window overflow. Agreed design: JSONB profile document "
            "for durable facts/preferences, plus summarizing old message "
            "ranges into a vector store with a per-conversation compaction "
            "watermark."
        ),
        seq_start=1,
        seq_end=4,
    )

    # ---- Layer 4: Indexed Files ----
    store.upsert_file_chunks(
        user_id=str(user_id),
        file_id=str(uuid.uuid4()),
        filename="memory_architecture_notes.md",
        description="Design notes for the 4-layer cognitive memory system.",
        chunks=[
            "Layer 1 (Working Context) stores raw chat logs relationally, "
            "ordered by a per-conversation sequence number.",
            "Layer 2 (Persistent Memory) is a JSONB profile document per user "
            "holding identity, preferences, and confidence-scored facts.",
            "Layers 3 and 4 are vector collections: compacted conversation "
            "summaries and uploaded-file chunks, both tenant-scoped by user_id.",
        ],
    )
    return store


def main() -> None:
    user_id, conversation_id = seed_relational()
    store = seed_vectors(user_id, conversation_id)

    # ---- Print fully populated example objects ----
    with SessionLocal() as session:
        convo = session.get(Conversation, conversation_id)
        profile = session.get(UserProfile, user_id)

        print("=== Example Conversation object (Layer 1) ===")
        print(ConversationOut.model_validate(convo).model_dump_json(indent=2))

        print("\n=== Example UserProfile object (Layer 2) ===")
        print(UserProfileOut.model_validate(profile).model_dump_json(indent=2))

    print("\n=== Layer 3 semantic search: 'how do we avoid context overflow?' ===")
    hits = store.search_history(
        user_id=str(user_id), query="how do we avoid context overflow?", top_k=1
    )
    print(json.dumps(hits, indent=2))

    print("\n=== Layer 4 semantic search: 'where are user preferences stored?' ===")
    hits = store.search_files(
        user_id=str(user_id), query="where are user preferences stored?", top_k=1
    )
    print(json.dumps(hits, indent=2))


if __name__ == "__main__":
    main()
