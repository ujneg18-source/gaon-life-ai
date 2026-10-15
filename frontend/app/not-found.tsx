import Link from "next/link";
export default function NotFound() {
  return (
    <main id="main" className="login-page">
      <section className="login-panel">
        <h1>페이지를 찾을 수 없어요</h1>
        <p className="muted">주소 또는 계정의 접근 권한을 확인해 주세요.</p>
        <Link className="btn primary" href="/">
          메인으로
        </Link>
      </section>
    </main>
  );
}
