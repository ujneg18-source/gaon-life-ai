"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  X,
  Check,
  Sparkles,
  MessageSquareText,
  ClipboardList,
  FileText,
  ScanLine,
  Send,
  History,
} from "lucide-react";
import { placeGuide } from "@/lib/guide/placement";
import { GuideContext } from "@/lib/guide/context";
import {
  guideAnswer,
  guideClaim,
  guideQuestion,
  guideResource,
} from "@/lib/guide/data";
import { tours } from "@/lib/tours";
import { HomeScreen } from "./home-screen";
import { ChatScreen, type Answer } from "./chat-screen";
import { WorkspaceShell } from "./workspace-shell";
import { Inbox, ClaimDetail, ClaimPicker } from "./claim-screens";
import { ReviewScreen } from "./review-screen";
import { SupplementScreen, HistoryScreen } from "./operations-screens";

export function GuidePlayer({
  screen,
  initialTime,
}: {
  screen: string;
  initialTime: string;
}) {
  const [index, setIndex] = useState(0);
  const steps = tours[screen],
    step = steps[index],
    stage = step.stage ?? "";
  const [box, setBox] = useState({ x: 0, y: 0, w: 0, h: 0 });
  const [position, setPosition] = useState({
    left: 16,
    top: 80,
    side: "top",
    arrow: 40,
    separate: true,
  });
  const Icon = (
    {
      home: Sparkles,
      assistant: MessageSquareText,
      inbox: ClipboardList,
      detail: FileText,
      review: ScanLine,
      supplement: Send,
      history: History,
    } as Record<string, typeof Sparkles>
  )[screen];
  const sectionName = (
    {
      home: "메인",
      assistant: "업무 어시스턴트",
      inbox: "청구 검토함",
      detail: "청구건 상세",
      review: "문서 분석·검토",
      supplement: "보완 처리",
      history: "검토 이력",
    } as Record<string, string>
  )[screen];
  const card = useRef<HTMLDivElement>(null);
  const data = useMemo(
    () => ({ resolve: (url: string) => guideResource(url, stage) }),
    [stage],
  );
  const close = () => {
    if (window.parent !== window)
      window.parent.postMessage("gaon-guide-close", location.origin);
    else
      window.location.assign(
        screen === "home"
          ? "/"
          : screen === "assistant"
            ? "/chat"
            : screen === "inbox"
              ? "/workspace"
              : `/workspace/${screen}`,
      );
  };
  useEffect(() => {
    let frame = 0,
      retries = 0;
    let positioned = false,
      shifted = false;
    const update = () => {
      let targets = Array.from(
        document.querySelectorAll<HTMLElement>(`[data-tour="${step.target}"]`),
      );
      // 좁은 화면도 머리글과 실제 두 행을 함께 보여주되 설명 공간을 남긴다.
      if (
        innerWidth <= 850 &&
        /^(inbox-heading-|review-field-(values|sources))/.test(step.target)
      )
        targets = targets.slice(0, 6);
      if (!targets.length) {
        if (retries++ < 30) frame = requestAnimationFrame(update);
        return;
      }
      const first = targets[0].getBoundingClientRect();
      // 보이는 일부만 잘라 강조하지 않고, 설명할 작은 영역 전체를 먼저 화면 안으로 옮긴다.
      if (
        !positioned &&
        (first.top < 16 ||
          first.bottom > innerHeight - 16 ||
          first.left < 16 ||
          first.right > innerWidth - 16)
      )
        targets[0].scrollIntoView({
          block: "center",
          inline: "center",
          behavior: "instant",
        });
      positioned = true;
      const rects = targets
        .map((t) => t.getBoundingClientRect())
        .filter((r) => r.width > 0 && r.height > 0);
      if (!rects.length) {
        setBox({ x: 0, y: 0, w: 0, h: 0 });
        return;
      }
      const x = Math.max(0, Math.min(...rects.map((r) => r.left)) - 7),
        y = Math.max(0, Math.min(...rects.map((r) => r.top)) - 7);
      const right = Math.min(
          innerWidth,
          Math.max(...rects.map((r) => r.right)) + 7,
        ),
        bottom = Math.min(
          innerHeight,
          Math.max(...rects.map((r) => r.bottom)) + 7,
        );
      const target = { x, y, w: right - x, h: bottom - y };
      setBox(target);
      const placement = placeGuide(
        target,
        {
          w: card.current?.offsetWidth ?? 410,
          h: card.current?.offsetHeight ?? 260,
        },
        { w: innerWidth, h: innerHeight },
        step.placement,
      );
      // 대상이 중앙에 있어 설명 공간이 없으면 먼저 위쪽에 정렬해 아래 공간을 확보한다.
      if (
        (!placement.separate || (step.placement && placement.side !== "top")) &&
        !shifted
      ) {
        shifted = true;
        targets[0].scrollIntoView({
          block: "start",
          inline: "nearest",
          behavior: "instant",
        });
        frame = requestAnimationFrame(update);
        return;
      }
      setPosition(placement);
    };
    frame = requestAnimationFrame(() => {
      update();
      card.current?.focus();
    });
    const observer = new ResizeObserver(update),
      main = document.querySelector("main");
    if (main) observer.observe(main);
    const keys = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        setIndex((n) => Math.min(steps.length - 1, n + 1));
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setIndex((n) => Math.max(0, n - 1));
      }
      if (e.key === "Tab") {
        const nodes = Array.from(
            card.current?.querySelectorAll<HTMLButtonElement>(
              "button:not(:disabled)",
            ) ?? [],
          ),
          first = nodes[0],
          last = nodes[nodes.length - 1];
        if (
          e.shiftKey &&
          (document.activeElement === first ||
            document.activeElement === card.current)
        ) {
          e.preventDefault();
          last?.focus();
        } else if (
          !e.shiftKey &&
          (document.activeElement === last ||
            document.activeElement === card.current)
        ) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener("keydown", keys);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("keydown", keys);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
    // 단계가 바뀔 때만 안내 전용 화면과 초점을 이동한다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, steps.length]);
  let content;
  if (screen === "home") content = <HomeScreen />;
  else if (screen === "assistant")
    content = (
      <ChatScreen
        initialTime={initialTime}
        key={stage}
        preview={{
          question: guideQuestion,
          answer: guideAnswer as unknown as Answer,
          showAnswer: stage === "answer",
          showQuestion: stage === "question",
        }}
      />
    );
  else {
    const claimId = guideClaim.id;
    const body =
      screen === "inbox" ? (
        <Inbox />
      ) : screen === "detail" ? (
        stage === "search" ? (
          <ClaimPicker section="detail" />
        ) : (
          <ClaimDetail
            claimId={claimId}
            readOnly={false}
            guideStep={step.detailStep ?? 0}
          />
        )
      ) : screen === "review" ? (
        <ReviewScreen
          key={stage}
          claimId={claimId}
          readOnly={false}
          guideIssue={
            stage === "compare"
              ? guideClaim.display_issues.find((i) => i.rule_id === "CV-01")?.id
              : undefined
          }
        />
      ) : screen === "supplement" ? (
        <SupplementScreen key={stage} claimId={claimId} readOnly={false} />
      ) : (
        <HistoryScreen claimId={claimId} />
      );
    content = (
      <WorkspaceShell
        admin={false}
        guidePath={screen === "inbox" ? "/workspace" : `/workspace/${screen}`}
      >
        {body}
      </WorkspaceShell>
    );
  }
  return (
    <GuideContext.Provider value={data}>
      <div
        className="guide-sample-surface"
        data-guide-screen={screen}
        data-guide-target={step.target}
      >
        {content}
      </div>
      <div className="tour-overlay">
        <svg width="100%" height="100%" aria-hidden="true">
          <defs>
            <mask id="tour-hole">
              <rect width="100%" height="100%" fill="white" />
              <rect
                x={box.x}
                y={box.y}
                width={box.w}
                height={box.h}
                rx="8"
                fill="black"
              />
            </mask>
          </defs>
          <rect
            width="100%"
            height="100%"
            fill="rgba(20,16,42,.65)"
            mask="url(#tour-hole)"
          />
          <rect
            x={box.x}
            y={box.y}
            width={box.w}
            height={box.h}
            rx="8"
            fill="none"
            stroke="white"
            strokeWidth="3"
          />
        </svg>
        <div
          ref={card}
          className="tour-card"
          data-guide-target={step.target}
          role="dialog"
          aria-modal="true"
          aria-labelledby="guide-title"
          aria-describedby="guide-description"
          tabIndex={-1}
          data-side={position.side}
          data-placement-separate={position.separate}
          style={{ left: position.left, top: position.top }}
        >
          <span className="tour-kicker">
            {sectionName} · {index + 1}단계
          </span>
          <button
            className="icon-button"
            aria-label="안내 닫기"
            onClick={close}
          >
            <X size={16} />
          </button>
          <span
            className="tour-pointer"
            aria-hidden="true"
            style={
              position.side === "left" || position.side === "right"
                ? { top: position.arrow - 7 }
                : { left: position.arrow - 7 }
            }
          />
          <div className="tour-heading">
            <span className="tour-symbol">
              <Icon size={22} />
            </span>
            <h2 id="guide-title">{step.title}</h2>
          </div>
          <div id="guide-description">
            {step.description.split("\n\n").map((p, i) => (
              <p key={i}>{p}</p>
            ))}
            {step.details && (
              <dl className="tour-details">
                {step.details.map((detail) => (
                  <div key={detail.label}>
                    <dt>{detail.label}</dt>
                    <dd>{detail.text}</dd>
                  </div>
                ))}
              </dl>
            )}
          </div>
          <footer>
            <button className="text-link" onClick={close}>
              건너뛰기
            </button>
            <span>
              {index + 1}/{steps.length}
            </span>
            <button
              className="icon-button"
              aria-label="이전 안내"
              disabled={!index}
              onClick={() => setIndex(index - 1)}
            >
              <ArrowLeft size={17} />
            </button>
            <button
              className="tour-next"
              aria-label={
                index === steps.length - 1 ? "안내 마침" : "다음 안내"
              }
              onClick={() =>
                index === steps.length - 1 ? close() : setIndex(index + 1)
              }
            >
              {index === steps.length - 1 ? (
                <Check size={19} />
              ) : (
                <ArrowRight size={19} />
              )}
            </button>
          </footer>
        </div>
      </div>
    </GuideContext.Provider>
  );
}
