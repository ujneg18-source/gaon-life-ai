"use client";
/** 일시적인 백엔드 장애를 로그인 성공으로 처리하지 않고 재시도를 제공한다. */
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main id="main" className="login-page">
      <section className="login-panel">
        <h1>잠시 연결이 원활하지 않아요</h1>
        <p className="muted">서버 연결을 확인한 뒤 다시 시도해 주세요.</p>
        <button className="btn primary" onClick={reset}>
          다시 시도
        </button>
      </section>
    </main>
  );
}
