"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

/** 쿠키는 JS에서 지우지 않고 서버 로그아웃으로 폐기한다. */
export function LogoutButton() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  async function logout() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok && response.status !== 401) throw new Error();
      router.replace("/login");
      router.refresh();
    } catch {
      setError("로그아웃에 실패했어요. 다시 시도해 주세요.");
      setBusy(false);
    }
  }
  return (
    <div className="logout">
      <button className="btn ghost sm" onClick={logout} disabled={busy}>
        <LogOut size={16} aria-hidden="true" />
        {busy ? "로그아웃 중" : "로그아웃"}
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
