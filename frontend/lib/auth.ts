import "server-only";
import { cache } from "react";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

/** 화면이 사용하는 공개 사용자 정보. 권한의 최종 판정은 FastAPI에서 한다. */
export type User = { id: number; name: string; role: "reviewer" | "admin" };
export const roleLabel = { reviewer: "심사 담당자", admin: "관리자" };

// 요청 안에서만 중복 조회를 줄인다. 사용자 응답을 공유 캐시에 저장하면 안 된다.
export const getCurrentUser = cache(async (): Promise<User | null> => {
  // 재직렬화하면 서명 쿠키의 = 문자가 %3D로 바뀔 수 있어 원본 헤더를 전달한다.
  const cookieHeader = (await headers()).get("cookie");
  if (!cookieHeader) return null;
  const response = await fetch(
    `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/me`,
    {
      headers: { Cookie: cookieHeader },
      cache: "no-store",
    },
  );
  if (response.status === 401) return null;
  if (!response.ok) throw new Error("사용자 정보를 확인하지 못했습니다.");
  return response.json() as Promise<User>;
});

/** 서버 렌더링 전에 인증을 확인해 로그인 전 업무 화면 노출을 막는다. */
export async function requireUser() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}
