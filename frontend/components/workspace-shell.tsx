"use client";
import Link from "next/link";
import { usePathname, useSearchParams, useRouter } from "next/navigation";
import {
  ClipboardList,
  FileText,
  ScanLine,
  Send,
  History,
  Settings2,
  Search,
  MessageSquareText,
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
  const search = useSearchParams();
  const router = useRouter();
  const claim = search.get("claim");

  return (
    <div className="workspace-shell">
      <aside
        className="sidebar"
        aria-label="워크스페이스 메뉴"
        data-tour="workspace-navigation"
      >
        <Link href="/" className="back-home">
          <ArrowLeft size={15} />
          메인으로
        </Link>
        <p className="eyebrow sidebar-label">WORKSPACE</p>
        <nav>
          {workspacePages.map((page, i) => {
            if ("adminOnly" in page && page.adminOnly && !admin) return null;
            const base = `/workspace${page.slug ? `/${page.slug}` : ""}`;
            const href = base + (page.slug && claim ? `?claim=${claim}` : "");
            const Icon = menuIcons[i];
            return (
              <Link
                key={href}
                href={href}
                className={`nav-item ${pathname === base ? "active" : ""}`}
                aria-current={pathname === base ? "page" : undefined}
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
        <div className="searchbar" data-tour="workspace-search">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget);
              router.push(
                "/workspace?" +
                  new URLSearchParams({ q: String(form.get("q") ?? "") }),
              );
            }}
          >
            <Search size={18} aria-hidden="true" />
            <input
              name="q"
              defaultValue={search.get("q") ?? ""}
              aria-label="고객 이름 · 청구번호 · 증권번호로 검색"
              placeholder="고객 이름 · 청구번호 · 증권번호로 검색"
            />
            <button className="btn sm" type="submit">
              검색
            </button>
          </form>
        </div>
        <main id="main" className="workspace-content">
          {children}
        </main>
        <div className="workspace-actions">
          <Link
            href={claim ? `/chat?claim=${encodeURIComponent(claim)}` : "/chat"}
            className="btn primary"
          >
            <MessageSquareText size={18} />
            가온 AI에게 묻기
          </Link>
        </div>
      </div>
    </div>
  );
}
