"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowUp,
  BookOpen,
  Clipboard,
  FileText,
  LoaderCircle,
  MessageSquarePlus,
  ShieldCheck,
} from "lucide-react";
import { api } from "@/lib/workspace";
import { formatDatesInText } from "@/lib/dates";

/** API 계약만 화면에 전달한다. 대화는 이 컴포넌트의 세션 메모리에만 보관한다. */
type Citation = {
  doc_name: string;
  article: string;
  source_path: string;
  is_mock: boolean;
  quote: string;
};
type Answer = {
  answer: string;
  intent: string;
  citations: Citation[];
  claim_refs: { claim_id: string; issue_id: number | null }[];
  suggested_actions: { label: string; action: string }[];
  refused: boolean;
};
type Turn = { id: number; question: string; result?: Answer; error?: string };
type Conversation = { id: number; turns: Turn[]; claimId?: string };
const questions = [
  "김유정 고객 서류 왔는지 확인해보고 보완사항 있는지 검토해줘",
  "김유정 약제비 영수증에 종합비타민정 보상돼?",
  "수술확인서 보완 요청 문자 써줘",
  "이거 지급해도 돼?",
];

function quoteText(text: string) {
  return text
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/\*\*/g, "")
    .replace(/^\|[- :|]+\|$/gm, "")
    .replace(/\|/g, " · ")
    .trim();
}

