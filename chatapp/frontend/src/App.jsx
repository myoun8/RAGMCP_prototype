import { useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import { useUserStore } from "./store/userStore";
import { useChatStore } from "./store/chatStore";

export default function App() {
  const user = useUserStore((s) => s.user);
  const bootError = useUserStore((s) => s.bootError);
  const bootstrap = useUserStore((s) => s.bootstrap);
  const loadConversations = useChatStore((s) => s.loadConversations);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    if (user) loadConversations(user.user_id);
  }, [user, loadConversations]);

  if (bootError) {
    return (
      <div className="boot-screen">
        <p>Could not reach the backend.</p>
        <p className="boot-detail">
          Start it with <code>uvicorn chatapp.api:app --port 8001</code>
        </p>
      </div>
    );
  }
  if (!user) return <div className="boot-screen">Connecting…</div>;

  return (
    <div className="app">
      <Sidebar />
      <ChatArea />
    </div>
  );
}
