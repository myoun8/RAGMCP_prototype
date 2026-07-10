"""LLM access layer.

One async client (official ``openai`` SDK) pointed at Ollama's
OpenAI-compatible endpoint serving Llama 3.2. Because the wire format is
OpenAI-standard, swapping to a hosted provider is a config change
(CHATAPP_LLM_BASE_URL / CHATAPP_LLM_API_KEY / CHATAPP_CHAT_MODEL), not a
code change.

Three entry points:
  complete()        — plain chat completion (the live response path).
  complete_stream() — same call as an async token generator (SSE path).
  complete_json()   — completion constrained to a JSON object, parsed
                      defensively (used by the background workers).
"""

from __future__ import annotations

import json
import re
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from chatapp.config import CHAT_MODEL, LLM_API_KEY, LLM_BASE_URL

client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)


async def complete(
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    model: str = CHAT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Run a chat completion and return the assistant text."""
    response = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    return response.choices[0].message.content or ""


async def complete_stream(
    system_prompt: str,
    messages: list[dict[str, str]],
    *,
    model: str = CHAT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> AsyncIterator[str]:
    """Run a chat completion and yield the assistant text delta by delta."""
    stream = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def complete_json(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = CHAT_MODEL,
    max_tokens: int = 1024,
) -> dict[str, Any] | None:
    """Completion that must yield a JSON object; returns None if unparseable.

    Uses Ollama's JSON mode (response_format json_object) plus defensive
    parsing — small local models occasionally wrap JSON in code fences or
    prose even when asked not to.
    """
    response = await client.chat.completions.create(
        model=model,
        temperature=0.0,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content or ""
    return _parse_json_object(raw)


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    # Strip a ```json ... ``` fence if present.
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Last resort: first {...} span in the output.
        span = re.search(r"\{.*\}", text, re.DOTALL)
        if not span:
            return None
        try:
            parsed = json.loads(span.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (~4 chars/token for English).

    Good enough to trigger compaction; swap in a real tokenizer if the
    budget needs to be exact.
    """
    return max(1, len(text) // 4)