export function ChatScreen() {
  const params = useSearchParams();
  const [conversations, setConversations] = useState<Conversation[]>([
    { id: 1, turns: [], claimId: params.get("claim") ?? undefined },
  ]);
  const [active, setActive] = useState(1),
    [input, setInput] = useState(""),
    [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<number | null>(null),
    [draft, setDraft] = useState<string | null>(null),
    [copied, setCopied] = useState(false);
  const scroll = useRef<HTMLDivElement>(null);
  const current = conversations.find((c) => c.id === active)!;
  const turns = current.turns;
  const focus = turns.find((t) => t.id === selected) ?? turns[turns.length - 1];
  const sources = focus?.result?.citations ?? [];
  const nextId = useRef(2);
  useEffect(() => {
    // 새 답변만 대화 영역 아래로 이동시킨다. 근거 패널이나 브라우저 전체는 움직이지 않는다.
    scroll.current?.scrollTo({
      top: scroll.current.scrollHeight,
      behavior: "smooth",
    });
  }, [turns.length, busy]);
  function update(id: number, patch: Partial<Turn>) {
    setConversations((list) =>
      list.map((c) =>
        c.id === active
          ? {
              ...c,
              turns: c.turns.map((t) => (t.id === id ? { ...t, ...patch } : t)),
            }
          : c,
      ),
    );
  }
  async function send(text: string, contextId?: string) {
    if (!text.trim() || busy) return;
    const id = nextId.current++;
    const history = turns
      .flatMap((t) => [
        { role: "user", content: t.question },
        ...(t.result ? [{ role: "assistant", content: t.result.answer }] : []),
      ])
      .slice(-24);
    const claimId = contextId ?? current.claimId;
    setConversations((list) =>
      list.map((c) =>
        c.id === active
          ? { ...c, claimId, turns: [...c.turns, { id, question: text }] }
          : c,
      ),
    );
    setDraft(null);
    setInput("");
    setBusy(true);
    setSelected(id);
    setCopied(false);
    try {
      const result = await api<Answer>("/chat", {
        method: "POST",
        body: JSON.stringify({
          message: text,
          claim_id: claimId ?? null,
          history,
        }),
      });
      update(id, { result });
      if (result.intent === "draft") setDraft(result.answer);
      // 이름 조회로 선택이 명확해진 경우에만 후속 질문의 청구 맥락을 유지한다.
      const ids = [...new Set(result.claim_refs.map((r) => r.claim_id))];
      if (ids.length === 1)
        setConversations((list) =>
          list.map((c) => (c.id === active ? { ...c, claimId: ids[0] } : c)),
        );
    } catch (error) {
      update(id, { error: (error as Error).message });
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="assistant-page">
      <div className="assistant-top">
        <Link href="/" className="back-home">
          <ArrowLeft size={16} />
          메인으로
        </Link>
        <span>업무 어시스턴트</span>
        <Link
          className="btn sm"
          href={
            current.claimId
              ? `/workspace/detail?claim=${current.claimId}`
              : "/workspace"
          }
        >
          워크스페이스로 이동
        </Link>
      </div>
      <div className="assistant-layout">
        <aside className="assistant-history" aria-label="대화 목록">
          <button
            className="btn"
            disabled={busy}
            onClick={() => {
              const id = nextId.current++;
              setConversations((list) => [
                { id, turns: [], claimId: params.get("claim") ?? undefined },
                ...list,
              ]);
              setActive(id);
              setSelected(null);
              setDraft(null);
            }}
          >
            <MessageSquarePlus size={17} />새 채팅
          </button>
          <p className="eyebrow">현재 세션</p>
          {conversations.map((c) => (
            <button
              key={c.id}
              disabled={busy}
              className={`conversation-item ${active === c.id ? "active" : ""}`}
              onClick={() => {
                setActive(c.id);
                setSelected(null);
                setDraft(null);
              }}
            >
              <strong>{c.turns[0]?.question ?? "새 대화"}</strong>
              <small>{c.turns.length}개 질문</small>
            </button>
          ))}
          <p className="assistant-session-note">
            대화는 현재 화면에만 보관돼요.
          </p>
        </aside>
        <section className="assistant-conversation" aria-label="업무 대화">
          <nav className="assistant-question-nav" aria-label="질문 바로가기">
            {turns.map((t, n) => (
              <button
                key={t.id}
                title={t.question}
                aria-label={`${n + 1}번 질문: ${t.question}`}
                onClick={() => {
                  document
                    .getElementById(`question-${t.id}`)
                    ?.scrollIntoView({ behavior: "smooth", block: "start" });
                  setSelected(t.id);
                }}
              />
            ))}
          </nav>
          <div className="assistant-scroll" ref={scroll}>
            {!turns.length && (
              <div className="assistant-welcome">
                <BookOpen size={30} />
                <p className="eyebrow">YOUR EVERYDAY WORK PARTNER</p>
                <h1>
                  근거를 찾고,
                  <br />
                  다음 업무를 이어가요.
                </h1>
                <p className="muted">
                  약관과 청구 서류를 함께 확인해 드릴게요.
                </p>
                <div className="assistant-suggestions">
                  {questions.map((q) => (
                    <button key={q} onClick={() => send(q)}>
                      {q}
                      <ArrowUp size={14} />
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div className="assistant-turns">
              {turns.map((t) => (
                <article
                  key={t.id}
                  id={`question-${t.id}`}
                  className="assistant-turn"
                >
                  <h2 className="assistant-user">{t.question}</h2>
                  {t.result && (
                    <div
                      className="assistant-answer"
                      data-testid={`answer-${t.id}`}
                    >
                      <div className="assistant-answer-label">
                        <ShieldCheck size={17} />
                        가온 AI
                        {t.result.refused && (
                          <span className="muted">판단 범위 안내</span>
                        )}
                      </div>
                      <p className="assistant-answer-text">
                        {formatDatesInText(t.result.answer)}
                      </p>
                      {t.result.citations.length > 0 && (
                        <div className="answer-citations">
                          {t.result.citations.map((c, n) => (
                            <button
                              key={n}
                              className="answer-source-card"
                              onClick={() => setSelected(t.id)}
                            >
                              <BookOpen size={14} />
                              <strong>
                                {c.doc_name} · {c.article}
                              </strong>
                              <small>
                                {c.is_mock ? "가상 문서" : "공개 표준약관"}
                              </small>
                              <blockquote>{quoteText(c.quote)}</blockquote>
                            </button>
                          ))}
                        </div>
                      )}
                      <div className="assistant-actions">
                        {t.result.claim_refs.map((r, n) => (
                          <Link
                            key={n}
                            className="text-link"
                            href={`/workspace/detail?claim=${encodeURIComponent(r.claim_id)}${r.issue_id !== null ? `&issue=${r.issue_id}#issue-${r.issue_id}` : ""}`}
                          >
                            <FileText size={14} />
                            {r.claim_id}
                            {r.issue_id !== null
                              ? ` · 이슈 ${r.issue_id}`
                              : " · 청구 상세"}
                          </Link>
                        ))}
                      </div>
                      {t.result.suggested_actions.map((a) => (
                        <button
                          key={a.action}
                          className="btn"
                          disabled={busy}
                          onClick={() => {
                            if (a.action.startsWith("draft_supplement:"))
                              send(
                                "누락 서류 보완 요청 문자 써줘",
                                a.action.slice("draft_supplement:".length),
                              );
                          }}
                        >
                          {a.label}
                        </button>
                      ))}
                    </div>
                  )}
                  {t.error && (
                    <p role="alert" className="bad">
                      {t.error}
                    </p>
                  )}
                </article>
              ))}
            </div>
            {busy && (
              <div role="status" className="assistant-loading">
                <LoaderCircle size={17} className="spin" />
                <span>
                  {/약|보상|규정/.test(turns[turns.length - 1]?.question ?? "")
                    ? "약관 찾는 중"
                    : "청구 건 확인 중"}
                </span>
              </div>
            )}
            {draft !== null && (
              <section className="assistant-draft">
                <h2>보완 요청 초안</h2>
                <p className="muted">
                  내용을 수정하고 확인한 뒤 사용해 주세요.
                </p>
                <textarea
                  aria-label="보완 요청 초안"
                  value={draft}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    setCopied(false);
                  }}
                />
                <button
                  className="btn sm"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(draft);
                      setCopied(true);
                    } catch {
                      setCopied(false);
                    }
                  }}
                >
                  <Clipboard size={14} />
                  {copied ? "복사했어요" : "문구 복사"}
                </button>
              </section>
            )}
          </div>
          <form
            className="assistant-composer"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            {current.claimId && (
              <p className="assistant-context">
                <FileText size={13} />
                {current.claimId} 청구를 확인하고 있어요.
              </p>
            )}
            <div>
              <textarea
                aria-label="메시지"
                placeholder="약관이나 업무 절차를 물어보세요"
                value={input}
                disabled={busy}
                rows={2}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    !e.shiftKey &&
                    !e.nativeEvent.isComposing
                  ) {
                    e.preventDefault();
                    send(input);
                  }
                }}
              />
              <button
                className="btn primary"
                type="submit"
                aria-label="보내기"
                disabled={busy || !input.trim()}
              >
                <ArrowUp size={18} />
              </button>
            </div>
            <p>
              근거를 바탕으로 안내해요. 지급 여부와 금액은 지급 심사 담당자가
              결정합니다.
            </p>
          </form>
        </section>
        <aside className="assistant-sources" aria-label="답변 근거">
          <h2>
            <BookOpen size={17} />
            답변 근거
          </h2>
          {!sources.length && (
            <p className="muted">
              답변에 사용한 문서와 조항을 여기서 확인할 수 있어요.
            </p>
          )}
          {sources.map((c, n) => (
            <section key={n} className="assistant-source">
              <small>
                {n + 1} · {c.is_mock ? "가상 문서" : "공개 표준약관"}
              </small>
              <h3>{c.doc_name}</h3>
              <strong>{c.article}</strong>
              <blockquote>{quoteText(c.quote)}</blockquote>
              <span>{c.source_path}</span>
            </section>
          ))}
        </aside>
      </div>
    </main>
  );
}
