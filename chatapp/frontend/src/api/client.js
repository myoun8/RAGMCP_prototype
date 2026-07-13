/**
 * API fetch client.
 *
 * Plain fetch wrappers for the REST routes, plus `streamChat`, which POSTs to
 * the SSE chat endpoint and parses the event stream incrementally so tokens
 * can be rendered the moment they arrive.
 *
 * BASE is empty: in dev the Vite proxy forwards /api to FastAPI; in prod the
 * built bundle is served by FastAPI itself, so requests are same-origin.
 */

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function http(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${options.method ?? "GET"} ${path} -> ${res.status} ${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  getSession: () => http("/api/session"),
  getProfile: (userId) => http(`/api/users/${userId}/profile`),
  listConversations: (userId) => http(`/api/users/${userId}/conversations`),
  createConversation: (userId) =>
    http(`/api/users/${userId}/conversations`, { method: "POST" }),
  deleteConversation: (conversationId) =>
    http(`/api/conversations/${conversationId}`, { method: "DELETE" }),
  getMessages: (conversationId) =>
    http(`/api/conversations/${conversationId}/messages`),
};

/**
 * Stream one chat turn. Resolves when the stream closes.
 *
 * handlers: { onStart(event), onToken(text), onDone(event), onError(error) }
 */
export async function streamChat(conversationId, content, handlers = {}) {
  const { onStart, onToken, onDone, onError, signal } = handlers;

  let res;
  try {
    res = await fetch(`${BASE}/api/conversations/${conversationId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
      signal,
    });
  } catch (err) {
    onError?.(err);
    return;
  }
  if (!res.ok || !res.body) {
    onError?.(new Error(`chat request failed (${res.status})`));
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (event) => {
    if (event.type === "start") onStart?.(event);
    else if (event.type === "token") onToken?.(event.text);
    else if (event.type === "done") onDone?.(event);
    else if (event.type === "error") onError?.(new Error(event.message));
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by a blank line; each data: line is JSON.
      let sep;
      while ((sep = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        for (const line of frame.split("\n")) {
          if (line.startsWith("data:")) dispatch(JSON.parse(line.slice(5)));
        }
      }
    }
  } catch (err) {
    onError?.(err);
  }
}
