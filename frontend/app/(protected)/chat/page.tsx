import Link from "next/link";
import { ArrowLeft, MessageSquareText } from "lucide-react";

export default function ChatPage() {
  return (
    <main id="main" className="chat-placeholder">
      <Link className="back-home" href="/">
        <ArrowLeft size={16} />
        메인으로
      </Link>
      <section className="empty-panel">
        <MessageSquareText
          size={40}
          strokeWidth={1.3}
          className="text-accent-strong"
        />
        <h1>업무 어시스턴트</h1>
        <p className="muted">
          약관과 업무 기준을 함께 찾아볼 대화 공간을 준비하고 있어요.
        </p>
        <Link href="/workspace" className="btn">
          서류 검토 워크스페이스로
        </Link>
      </section>
    </main>
  );
}
