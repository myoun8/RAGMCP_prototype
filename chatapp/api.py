"""Part 3 backend surface: FastAPI routes over the Part-2 engine.

Run:  uvicorn chatapp.api:app --reload      (or: python -m chatapp.api)

Routes:
  GET    /api/session                                get-or-create demo user
  GET    /api/users/{user_id}/profile                Layer 2 (global state)
  GET    /api/users/{user_id}/conversations          sidebar thread list
  POST   /api/users/{user_id}/conversations          new thread
  GET    /api/conversations/{id}/messages            Layer 1 for one thread
  DELETE /api/conversations/{id}                     remove a thread
  POST   /api/conversations/{id}/chat                SSE-streamed reply

The chat route streams Server-Sent Events; each ``data:`` frame is one JSON
event from ``orchestrator.stream_chat_response`` (start / token / done, plus
an ``error`` frame if the pipeline throws mid-stream — the HTTP status is
already sent by then, so errors must travel in-band).

If ``chatapp/frontend/dist`` exists (``npm run build``), it is served at ``/``
so the whole app runs from this one process; during development the Vite dev
server proxies ``/api`` here instead.
"""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select

from chatapp.db import (
    Conversation,
    Message,
    SessionLocal,
    User,
    UserProfile,
    init_db,
)
from chatapp.orchestrator import stream_chat_response
from chatapp.schemas import (
    ConversationListItem,
    MessageOut,
    PersistentProfile,
    UserProfileOut,
)

logger = logging.getLogger("chatapp.api")

DEFAULT_USER_EMAIL = "ada@example.com"
DEFAULT_USER_NAME = "Ada Lovelace"

FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="chatapp", version="0.3.0", lifespan=_lifespan)

# Dev-mode CORS for the Vite dev server (the /api proxy makes this mostly
# unnecessary, but it keeps direct cross-origin fetches working too).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request/response models local to the API layer
# ---------------------------------------------------------------------------

class SessionOut(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str | None


class ChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=32_000)


# ---------------------------------------------------------------------------
# Session / profile (Layer 2 — global state, never mixed into threads)
# ---------------------------------------------------------------------------

@app.get("/api/session", response_model=SessionOut)
def get_session() -> SessionOut:
    """Get-or-create the demo user.

    Stand-in for real authentication: Part 3's scope is the UI, so the
    backend pins a single local user. Swapping this for an auth dependency
    changes no other route (they all take explicit ids).
    """
    with SessionLocal() as session:
        user = session.execute(
            select(User).where(User.email == DEFAULT_USER_EMAIL)
        ).scalar_one_or_none()
        if user is None:
            user = User(email=DEFAULT_USER_EMAIL, display_name=DEFAULT_USER_NAME)
            session.add(user)
            session.flush()
            session.add(
                UserProfile(
                    user_id=user.id,
                    data=PersistentProfile().model_dump(mode="json"),
                )
            )
            session.commit()
        return SessionOut(
            user_id=user.id, email=user.email, display_name=user.display_name
        )


@app.get("/api/users/{user_id}/profile", response_model=UserProfileOut)
def get_profile(user_id: uuid.UUID) -> UserProfileOut:
    with SessionLocal() as session:
        row = session.get(UserProfile, user_id)
        if row is None:
            raise HTTPException(404, "No profile for that user")
        return UserProfileOut.model_validate(row)


# ---------------------------------------------------------------------------
# Conversations (threads)
# ---------------------------------------------------------------------------

@app.get(
    "/api/users/{user_id}/conversations",
    response_model=list[ConversationListItem],
)
def list_conversations(user_id: uuid.UUID) -> list[ConversationListItem]:
    with SessionLocal() as session:
        rows = session.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_archived.is_(False),
            )
            .order_by(Conversation.updated_at.desc())
        ).scalars().all()
        return [ConversationListItem.model_validate(r) for r in rows]


@app.post(
    "/api/users/{user_id}/conversations",
    response_model=ConversationListItem,
    status_code=201,
)
def create_conversation(user_id: uuid.UUID) -> ConversationListItem:
    with SessionLocal() as session:
        if session.get(User, user_id) is None:
            raise HTTPException(404, "Unknown user")
        convo = Conversation(user_id=user_id)
        session.add(convo)
        session.commit()
        return ConversationListItem.model_validate(convo)


@app.delete("/api/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: uuid.UUID) -> None:
    """Delete a thread (Layer 1). Its Layer-3 summaries are kept on purpose:
    they are the user's long-term memory, not part of the thread."""
    with SessionLocal() as session:
        convo = session.get(Conversation, conversation_id)
        if convo is None:
            raise HTTPException(404, "Unknown conversation")
        session.delete(convo)
        session.commit()


@app.get(
    "/api/conversations/{conversation_id}/messages",
    response_model=list[MessageOut],
)
def get_messages(conversation_id: uuid.UUID) -> list[MessageOut]:
    with SessionLocal() as session:
        if session.get(Conversation, conversation_id) is None:
            raise HTTPException(404, "Unknown conversation")
        rows = session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.seq)
        ).scalars().all()
        return [MessageOut.model_validate(r) for r in rows]


# ---------------------------------------------------------------------------
# Chat (SSE streaming over the Part-2 engine)
# ---------------------------------------------------------------------------

@app.post("/api/conversations/{conversation_id}/chat")
async def chat(conversation_id: uuid.UUID, body: ChatRequest) -> StreamingResponse:
    # Validate up front so a bad id is a clean 404, not an in-band error.
    with SessionLocal() as session:
        if session.get(Conversation, conversation_id) is None:
            raise HTTPException(404, "Unknown conversation")

    async def event_stream():
        try:
            async for event in stream_chat_response(body.content, conversation_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:  # status line already sent — report in-band
            logger.exception("Chat stream failed for %s", conversation_id)
            yield 'data: {"type": "error", "message": "The model call failed. Is Ollama running?"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # don't let nginx buffer the stream
        },
    )


# ---------------------------------------------------------------------------
# Built frontend (optional, production single-process serving)
# ---------------------------------------------------------------------------

if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="ui")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("chatapp.api:app", host="127.0.0.1", port=8001)
