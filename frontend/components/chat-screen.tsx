"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  Plus,
  ArrowUp,
  ArrowLeft,
  BookOpen,
  Clipboard,
  FileText,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";
import { conversationDate } from "@/lib/chat-history";
import { useTyping } from "@/lib/use-typing";
import { api, Claim, ClaimList } from "@/lib/workspace";
import { formatDatesInText } from "@/lib/dates";

/** API 계약만 화면에 전달한다. 대화는 이 컴포넌트의 세션 메모리에만 보관한다. */
type Citation = {
  source_kind?: string;
  coverage_section?: string;
  doc_name: string;
  article: string;
  source_path: string;
  is_mock: boolean;
  quote: string;
  display_quote?: string | null;
};
// 보장종목이 같아야 같은 조 번호를 인용할 수 있다. 원래 주소는 API 그대로 보존한다.
function citationAddress(c: Citation): string {
  const coverage = c.coverage_section
    ?.replace("질병비급여", "질병 비급여")
    .replace("상해비급여", "상해 비급여");
  const rider = c.source_path.includes("rider2_") ? "특약2 " : "";
  return `${rider}${coverage ? coverage + " " : ""}${c.article}`;
}
function citationKind(c: Citation): string {
  const kind =
    c.source_kind ?? (/\/(10|11)_/.test(c.source_path) ? "업무 기준" : "약관");
  return `${kind}${c.is_mock ? " · 가상 문서" : " · 공개 문서"}`;
}
export type Answer = {
  answer: string;
  draft_text?: string | null;
  display_answer?: string | null;
  display_citations?: Citation[] | null;
  display_claim_refs?:
    { claim_id: string; issue_id: number | null; label: string }[] | null;
  intent: string;
  citations: Citation[];
  claim_refs: { claim_id: string; issue_id: number | null }[];
  suggested_actions: { label: string; action: string }[];
  refused: boolean;
};
type Turn = { id: number; question: string; result?: Answer; error?: string };
type Conversation = {
  id: number;
  turns: Turn[];
  claimId?: string;
  startedAt: string;
};
const generalQuestions = [
  "암 진단금 청구에 필요한 서류가 뭐야?",
  "실손에서 영양제 비용도 보상돼?",
  "고객님 관련해서 해야 하는 업무 리스트 좀 뽑아줘",
  "오늘 내가 검토할 청구가 몇 건이야?",
];
const claimQuestions = [
  "이 청구 건 서류 다 왔는지 검토해줘",
  "이 건 영수증에 보상 제외될 항목 있어?",
  "누락 서류 보완 요청 문자 써줘",
  "이 건 지급 심사로 넘겨도 돼?",
];

function quoteText(text: string) {
  return text
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/\*\*/g, "")
    .replace(/^\|[- :|]+\|$/gm, "")
    .trim();
}

/** 본문을 안전한 React 텍스트 노드로 렌더링한다. HTML이나 원문 속 명령은 실행하지 않는다. */
function AnswerText({
  text,
  onSkip,
  immediate = false,
}: {
  text: string;
  onSkip: () => void;
  immediate?: boolean;
}) {
  const typing = useTyping(formatDatesInText(text));
  function inline(line: string) {
    return line
      .split(/(\([^()\n]*(?:제\d+조|\d+장)[^()\n]*\))/g)
      .map((part, i) =>
        /^\(.*(?:제\d+조|\d+장)/.test(part) ? (
          <span key={i} className="answer-law">
            {part}
          </span>
        ) : (
          part
        ),
      );
  }
  function body(content: string) {
    // 연속된 목록 줄만 묶어 실제 목록 의미를 제공한다. 원문과 일반 줄바꿈은 보존한다.
    const groups: { list: boolean; lines: string[] }[] = [];
    for (const line of content.split("\n")) {
      const list = /^[ \t]*- /.test(line);
      const last = groups[groups.length - 1];
      if (last?.list === list) last.lines.push(line);
      else groups.push({ list, lines: [line] });
    }
    return groups.map((group, index) =>
      group.list ? (
        <ul key={index} className="answer-list">
          {group.lines.map((line, item) => (
            <li key={item}>{inline(line.replace(/^[ \t]*- /, ""))}</li>
          ))}
        </ul>
      ) : (
        <span key={index}>{inline(group.lines.join("\n"))}</span>
      ),
    );
  }
  return (
    <div
      className="assistant-answer-text"
      data-testid="answer-body"
      aria-busy={!immediate && !typing.complete}
      tabIndex={0}
      title="누르면 답변 전체를 바로 표시해요"
      onClick={() => {
        typing.skip();
        onSkip();
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          typing.skip();
          onSkip();
        }
      }}
    >
      {(immediate ? formatDatesInText(text) : typing.text)
        .split(/\n\s*\n/)
        .map((block, n) => {
          const [title, ...rest] = block.split("\n");
          const headed = /^(추가 서류:|[①-⑳] )/.test(title);
          return (
            <div
              className="answer-block"
              key={n}
              data-tour={n < 4 ? "assistant-answer-summary" : undefined}
            >
              {headed ? (
                <>
                  <strong>{title}</strong>
                  {rest.length > 0 && (
                    <>
                      <br />
                      {body(rest.join("\n"))}
                    </>
                  )}
                </>
              ) : (
                body(block)
              )}
            </div>
          );
        })}
    </div>
  );
}

