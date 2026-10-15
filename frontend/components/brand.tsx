import Link from "next/link";

/** 원본 HTML의 하트 안 십자가를 그대로 표현하는 브랜드 로고. */
export function Brand() {
  return (
    <Link href="/" className="brand" aria-label="가온생명 AI 홈">
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        {/* 첨부 마크와 동일한 원본 SVG를 사용해 채움색·십자가 비율을 유지한다. */}
        <path
          fill="#9A89F2"
          d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"
        />
        <rect
          x="10.9"
          y="7.2"
          width="2.2"
          height="7.6"
          rx=".5"
          fill="#FFFFFF"
        />
        <rect x="8.2" y="9.9" width="7.6" height="2.2" rx=".5" fill="#FFFFFF" />
      </svg>
      <span>가온생명</span>
      <small>AI</small>
    </Link>
  );
}
