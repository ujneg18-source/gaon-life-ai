"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  ClipboardList,
  FileText,
  ScanLine,
  Send,
  History,
  Settings2,
  Search,
  MessageSquareText,
  CircleHelp,
  ArrowLeft,
} from "lucide-react";
import { workspacePages } from "@/lib/navigation";

const menuIcons = [ClipboardList, FileText, ScanLine, Send, History, Settings2];
/** 역할별 메뉴 표시만 담당한다. 서버 경로/API 권한 검사는 별도다. */
export function WorkspaceShell({
  admin,
  children,
}: {
  admin: boolean;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [help, setHelp] = useState(false);
  const [searchNote, setSearchNote] = useState("");
  return (
    <div className="workspace-shell">
      <aside className="sidebar" aria-label="워크스페이스 메뉴">
        <Link href="/" className="back-home">
          <ArrowLeft size={15} />
          메인으로
        </Link>
        <p className="eyebrow sidebar-label">WORKSPACE</p>
        <nav>
          {workspacePages.map((page, i) => {
            if ("adminOnly" in page && page.adminOnly && !admin) return null;
            const href = `/workspace${page.slug ? `/${page.slug}` : ""}`;
            const Icon = menuIcons[i];
            return (
              <Link
                key={href}
                href={href}
                className={`nav-item ${pathname === href ? "active" : ""}`}
                aria-current={pathname === href ? "page" : undefined}
              >
                <Icon size={19} strokeWidth={1.7} />
                {page.title}
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          가온생명 AI<span>보험금 청구 서류 검토</span>
        </div>
      </aside>
      <div className="workspace-body">
        <div className="searchbar">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              setSearchNote("통합 검색은 준비 중입니다.");
            }}
          >
            <Search size={18} aria-hidden="true" />
            <input
              aria-label="고객 이름 · 청구번호 · 증권번호로 검색"
              placeholder="고객 이름 · 청구번호 · 증권번호로 검색"
            />
            <button className="btn sm" type="submit">
              검색
            </button>
          </form>
          {searchNote && (
            <span role="status" className="search-note">
              {searchNote}
            </span>
          )}
        </div>
        <main id="main" className="workspace-content">
          {children}
        </main>
      </div>
      <div className="floating-actions">
        <Link href="/chat" className="btn primary">
          <MessageSquareText size={18} />
          가온 AI에게 묻기
        </Link>
        <button
          className="btn help-button"
          aria-label="메뉴 안내"
          aria-expanded={help}
          aria-controls="workspace-help"
          onClick={() => setHelp(!help)}
        >
          <CircleHelp size={21} />
        </button>
      </div>
      {help && (
        <section
          id="workspace-help"
          className="help-panel"
          aria-label="메뉴 안내"
        >
          <strong>워크스페이스 안내</strong>
          <p>
            왼쪽 메뉴에서 청구 검토·보완·이력을 선택하세요. 운영 관리는
            관리자에게만 표시됩니다.
          </p>
          <button className="btn sm" onClick={() => setHelp(false)}>
            닫기
          </button>
        </section>
      )}
    </div>
  );
}
