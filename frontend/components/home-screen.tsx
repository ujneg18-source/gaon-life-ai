import Link from "next/link";
import {
  ArrowRight,
  FileCheck2,
  MessageSquareText,
  Sparkles,
} from "lucide-react";

/** SCR-02: 두 업무의 입구만 제공한다. 실제 처리 결과를 목업 숫자로 꾸미지 않는다. */
export function HomeScreen() {
  return (
    <main id="main" className="hero">
      <div className="home-overview" data-tour="home-overview">
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
                약관, 심사 기준, 업무 절차를 물어보면
                <br />
                관련된 근거 문서와 함께 답해 드려요
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
                청구 서류 분석부터 누락 불일치 확인 보완요청까지
                <br />
                한곳에서 처리해요
              </p>
            </div>
            <span className="door-go">
              워크스페이스 열기 <ArrowRight size={17} />
            </span>
          </Link>
        </div>
      </div>
      <p className="home-note">
        <Sparkles size={15} aria-hidden="true" /> 판단은 담당자가, 확인은 더
        명확하게.
      </p>
    </main>
  );
}
