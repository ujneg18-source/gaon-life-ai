"use client";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Brand } from "./brand";
import { OnboardingTour } from "./onboarding-tour";
import { LogoutButton } from "./logout-button";
import type { User } from "@/lib/auth";
/** 챗봇은 목업처럼 한 줄 헤더를 사용한다. 나머지 업무 화면은 기존 사용자 메뉴를 유지한다. */
export function AppHeader({ user }: { user: User }) {
  const path = usePathname(),
    query = useSearchParams();
  const chat = path === "/chat" || path === "/guide/assistant";
  const workspace =
    path === "/workspace" ||
    path.startsWith("/workspace/") ||
    /^\/guide\/(inbox|detail|review|supplement|history)$/.test(path);
  const claim = query.get("claim");
  return (
    <header className="topbar" data-tour={chat ? "assistant-intro" : undefined}>
      <div className="brand-help">
        <Brand
          badge={
            chat
              ? "업무 어시스턴트"
              : workspace
                ? "서류 검토 워크스페이스"
                : "AI"
          }
        />
        <OnboardingTour />
      </div>
      {chat ? (
        <Link
          className="btn sm"
          href={
            claim
              ? `/workspace/detail?claim=${encodeURIComponent(claim)}`
              : "/workspace"
          }
        >
          워크스페이스로 이동
        </Link>
      ) : (
        <div className="user-menu">
          <span>
            <strong>{user.name}</strong>
            <span className="user-role">
              {user.role === "admin" ? "관리자" : "심사 담당자"}
            </span>
          </span>
          <LogoutButton />
        </div>
      )}
    </header>
  );
}
