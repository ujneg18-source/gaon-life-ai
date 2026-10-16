"use client";
import { useEffect } from "react";
import { clearDemoSession } from "@/lib/demo-session";

/** CLI/다른 탭에서 초기화해도 새 페이지로 이동해 메모리의 채팅·안내를 버린다. */
export function DemoSessionBoundary() {
  useEffect(() => {
    if (location.pathname.startsWith("/guide/")) return;
    let disposed = false;
    let checking = false;
    const refresh = () => {
      location.replace("/");
    };
    const check = async () => {
      if (checking || document.hidden) return;
      checking = true;
      try {
        const response = await fetch("/api/demo/state", { cache: "no-store" });
        if (!response.ok || disposed) return;
        const { revision } = (await response.json()) as { revision: string };
        if (disposed) return;
        const previous = localStorage.getItem("gaon-demo-revision");
        if (previous && previous !== revision) {
          clearDemoSession(revision);
          refresh();
        } else localStorage.setItem("gaon-demo-revision", revision);
      } catch {
        // 서버 재시작 중에는 다음 상태 확인에서 다시 시도한다.
      } finally {
        checking = false;
      }
    };
    const storage = (event: StorageEvent) => {
      if (
        event.key === "gaon-demo-revision" &&
        event.oldValue &&
        event.newValue
      ) {
        sessionStorage.removeItem("inbox-return");
        refresh();
      }
    };
    void check();
    const timer = window.setInterval(check, 2000);
    window.addEventListener("storage", storage);
    window.addEventListener("focus", check);
    return () => {
      disposed = true;
      clearInterval(timer);
      window.removeEventListener("storage", storage);
      window.removeEventListener("focus", check);
    };
  }, []);
  return null;
}
