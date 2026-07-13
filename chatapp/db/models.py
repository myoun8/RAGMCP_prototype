"""ORM models for memory Layers 1 & 2.

Layer 1 — Working Context:   Conversation, Message (raw chat log).
Layer 2 — Persistent Memory: UserProfile (JSONB document of durable facts).

The JSON columns are declared as generic JSON with a JSONB variant, so the
same models run on PostgreSQL (JSONB, indexable with GIN) and on the SQLite
dev fallback.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from sqlalchemy.types import JSON

from chatapp.db.base import Base

# JSONB on Postgres, plain JSON elsewhere.
JSONDocument = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    """Layer 2 — Persistent Memory.

    One row per user. ``data`` holds the whole memory document (identity,
    preferences, accumulated facts); its shape is validated at the
    application boundary by ``chatapp.schemas.PersistentProfile``.
    ``version`` increments on every memory write so concurrent memory-update
    jobs can do optimistic locking instead of clobbering each other.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    data: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONDocument), default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped[User] = relationship(back_populates="profile")


class Conversation(Base):
    """Layer 1 — Working Context (thread container)."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), default="New chat")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    # Compaction watermark: highest Message.seq already folded into a
    # compacted-history summary (Layer 3). 0 = nothing compacted yet.
    compacted_through_seq: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.seq",
    )

    __table_args__ = (
        # Thread-list query: "my conversations, newest activity first".
        Index("ix_conversations_user_updated", "user_id", "updated_at"),
    )


class MessageRole(str, enum.Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class Message(Base):
    """Layer 1 — Working Context (raw chat log)."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    # Monotonic per-conversation ordinal. Ordering by seq is unambiguous
    # where created_at can collide at millisecond resolution.
    seq: Mapped[int] = mapped_column(Integer)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, native_enum=False, length=20)
    )
    content: Mapped[str] = mapped_column(Text)
    # Free-form per-message extras: model name, tool-call payloads,
    # token_count, attachment file_ids, etc.
    meta: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONDocument), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    __table_args__ = (
        UniqueConstraint("conversation_id", "seq", name="uq_messages_conversation_seq"),
    )


def next_seq(session: Session, conversation_id: uuid.UUID) -> int:
    """Next message ordinal for a conversation.

    Fine for a single app process; under multi-writer concurrency the unique
    constraint on (conversation_id, seq) turns a race into a retryable
    IntegrityError rather than silent misordering.
    """
    current = session.execute(
        select(func.coalesce(func.max(Message.seq), 0)).where(
            Message.conversation_id == conversation_id
        )
    ).scalar_one()
    return current + 1
