import Link from "next/link";

/** 원본 HTML의 하트 안 십자가를 그대로 표현하는 브랜드 로고. */
export function Brand() {
  return (
    <Link href="/" className="brand" aria-label="가온생명 AI 홈">
      <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <path
          d="M16 28S3 20 3 11.5C3 4.5 12 2 16 8c4-6 13-3.5 13 3.5C29 20 16 28 16 28Z"
          fill="var(--accent-soft)"
          stroke="var(--accent-strong)"
          strokeWidth="1.8"
        />
        <path
          d="M16 11v10M11 16h10"
          stroke="var(--accent-strong)"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
      </svg>
      <span>가온생명</span>
      <small>AI</small>
    </Link>
  );
}
