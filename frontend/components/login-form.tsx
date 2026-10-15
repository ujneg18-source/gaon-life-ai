"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ShieldCheck, UserRound, LoaderCircle } from "lucide-react";

/** 역할은 데모 계정 선택에만 사용한다. 실제 세션과 권한은 서버가 발급한다. */
export function LoginForm() {
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();
  async function login(role: "reviewer" | "admin") {
    setPending(role);
    setError("");
    try {
      const response = await fetch("/api/auth/demo-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      if (!response.ok) throw new Error();
      router.replace("/");
      router.refresh();
    } catch {
      setError("로그인에 실패했어요. 서버 연결을 확인하고 다시 시도해 주세요.");
      setPending(null);
    }
  }
  return (
    <div className="login-options">
      {(
        [
          {
            role: "reviewer",
            name: "한지원",
            title: "심사 담당자로 시작",
            description: "접수된 청구를 확인하고 검토합니다.",
            Icon: UserRound,
          },
          {
            role: "admin",
            name: "오세린",
            title: "관리자로 시작",
            description: "검토 기준과 운영 현황을 관리합니다.",
            Icon: ShieldCheck,
          },
        ] as const
      ).map(({ role, name, title, description, Icon }) => (
        <button
          key={role}
          onClick={() => login(role)}
          disabled={pending !== null}
          className="login-option"
        >
          <Icon size={23} className="text-accent-strong" aria-hidden="true" />
          <span>
            <strong>{title}</strong>
            <span className="option-description">{description}</span>
            <span className="option-name">{name} · 데모 계정</span>
          </span>
          {pending === role ? (
            <LoaderCircle
              size={19}
              className="animate-spin"
              aria-label="로그인 중"
            />
          ) : (
            <ArrowRight size={19} aria-hidden="true" />
          )}
        </button>
      ))}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </div>
  );
}
