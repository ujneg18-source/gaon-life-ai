"use client";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { CircleHelp, ArrowLeft, ArrowRight, X } from "lucide-react";
import { tours } from "@/lib/tours";
/** 외부 라이브러리 없이 스포트라이트와 키보드 탐색을 제공한다. 저장 실패는 업무를 막지 않는다. */
export function OnboardingTour() {
  const path = usePathname();
  const key =
    path === "/"
      ? "home"
      : path === "/chat"
        ? "assistant"
        : path === "/workspace"
          ? "inbox"
          : path === "/workspace/detail"
            ? "detail"
            : path === "/workspace/review"
              ? "review"
              : path.startsWith("/workspace/")
                ? "workspace"
                : "";
  const [index, setIndex] = useState<number | null>(null);
  const [box, setBox] = useState({ x: 0, y: 0, w: 0, h: 0 });
  const [windowSize, setWindowSize] = useState({ w: 1280, h: 720 });
  const card = useRef<HTMLDivElement>(null),
    trigger = useRef<HTMLButtonElement>(null);
  const steps = tours[key] ?? [];
  const step = index === null ? null : steps[index];
  function finish() {
    setIndex(null);
    trigger.current?.focus();
  }
  // 사용자가 도움말을 요청할 때만 열어 업무 진입을 방해하지 않는다.
  useEffect(() => {
    if (!step) return;
    if (step.detailStep !== undefined)
      window.dispatchEvent(
        new CustomEvent("tour-detail-step", { detail: step.detailStep }),
      );
    const update = () => {
      const target = document.querySelector(`[data-tour="${step.target}"]`);
      const r = target?.getBoundingClientRect();
      if (r)
        setBox({
          x: Math.max(8, r.left - 6),
          y: Math.max(8, r.top - 6),
          w: Math.min(r.width + 12, window.innerWidth - 16),
          h: Math.min(r.height + 12, window.innerHeight - 16),
        });
      setWindowSize({ w: innerWidth, h: innerHeight });
    };
    const frame = requestAnimationFrame(() => {
      const target = document.querySelector(`[data-tour="${step.target}"]`);
      const r = target?.getBoundingClientRect();
      if (r && (r.top < 64 || r.bottom > innerHeight))
        target?.scrollIntoView({ block: "center", behavior: "instant" });
      update();
      card.current?.focus();
    });
    const keys = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIndex(null);
        trigger.current?.focus();
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        setIndex((n) =>
          n === null ? null : Math.min(steps.length - 1, n + 1),
        );
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setIndex((n) => (n === null ? null : Math.max(0, n - 1)));
      }
      if (e.key === "Tab") {
        const nodes = Array.from(
          card.current?.querySelectorAll<HTMLButtonElement>(
            "button:not(:disabled)",
          ) ?? [],
        );
        const first = nodes[0],
          last = nodes[nodes.length - 1];
        if (
          e.shiftKey &&
          (document.activeElement === first ||
            document.activeElement === card.current)
        ) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    window.addEventListener("keydown", keys);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
      window.removeEventListener("keydown", keys);
    };
  }, [step, steps.length]);
  if (!steps.length) return null;
  return (
    <>
      <button
        ref={trigger}
        className="icon-button tour-trigger"
        aria-label="화면 사용 안내"
        title="화면 사용 안내"
        disabled={!steps.length}
        onClick={() => setIndex(0)}
      >
        <CircleHelp size={19} />
      </button>
      {step && index !== null && (
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
              stroke="var(--accent)"
              strokeWidth="2"
            />
          </svg>
          <div
            className="tour-card"
            role="dialog"
            aria-modal="true"
            aria-label="화면 사용 안내"
            tabIndex={-1}
            ref={card}
            style={{
              left: Math.max(
                12,
                Math.min(box.x + box.w + 16, windowSize.w - 350),
              ),
              top: Math.max(
                80,
                Math.min(box.y + box.h + 16, windowSize.h - 245),
              ),
            }}
          >
            <span className="accent">화면 안내</span>
            <button
              className="icon-button"
              aria-label="안내 닫기"
              onClick={finish}
            >
              <X size={16} />
            </button>
            <h2>{step.title}</h2>
            <p>{step.description}</p>
            <footer>
              <button className="text-link" onClick={finish}>
                건너뛰기
              </button>
              <span>
                {index + 1}/{steps.length}
              </span>
              <button
                className="icon-button"
                aria-label="이전 안내"
                disabled={index === 0}
                onClick={() => setIndex(index - 1)}
              >
                <ArrowLeft size={17} />
              </button>
              <button
                className="icon-button"
                aria-label={
                  index === steps.length - 1 ? "안내 마침" : "다음 안내"
                }
                onClick={() =>
                  index === steps.length - 1 ? finish() : setIndex(index + 1)
                }
              >
                <ArrowRight size={17} />
              </button>
            </footer>
          </div>
        </div>
      )}
    </>
  );
}
