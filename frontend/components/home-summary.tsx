"use client";
import { useResource } from "./workspace-ui";
import { ClaimList } from "@/lib/workspace";
export function HomeSummary() {
  const { data, error } = useResource<ClaimList>("/claims");
  return (
    <p data-tour="home-summary" className="home-summary">
      {data
        ? `배정된 청구 ${data.counts.total}건 · 검토 필요 ${data.counts.needs_review}건 · 보완 요청 ${data.counts.supplement}건`
        : error
          ? "청구 현황을 확인하지 못했어요."
          : "청구 현황을 확인하고 있어요."}
    </p>
  );
}