export function ChatScreen({
  preview,
  initialTime,
}: {
  initialTime: string;
  preview?: {
    question: string;
    answer: Answer;
    showAnswer: boolean;
    showQuestion?: boolean;
  };
}) {
  const params = useSearchParams();
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: 1,
      startedAt: initialTime,
      turns:
        preview && (preview.showAnswer || preview.showQuestion)
          ? [
              {
                id: 1,
                question: preview.question,
                result: preview.showAnswer ? preview.answer : undefined,
              },
            ]
          : [],
      claimId: params.get("claim") ?? undefined,
    },
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
  const sources =
    focus?.result?.display_citations ?? focus?.result?.citations ?? [];
  const nextId = useRef(2);
  const [historyTime, setHistoryTime] = useState(initialTime);
  const [navQuestion, setNavQuestion] = useState<number | null>(null);
  const [exampleClaim, setExampleClaim] = useState<Claim | null>(null);
  const [context, setContext] = useState<Claim | null>(null);
  const [draftTarget, setDraftTarget] = useState("");
  const draftTyping = useTyping(draftTarget);
  const contextId = current.claimId;
  const questions = contextId
    ? claimQuestions
        .filter(
          (q) =>
            q !== claimQuestions[2] ||
            !context ||
            context.issues.some(
              (i) => i.kind === "missing" && i.status === "open",
            ),
        )
        .map((q, index) =>
          index === 0 && context
            ? `${context.customer_name} 고객님 관련해서 해야 하는 업무 리스트 좀 뽑아줘`
            : q,
        )
    : generalQuestions.map((q, index) =>
        index === 2 && exampleClaim
          ? `${exampleClaim.customer_name} 고객님 관련해서 해야 하는 업무 리스트 좀 뽑아줘`
          : q,
      );
  // 예시 고객도 현재 담당자가 조회할 수 있는 실제 청구에서 선택한다.
  useEffect(() => {
    if (preview) return;
    let live = true;
    api<ClaimList>("/claims")
      .then((result) => {
        if (live) setExampleClaim(result.items[0] ?? null);
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [preview]);
  useEffect(() => {
    if (!contextId || preview) return;
    let live = true;
    api<Claim>(`/claims/${contextId}`)
      .then((c) => {
        if (live) setContext(c);
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [contextId, preview]);
  useEffect(() => {
    if (preview) return;
    // 새 답변만 대화 영역 아래로 이동시킨다. 근거 패널이나 브라우저 전체는 움직이지 않는다.
    scroll.current?.scrollTo({
      top: scroll.current.scrollHeight,
      behavior: "smooth",
    });
  }, [turns.length, busy, preview]);
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
    const now = new Date().toISOString();
    setHistoryTime(now);
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
          ? {
              ...c,
              startedAt: c.turns.length ? c.startedAt : now,
              claimId,
              turns: [...c.turns, { id, question: text }],
            }
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
      if (result.intent === "draft") {
        setDraft(result.draft_text ?? null);
        setDraftTarget(result.draft_text ?? "");
      }
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
      <div className="assistant-layout">
        <aside className="assistant-history" aria-label="대화 목록">
          <Link href="/" className="back-home">
            <ArrowLeft size={15} />
            메인으로
          </Link>
          <button
            data-tour="assistant-new-chat"
            className="btn"
            disabled={busy}
            onClick={() => {
              setHistoryTime(new Date().toISOString());
              const id = nextId.current++;
              setConversations((list) => [
                {
                  id,
                  startedAt: new Date().toISOString(),
                  turns: [],
                  claimId: params.get("claim") ?? undefined,
                },
                ...list,
              ]);
              setActive(id);
              setSelected(null);
              setNavQuestion(null);
              setDraft(null);
            }}
          >
            <Plus size={18} />새 채팅
          </button>
          {["오늘", "지난 7일", "이전 대화"].map((group) => {
            const items = conversations.filter(
              (c) =>
                c.turns.length > 0 &&
                conversationDate(c.startedAt, historyTime).group === group,
            );
            return items.length > 0 ? (
              <section className="conversation-group" key={group}>
                <h2>{group}</h2>
                <div className="conversation-list">
                  {items.map((c) => (
                    <button
                      key={c.id}
                      className={`conversation-item ${active === c.id ? "active" : ""}`}
                      disabled={busy}
                      aria-current={active === c.id ? "true" : undefined}
                      onClick={() => {
                        setActive(c.id);
                        setSelected(null);
                        setNavQuestion(null);
                        setDraft(null);
                      }}
                    >
                      <strong title={c.turns[0].question}>
                        {c.turns[0].question}
                      </strong>
                      <time dateTime={c.startedAt}>
                        {conversationDate(c.startedAt, historyTime).label}
                      </time>
                    </button>
                  ))}
                </div>
              </section>
            ) : null;
          })}
          <p className="assistant-session-note">
            대화는 현재 화면에만 보관돼요.
          </p>
        </aside>
        <section
          className="assistant-conversation"
          aria-label="업무 대화"
          data-tour="assistant-body"
        >
          {turns.length > 0 && (
            <nav className="question-nav" aria-label="질문 바로가기">
              {turns.map((t, index) => (
                <button
                  key={t.id}
                  type="button"
                  className={
                    (navQuestion ?? focus?.id) === t.id ? "active" : ""
                  }
                  aria-label={`${index + 1}번째 질문: ${t.question}`}
                  aria-current={
                    (navQuestion ?? focus?.id) === t.id ? "true" : undefined
                  }
                  data-question={t.question}
                  onClick={() => {
                    setSelected(t.id);
                    setNavQuestion(t.id);
                    const node = document.getElementById(`question-${t.id}`),
                      container = scroll.current;
                    if (node && container)
                      container.scrollTo({
                        top:
                          container.scrollTop +
                          node.getBoundingClientRect().top -
                          container.getBoundingClientRect().top -
                          20,
                        behavior: "smooth",
                      });
                  }}
                />
              ))}
            </nav>
          )}
          <div
            className="assistant-scroll"
            ref={scroll}
            onScroll={() => {
              const el = scroll.current;
              if (!el) return;
              const top = el.getBoundingClientRect().top;
              let id = turns[0]?.id ?? null;
              for (const t of turns) {
                const node = document.getElementById(`question-${t.id}`);
                if (node && node.getBoundingClientRect().top <= top + 70)
                  id = t.id;
              }
              setNavQuestion(id);
            }}
          >
            {!turns.length && (
              <div className="assistant-welcome">
                <BookOpen size={30} />
                <h1>무엇을 확인할까요?</h1>
                <p className="muted">
                  약관 조항, 청구 서류 검토, 보완 요청 문구까지 물어보세요.
                  답변마다 근거를 함께 보여드려요.
                </p>
                <div
                  className="assistant-suggestions"
                  data-tour="assistant-actions"
                >
                  {questions.map((q, index) => (
                    <button
                      key={q}
                      onClick={() =>
                        send(
                          q,
                          !contextId && index === 2
                            ? exampleClaim?.id
                            : undefined,
                        )
                      }
                    >
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
                  <h2 className="assistant-user" data-tour="assistant-question">
                    {t.question}
                  </h2>
                  {t.result && (
                    <div
                      className="assistant-answer"
                      data-tour="assistant-answer"
                      data-testid={`answer-${t.id}`}
                    >
                      <div
                        className="assistant-answer-label"
                        data-tour="assistant-answer-summary"
                      >
                        <ShieldCheck size={17} />
                        가온 AI
                        {t.result.refused && (
                          <span className="muted">판단 범위 안내</span>
                        )}
                      </div>
                      <AnswerText
                        immediate={!!preview}
                        onSkip={draftTyping.skip}
                        text={t.result.display_answer ?? t.result.answer}
                      />
                      {(t.result.display_citations ?? t.result.citations)
                        .length > 0 && (
                        <div className="answer-citations">
                          {(
                            t.result.display_citations ?? t.result.citations
                          ).map((c, n) => (
                            <button
                              key={n}
                              className="answer-source-card"
                              onClick={() => setSelected(t.id)}
                            >
                              <BookOpen size={14} />
                              <strong>
                                {c.doc_name} · {citationAddress(c)}
                              </strong>
                            </button>
                          ))}
                        </div>
                      )}
                      <div
                        className="assistant-actions"
                        data-tour="assistant-actions"
                      >
                        {(
                          t.result.display_claim_refs ??
                          t.result.claim_refs.map((r) => ({
                            ...r,
                            label: "청구 상세",
                          }))
                        ).map((r, n) => (
                          <Link
                            key={n}
                            className="text-link"
                            href={`/workspace/detail?claim=${encodeURIComponent(r.claim_id)}${r.issue_id !== null ? `&issue=${r.issue_id}#issue-${r.issue_id}` : ""}`}
                          >
                            <FileText size={14} />
                            {r.label}
                          </Link>
                        ))}
                      </div>
                      {t.result.suggested_actions.map((a) =>
                        a.action.startsWith("open_claim:") ? (
                          <Link
                            key={a.action}
                            className="btn"
                            href={
                              a.action.slice("open_claim:".length)
                                ? `/workspace/detail?claim=${encodeURIComponent(a.action.slice("open_claim:".length))}`
                                : "/workspace"
                            }
                          >
                            {a.label}
                          </Link>
                        ) : a.action.startsWith("open_supplement:") ? (
                          <Link
                            key={a.action}
                            className="btn"
                            href={`/workspace/supplement?claim=${encodeURIComponent(a.action.slice("open_supplement:".length))}`}
                          >
                            {a.label}
                          </Link>
                        ) : (
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
                        ),
                      )}
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
              <section
                className="assistant-draft"
                data-tour="assistant-draft"
                onClick={draftTyping.skip}
              >
                <h2>보완 요청 초안</h2>
                <p className="muted">
                  내용을 수정하고 확인한 뒤 사용해 주세요.
                </p>
                <textarea
                  aria-label="보완 요청 초안"
                  value={draftTyping.complete ? draft : draftTyping.text}
                  readOnly={!draftTyping.complete}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    setCopied(false);
                  }}
                />
                <button
                  className="btn sm"
                  disabled={!draftTyping.complete}
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
                  {copied ? "복사했어요" : "복사"}
                </button>
              </section>
            )}
          </div>
          <form
            data-tour="assistant-input"
            className="assistant-composer"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            {current.claimId && (
              <p className="assistant-context">
                <FileText size={13} />
                {context?.id === current.claimId
                  ? `${context.customer_name} 고객 청구(${current.claimId})를 보고 있어요`
                  : `청구(${current.claimId})를 확인하고 있어요`}
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
        <aside
          className="assistant-sources"
          aria-label="답변 근거"
          data-tour="assistant-sources"
        >
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
                {n + 1} · {citationKind(c)}
              </small>
              <h3>{c.doc_name}</h3>
              <strong>{citationAddress(c)}</strong>
              <blockquote>{c.display_quote ?? quoteText(c.quote)}</blockquote>
              <span>{c.source_path}</span>
            </section>
          ))}
        </aside>
      </div>
    </main>
  );
}
