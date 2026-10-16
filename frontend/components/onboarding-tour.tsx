"use client";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { CircleHelp } from "lucide-react";
import { tourKey } from "@/lib/tours";
/** 별도 히든 페이지로 격리해 원래 화면의 입력·대화·선택 상태를 보존한다. */
export function OnboardingTour() {
  const path = usePathname(),
    key = tourKey(path);
  const [open, setOpen] = useState(false);
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
        event.source === frame.current?.contentWindow &&
        event.data === "gaon-guide-close"
      )
        close();
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
        <CircleHelp size={19} />
      </button>
    );
  if (!key) return null;
  return (
    <>
      <button
        ref={trigger}
        className="icon-button tour-trigger"
        aria-label="화면 사용 안내"
        title="화면 사용 안내"
        onClick={() => setOpen(true)}
      >
        <CircleHelp size={19} />
      </button>
      {open && (
        <div
          className="guide-frame"
          role="dialog"
          aria-modal="true"
          aria-label="페이지 사용 안내"
        >
          <iframe
            ref={frame}
            title="독립된 화면 사용 안내"
            src={`/guide/${key}?${key === "detail" ? `q=${encodeURIComponent("김유정")}&` : ""}claim=GA-2610-0482`}
            onLoad={() => frame.current?.focus()}
          />
        </div>
      )}
    </>
  );
}
