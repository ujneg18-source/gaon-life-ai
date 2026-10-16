import Link from "next/link";
import {
  ArrowRight,
  FileCheck2,
  MessageSquareText,
  Sparkles,
} from "lucide-react";

/** SCR-02: 두 업무의 입구만 제공한다. 실제 처리 결과를 목업 숫자로 꾸미지 않는다. */
export default function HomePage() {
  return (
    <main id="main" className="hero">
      <div className="hero-heading" data-tour="home-heading">
        <h1>오늘은 어떤 업무를 도와드릴까요?</h1>
        <p className="muted">보상 담당자를 위한 가온생명 AI</p>
      </div>
      <div className="doors">
        <Link href="/chat" className="door" data-tour="home-assistant">
          <div className="door-top">
            <MessageSquareText size={26} strokeWidth={1.6} />
            <span className="door-index">01 / ASSISTANT</span>
          </div>
          <div>
            <p className="door-kicker">궁금한 업무를, 대화로</p>
            <h2>업무 어시스턴트</h2>
            <p>
              약관과 업무 기준을 찾아보고,
              <br />
              필요한 안내 문구를 준비하세요.
            </p>
          </div>
          <span className="door-go">
            어시스턴트 열기 <ArrowRight size={17} />
          </span>
        </Link>
        <Link href="/workspace" className="door" data-tour="home-workspace">
          <div className="door-top">
            <FileCheck2 size={26} strokeWidth={1.6} />
            <span className="door-index">02 / WORKSPACE</span>
          </div>
          <div>
            <p className="door-kicker">흩어진 서류를, 한눈에</p>
            <h2>보험금 지급 서류 검토</h2>
            <p>
              청구별 서류와 정보를 모아 보고,
              <br />
              누락과 불일치를 확인하세요.
            </p>
          </div>
          <span className="door-go">
            워크스페이스 열기 <ArrowRight size={17} />
          </span>
        </Link>
      </div>
      <p className="home-note">
        <Sparkles size={15} aria-hidden="true" /> 판단은 담당자가, 확인은 더
        명확하게.
      </p>
    </main>
  );
}
