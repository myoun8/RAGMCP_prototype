/**
 * Chat state: the thread list, the active conversation id, and the message
 * buffer for THAT THREAD ONLY.
 *
 * Isolation contract: `messages` always belongs to `activeConversationId`.
 * `switchConversation` clears the buffer synchronously, then loads the new
 * thread fresh from the backend; a monotonically increasing `loadToken`
 * discards any fetch that resolves after the user has already switched again,
 * and tokens from a stream left running in a background thread are dropped
 * (the backend persists the full reply, so switching back re-fetches it).
 */

import { create } from "zustand";
import { api, streamChat } from "../api/client";
import { useUserStore } from "./userStore";

let localId = 0;
const nextLocalId = (prefix) => `local-${prefix}-${++localId}`;

export const useChatStore = create((set, get) => ({
  conversations: [],          // sidebar list, newest activity first
  activeConversationId: null,
  messages: [],               // buffer for the active thread ONLY
  isLoadingMessages: false,
  isStreaming: false,
  error: null,
  loadToken: 0,               // stale-fetch guard for fast thread switching

  // ---- Thread list -------------------------------------------------------

  loadConversations: async (userId) => {
    const conversations = await api.listConversations(userId);
    set({ conversations });
  },

  createConversation: async (userId) => {
    const convo = await api.createConversation(userId);
    set((s) => ({ conversations: [convo, ...s.conversations] }));
    await get().switchConversation(convo.id);
    return convo;
  },

  deleteConversation: async (conversationId) => {
    await api.deleteConversation(conversationId);
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== conversationId),
    }));
    if (get().activeConversationId === conversationId) {
      set({ activeConversationId: null, messages: [], isLoadingMessages: false });
    }
  },

  // ---- Switching (the isolation-critical action) --------------------------

  switchConversation: async (conversationId) => {
    if (get().activeConversationId === conversationId) return;
    const token = get().loadToken + 1;
    // Clear the buffer BEFORE fetching — the old thread's messages must
    // never be visible under the new thread's title.
    set({
      activeConversationId: conversationId,
      messages: [],
      isLoadingMessages: true,
      error: null,
      loadToken: token,
    });
    try {
      const messages = await api.getMessages(conversationId);
      if (get().loadToken !== token) return; // user switched again — stale
      set({ messages, isLoadingMessages: false });
    } catch (err) {
      if (get().loadToken !== token) return;
      set({ isLoadingMessages: false, error: String(err) });
    }
  },

  // ---- Message buffer ------------------------------------------------------

  /** Append a message to the buffer iff it belongs to the active thread. */
  addMessage: (conversationId, message) => {
    if (get().activeConversationId !== conversationId) return;
    set((s) => ({ messages: [...s.messages, message] }));
  },

  // ---- Sending + streaming -------------------------------------------------

  sendMessage: async (content) => {
    const conversationId = get().activeConversationId;
    const text = content.trim();
    if (!conversationId || !text || get().isStreaming) return;

    // Optimistic user turn + empty assistant placeholder the stream fills in.
    get().addMessage(conversationId, {
      id: nextLocalId("user"),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    });
    const placeholderId = nextLocalId("assistant");
    get().addMessage(conversationId, {
      id: placeholderId,
      role: "assistant",
      content: "",
      streaming: true,
      created_at: new Date().toISOString(),
    });
    set({ isStreaming: true, error: null });

    // All stream callbacks funnel through this guard: if the user switched
    // threads mid-stream, updates are dropped (the reply is still persisted
    // server-side and appears when they switch back).
    const patchPlaceholder = (patch) => {
      if (get().activeConversationId !== conversationId) return;
      set((s) => ({
        messages: s.messages.map((m) =>
          m.id === placeholderId
            ? { ...m, ...patch, content: patch.content ?? m.content }
            : m
        ),
      }));
    };

    try {
      await streamChat(conversationId, text, {
        onToken: (delta) => {
          if (get().activeConversationId !== conversationId) return;
          set((s) => ({
            messages: s.messages.map((m) =>
              m.id === placeholderId ? { ...m, content: m.content + delta } : m
            ),
          }));
        },
        onDone: (event) =>
          patchPlaceholder({
            id: event.assistant_message_id,
            content: event.reply,
            streaming: false,
          }),
        onError: (err) =>
          patchPlaceholder({
            streaming: false,
            error: true,
            content: `⚠ ${err.message}`,
          }),
      });
    } finally {
      set({ isStreaming: false });
      // The turn changed server-side state beyond this thread: the sidebar
      // ordering/title (updated_at, auto-title) and possibly the Layer-2
      // profile (memory-extraction worker). Refresh both.
      const user = useUserStore.getState().user;
      if (user) {
        get().loadConversations(user.user_id).catch(() => {});
        useUserStore.getState().refreshProfile();
      }
    }
  },
}));
