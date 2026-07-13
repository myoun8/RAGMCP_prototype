import { useChatStore } from "../store/chatStore";
import { useUserStore } from "../store/userStore";

/**
 * Thread manager: new-chat button, the list of past conversations (newest
 * activity first, active one highlighted), and a footer showing the global
 * Layer-2 profile state — rendered from userStore, never from chat state.
 */
export default function Sidebar() {
  const user = useUserStore((s) => s.user);
  const profile = useUserStore((s) => s.profile);

  const conversations = useChatStore((s) => s.conversations);
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const switchConversation = useChatStore((s) => s.switchConversation);
  const createConversation = useChatStore((s) => s.createConversation);
  const deleteConversation = useChatStore((s) => s.deleteConversation);

  const identity = profile?.data?.identity;
  const facts = profile?.data?.facts ?? [];

  return (
    <aside className="sidebar">
      <button
        className="new-chat"
        onClick={() => createConversation(user.user_id)}
      >
        + New chat
      </button>

      <nav className="thread-list">
        {conversations.length === 0 && (
          <p className="thread-empty">No conversations yet.</p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            className={
              "thread" + (c.id === activeConversationId ? " thread-active" : "")
            }
            onClick={() => switchConversation(c.id)}
          >
            <span className="thread-title" title={c.title}>
              {c.title}
            </span>
            <button
              className="thread-delete"
              title="Delete thread"
              onClick={(e) => {
                e.stopPropagation();
                deleteConversation(c.id);
              }}
            >
              ×
            </button>
          </div>
        ))}
      </nav>

      <footer className="profile-panel">
        <div className="profile-name">
          {identity?.name ?? user.display_name ?? user.email}
        </div>
        <div className="profile-meta">
          {identity?.role && <span>{identity.role} · </span>}
          Memory v{profile?.version ?? 0} · {facts.length} fact
          {facts.length === 1 ? "" : "s"} learned
        </div>
        {facts.length > 0 && (
          <ul className="profile-facts">
            {facts.slice(-3).map((f, i) => (
              <li key={i} title={`${f.category} (${f.confidence})`}>
                {f.fact}
              </li>
            ))}
          </ul>
        )}
      </footer>
    </aside>
  );
}
