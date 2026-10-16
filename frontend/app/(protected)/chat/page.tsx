import { Suspense } from "react";
import { ChatScreen } from "@/components/chat-screen";

/** URL 청구 맥락은 클라이언트에서 읽고, 인증은 protected layout이 담당한다. */
export default function ChatPage() {
  return (
    <Suspense fallback={<p>업무 어시스턴트를 열고 있어요.</p>}>
      <ChatScreen initialTime={new Date().toISOString()} />
    </Suspense>
  );
}
