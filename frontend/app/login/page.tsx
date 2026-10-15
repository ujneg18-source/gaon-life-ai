import { redirect } from "next/navigation";
import { Brand } from "@/components/brand";
import { LoginForm } from "@/components/login-form";
import { getCurrentUser } from "@/lib/auth";

export default async function LoginPage() {
  if (await getCurrentUser()) redirect("/");
  return (
    <main id="main" className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <Brand />
        <p className="eyebrow">GAON LIFE · AI WORKSPACE</p>
        <h1 id="login-title">
          더 명확한 검토,
          <br />더 든든한 업무의 시작.
        </h1>
        <p className="muted login-intro">
          보험금 청구 서류를 모아 보고,
          <br />
          확인이 필요한 순간에 집중하세요.
        </p>
        <LoginForm />
        <p className="demo-note">데모 계정입니다. 모든 데이터는 가상입니다.</p>
      </section>
      <p className="login-footer">가온생명 · 보상 업무를 위한 AI</p>
    </main>
  );
}
