import { useEffect, useRef, useState } from "react";
import { useChatStore } from "../store/chatStore";

/**
 * The active thread: message history plus the composer. Renders exclusively
 * from chatStore's `messages` buffer, which is guaranteed to belong to
 * `activeConversationId` (cleared on every switch, streamed into in place).
 */
export default function ChatArea() {
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const messages = useChatStore((s) => s.messages);
  const isLoadingMessages = useChatStore((s) => s.isLoadingMessages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const error = useChatStore((s) => s.error);

  const scrollRef = useRef(null);

  // Keep the newest message in view while tokens stream in.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, isLoadingMessages]);

  if (!activeConversationId) {
    return (
      <main className="chat-area">
        <div className="chat-placeholder">
          Pick a thread or start a new chat.
        </div>
      </main>
    );
  }

  return (
    <main className="chat-area">
      <div className="message-scroll" ref={scrollRef}>
        {isLoadingMessages && <div className="chat-placeholder">Loading…</div>}
        {error && <div className="chat-error">{error}</div>}
        {!isLoadingMessages &&
          messages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => <MessageBubble key={m.id} message={m} />)}
        {!isLoadingMessages && messages.length === 0 && !error && (
          <div className="chat-placeholder">
            New thread — say something to begin.
          </div>
        )}
      </div>
      <Composer disabled={isStreaming || isLoadingMessages} />
    </main>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={"bubble-row " + (isUser ? "from-user" : "from-assistant")}>
      <div
        className={
          "bubble" +
          (message.streaming ? " bubble-streaming" : "") +
          (message.error ? " bubble-error" : "")
        }
      >
        {message.content}
        {message.streaming && <span className="cursor">▍</span>}
      </div>
    </div>
  );
}

function Composer({ disabled }) {
  const [draft, setDraft] = useState("");
  const sendMessage = useChatStore((s) => s.sendMessage);

  const send = () => {
    if (disabled || !draft.trim()) return;
    sendMessage(draft);
    setDraft("");
  };

  return (
    <div className="composer">
      <textarea
        value={draft}
        placeholder={disabled ? "Waiting for the model…" : "Message the assistant"}
        rows={1}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
          }
        }}
      />
      <button onClick={send} disabled={disabled || !draft.trim()}>
        Send
      </button>
    </div>
  );
}
