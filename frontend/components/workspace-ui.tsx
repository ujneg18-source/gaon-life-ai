"use client";
import { useEffect, useState } from "react";
import { CircleCheck, TriangleAlert, Clock3, FilePlus2 } from "lucide-react";
import { api } from "@/lib/workspace";

/** URL과 응답을 함께 보관해 검색이 바뀔 때 이전 응답을 새 결과로 표시하지 않는다. */
export function useResource<T>(url: string) {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<{
    url: string;
    data?: T;
    error?: string;
  }>({ url: "" });
  useEffect(() => {
    let live = true;
    api<T>(url)
      .then((data) => {
        if (live) setResult({ url, data });
      })
      .catch((error) => {
        if (live) setResult({ url, error: error.message });
      });
    return () => {
      live = false;
    };
  }, [url, version]);
  return {
    data: result.url === url ? result.data : undefined,
    error: result.url === url ? result.error : undefined,
    reload: () => setVersion((v) => v + 1),
  };
}
export function Status({ status }: { status: string }) {
  const states: Record<
    string,
    { text: string; className: string; Icon: typeof CircleCheck }
  > = {
    pending: { text: "처리 전", className: "neutral", Icon: Clock3 },
    ready_review: {
      text: "지급 심사 이관 가능",
      className: "good",
      Icon: CircleCheck,
    },
    auto_pass: { text: "자동 통과", className: "good", Icon: CircleCheck },
    supplement: { text: "보완 요청", className: "bad", Icon: FilePlus2 },
    needs_review: {
      text: "검토 필요",
      className: "warning",
      Icon: TriangleAlert,
    },
    processing: { text: "처리 중", className: "neutral", Icon: Clock3 },
    to_payment_review: { text: "지급 심사", className: "accent", Icon: Clock3 },
    open: { text: "확인 필요", className: "warning", Icon: TriangleAlert },
    resolved: { text: "확인 완료", className: "good", Icon: CircleCheck },
    draft: { text: "작성 중", className: "bad", Icon: FilePlus2 },
    sent_mock: { text: "회신 대기", className: "warning", Icon: Clock3 },
    received: { text: "제출 완료", className: "good", Icon: CircleCheck },
  };
  const state = states[status] ?? {
    text: status,
    className: "neutral",
    Icon: Clock3,
  };
  return (
    <span className={`plain-state ${state.className}`}>
      <state.Icon size={15} aria-hidden="true" />
      {state.text}
    </span>
  );
}
export function PageTitle({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="work-title">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <span className="sample-note">가상 시연 데이터</span>
    </div>
  );
}
export function LoadState({ error }: { error?: string }) {
  return (
    <div className="panel load-state" role={error ? "alert" : "status"}>
      {error ?? "정보를 불러오고 있어요…"}
    </div>
  );
}
