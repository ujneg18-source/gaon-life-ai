import type { Claim, ClaimList } from "@/lib/workspace";
import snapshot from "./snapshot.json";
/** 가상 시연 기록의 읽기 전용 복사본. 실제 API·DB·업무 세션과 연결하지 않는다. */
export const guideClaim = snapshot.claims.find(
  (c) => c.id === "GA-2610-0482",
) as unknown as Claim;
export const guideAnswer = snapshot.answer;
export const guideQuestion =
  "김유정 고객님 관련해서 해야 하는 업무 리스트 좀 뽑아줘";
export function guideResource(url: string, stage: string): unknown {
  const path = new URL(url, "https://guide.invalid");
  if (path.pathname === "/claims") {
    const q = path.searchParams.get("q") ?? "";
    const status = path.searchParams.get("status");
    // 실제 검토함과 같은 우선순위·접수순을 복사본에만 적용한다.
    const all = [...(snapshot.claims as unknown as Claim[])].sort(
      (a, b) =>
        Number(!["supplement", "needs_review"].includes(a.status)) -
          Number(!["supplement", "needs_review"].includes(b.status)) ||
        b.received_at.localeCompare(a.received_at),
    );
    const counts: Record<string, number> = { total: all.length };
    all.forEach((c) => (counts[c.status] = (counts[c.status] ?? 0) + 1));
    return {
      items: all.filter(
        (c) =>
          (!q || `${c.customer_name} ${c.customer?.id} ${c.id}`.includes(q)) &&
          (!status || c.status === status),
      ),
      counts,
    } satisfies ClaimList;
  }
  if (path.pathname === `/claims/${guideClaim.id}`) return guideClaim;
  if (path.pathname.endsWith("/logs")) return snapshot.logs;
  if (path.pathname === "/supplements")
    return [
      {
        id: -1,
        claim_id: guideClaim.id,
        customer_name: guideClaim.customer_name,
        doc_types: ["surgery_cert"],
        channel: "sms",
        message: snapshot.letter,
        status: stage === "sent" ? "sent_mock" : "draft",
        sent_at: stage === "sent" ? "2026-10-16T00:12:00Z" : null,
        received_at: null,
      },
    ];
  throw new Error("안내 예시에 없는 정보입니다. 원래 화면에서 확인해 주세요.");
}
