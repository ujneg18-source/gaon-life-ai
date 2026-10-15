import type { Metadata } from "next";
import "@fontsource/noto-sans-kr/400.css";
import "@fontsource/noto-sans-kr/500.css";
import "@fontsource/noto-sans-kr/700.css";
import "@fontsource/ibm-plex-mono/500.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "가온생명 AI",
  description: "보험금 청구 서류 검토를 위한 가온생명 AI 워크스페이스",
};

// 폰트는 로컬 번들로 제공해 빌드·시연에서 Google Fonts 연결에 의존하지 않는다.
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <a className="skip-link" href="#main">
          본문으로 이동
        </a>
        {children}
      </body>
    </html>
  );
}
