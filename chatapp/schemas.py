"""Pydantic v2 schemas.

Two jobs in Part 1:

1. Type the ``UserProfile.data`` JSONB document (Layer 2) so every write to
   persistent memory is validated before it hits the database.
2. Type the metadata attached to vector records (Layers 3 & 4). ChromaDB
   metadata values must be scalars (str/int/float/bool), so these models are
   deliberately flat; ``model_dump()`` output is passed straight to Chroma.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Layer 2 — Persistent Memory (shape of UserProfile.data)
# --------------------------------------------------------------------------

class ProfileIdentity(BaseModel):
    name: str | None = None
    role: str | None = None
    organization: str | None = None
    timezone: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ProfilePreferences(BaseModel):
    tone: str = "neutral"                 # e.g. "concise", "friendly"
    response_language: str = "en"
    expertise_level: str = "intermediate"  # calibrates explanations
    custom: dict[str, Any] = Field(default_factory=dict)


class ProfileFact(BaseModel):
    """One durable fact the assistant has learned about the user."""

    fact: str
    category: str = "general"             # e.g. "work", "project", "personal"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_conversation_id: str | None = None
    learned_at: datetime = Field(default_factory=_utcnow)


class PersistentProfile(BaseModel):
    """The full Layer-2 memory document stored in UserProfile.data."""

    identity: ProfileIdentity = Field(default_factory=ProfileIdentity)
    preferences: ProfilePreferences = Field(default_factory=ProfilePreferences)
    facts: list[ProfileFact] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Layer 3 — Compacted History (vector record metadata)
# --------------------------------------------------------------------------

class SummaryMetadata(BaseModel):
    """Metadata for one conversation-summary vector record."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    conversation_id: str
    seq_start: int          # first Message.seq covered by this summary
    seq_end: int            # last Message.seq covered by this summary
    message_count: int
    created_at: str         # ISO-8601 (Chroma metadata must be scalar)


# --------------------------------------------------------------------------
# Layer 4 — Indexed Files (vector record metadata)
# --------------------------------------------------------------------------

class FileChunkMetadata(BaseModel):
    """Metadata for one chunk of an uploaded file."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    file_id: str
    filename: str
    chunk_index: int
    total_chunks: int
    description: str = ""   # short human/LLM-written description of the file
    uploaded_at: str        # ISO-8601


# --------------------------------------------------------------------------
# API-facing read models (used by Part 2's FastAPI routes)
# --------------------------------------------------------------------------

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seq: int
    role: str
    content: str
    meta: dict[str, Any]
    created_at: datetime


class ConversationListItem(BaseModel):
    """Sidebar-sized view of a conversation — no messages attached."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    is_archived: bool
    compacted_through_seq: int
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = Field(default_factory=list)


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    data: PersistentProfile
    version: int
    updated_at: datetime
