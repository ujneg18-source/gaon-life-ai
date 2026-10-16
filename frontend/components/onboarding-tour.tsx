"use client";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  BookOpen,
  CircleHelp,
  Database,
  MessageSquareText,
  X,
} from "lucide-react";
import { tourKey } from "@/lib/tours";
/** 별도 히든 페이지로 격리해 원래 화면의 입력·대화·선택 상태를 보존한다. */
export function OnboardingTour() {
  const path = usePathname(),
    key = tourKey(path) || "home";
  const query = useSearchParams();
  const claim = query.get("claim");
  const [open, setOpen] = useState(false);
  const [frameReady, setFrameReady] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const hub = useRef<HTMLDivElement>(null);
  const menu = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!menuOpen) return;
    menu.current?.querySelector<HTMLElement>("button, a")?.focus();
    const outside = (event: PointerEvent) => {
      if (!hub.current?.contains(event.target as Node)) setMenuOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
        trigger.current?.focus();
      }
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [menuOpen]);
  const trigger = useRef<HTMLButtonElement>(null),
    frame = useRef<HTMLIFrameElement>(null);
  useEffect(() => {
    if (!open) return;
    const before = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const close = () => {
      setOpen(false);
      trigger.current?.focus();
    };
    const receive = (event: MessageEvent) => {
      if (
        event.origin === location.origin &&
        event.source === frame.current?.contentWindow
      ) {
        if (event.data === "gaon-guide-close") close();
        if (event.data === "gaon-guide-ready") {
          setFrameReady(true);
          frame.current?.focus();
        }
      }
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("message", receive);
    window.addEventListener("keydown", escape);
    return () => {
      document.body.style.overflow = before;
      window.removeEventListener("message", receive);
      window.removeEventListener("keydown", escape);
    };
  }, [open]);
  if (path.startsWith("/guide/"))
    return (
      <button
        className="icon-button tour-trigger"
        data-tour="guide-help"
        aria-label="화면 사용 안내"
        disabled
      >
        <CircleHelp size={28} />
      </button>
    );
  return (
    <>
      <div ref={hub} className="help-hub">
        {menuOpen && (
          <nav
            ref={menu}
            id="help-hub-menu"
            className="help-hub-menu"
            aria-label="도움말 메뉴"
          >
            <p>무엇을 도와드릴까요?</p>
            <button
              onClick={() => {
                setMenuOpen(false);
                setFrameReady(false);
                setOpen(true);
              }}
            >
              <BookOpen size={20} />
              <span>
                <strong>가이드라인</strong>
                <small>화면별 사용 방법을 알아보세요</small>
              </span>
            </button>
            <Link
              href={
                claim ? `/chat?claim=${encodeURIComponent(claim)}` : "/chat"
              }
              onClick={() => setMenuOpen(false)}
            >
              <MessageSquareText size={20} />
              <span>
                <strong>업무 어시스턴트</strong>
                <small>약관과 청구 업무를 대화로 물어보세요</small>
              </span>
            </Link>
            <Link href="/data-sources" onClick={() => setMenuOpen(false)}>
              <Database size={20} />
              <span>
                <strong>데이터 출처</strong>
                <small>데모에 사용한 자료를 확인하세요</small>
              </span>
            </Link>
          </nav>
        )}
        <button
          ref={trigger}
          className="icon-button tour-trigger"
          aria-label={menuOpen ? "도움말 메뉴 닫기" : "도움말 메뉴 열기"}
          title="도움말"
          aria-expanded={menuOpen}
          aria-controls="help-hub-menu"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <X size={28} /> : <CircleHelp size={28} />}
        </button>
      </div>
      {open && (
        <div
          className="guide-frame"
          data-ready={frameReady}
          aria-busy={!frameReady}
          role="dialog"
          aria-modal="true"
          aria-label="페이지 사용 안내"
        >
          <iframe
            ref={frame}
            title="독립된 화면 사용 안내"
            src={`/guide/${key}?${key === "detail" ? `q=${encodeURIComponent("김유정")}&` : ""}claim=GA-2610-0482`}
          />
        </div>
      )}
    </>
  );
}
