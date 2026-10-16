"use client";
import { useEffect, useState, useRef } from "react";
/** 원문은 보존하고 화면에서만 초당 50글자를 표시한다. 건너뛰기는 진행 중 프레임도 멈춘다. */
export function useTyping(text: string) {
  const skipped = useRef(false);
  const [progress, setProgress] = useState({ text: "", count: 0 });
  useEffect(() => {
    skipped.current = false;
    let frame = 0;
    const start = performance.now();
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const tick = (now: number) => {
      const count =
        reduced.matches || skipped.current
          ? text.length
          : Math.min(text.length, Math.floor((now - start) / 20));
      setProgress({ text, count });
      if (count < text.length) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [text]);
  const count = progress.text === text ? progress.count : 0;
  return {
    text: text.slice(0, count),
    complete: count >= text.length,
    skip: () => {
      skipped.current = true;
      setProgress({ text, count: text.length });
    },
  };
}
