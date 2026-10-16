"use client";
import { useState } from "react";
import Link from "next/link";
import { formatDateTime, formatDatesInText } from "@/lib/dates";
import {
  CircleCheck,
  Send,
  Save,
  UserRound,
  Sparkles,
  SlidersHorizontal,
} from "lucide-react";
import {
  api,
  Claim,
  docLabels,
  typeLabels,
  label,
  ruleLabel,
} from "@/lib/workspace";
import { PageTitle, LoadState, Status, useResource } from "./workspace-ui";

type Supplement = {
  id: number;
  claim_id: string;
  customer_name: string;
  doc_types: string[];
  channel: string;
  message: string;
  status: string;
  created_at: string | null;
  sent_at: string | null;
  received_at: string | null;
};
/** 서버가 만든 초안만 편집한다. 발송은 모의 상태 전이이며 수신자 전송 기능은 없다. */
function MessageEditor({
  row,
  readOnly,
  reload,
}: {
  row: Supplement;
  readOnly: boolean;
  reload: () => void;
}) {
  const [message, setMessage] = useState(row.message),
    [channel, setChannel] = useState(row.channel),
    [feedback, setFeedback] = useState(""),
    [busy, setBusy] = useState(false);
  const [sourceMessage, setSourceMessage] = useState(row.message);
  // 같은 초안 ID를 재생성해도 서버의 새 문구를 반영하고 발송 피드백은 유지한다.
  if (sourceMessage !== row.message) {
    setSourceMessage(row.message);
    setMessage(row.message);
  }
  const locked = readOnly || row.status !== "draft";
  async function save(send = false) {
    setBusy(true);
    try {
      await api(`/supplements/${row.id}`, {
        method: "PATCH",
        body: JSON.stringify({ message, channel }),
      });
      if (send) await api(`/supplements/${row.id}/send`, { method: "POST" });
      setFeedback(
        send ? "모의 발송 완료 · 회신 대기 상태예요." : "초안을 저장했어요.",
      );
      reload();
    } catch (e) {
      setFeedback((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel message-editor" data-tour="supplement-editor">
      <div className="panel-heading">
        <h2>{row.customer_name} 고객 안내</h2>
        <Status status={row.status} />
      </div>
      <div className="message-body">
        <div className="channel-tabs" aria-label="발송 채널">
          {[
            ["kakao", "알림톡"],
            ["sms", "문자"],
          ].map(([value, text]) => (
            <button
              key={value}
              aria-pressed={channel === value}
              disabled={locked || busy}
              className={channel === value ? "selected" : ""}
              onClick={() => setChannel(value)}
            >
              {text}
            </button>
          ))}
        </div>
        <p className="muted small">요청 서류</p>
        <p className="request-docs">
          {row.doc_types.map((t) => (
            <span key={t}>
              <CircleCheck size={14} />
              {docLabels[t] ?? t}
            </span>
          ))}
        </p>
        <div className="message-preview">
          <strong>가온생명 보험금 안내</strong>
          <textarea
            aria-label="고객 안내 문구"
            data-tour="supplement-letter"
            value={message}
            maxLength={2000}
            disabled={locked || busy}
            onChange={(e) => setMessage(e.target.value)}
          />
        </div>
        <p className="muted small">
          {row.status === "sent_mock"
            ? "모의 발송이 완료됐어요. 보완 서류의 회신을 기다리고 있어요."
            : "안내 문구를 확인한 뒤 모의 발송해 주세요."}
        </p>
        <div className="action-row" data-tour="supplement-send">
          <button
            className="btn"
            disabled={locked || busy || !message.trim()}
            onClick={() => save()}
          >
            <Save size={16} />
            초안 저장
          </button>
          <button
            className="btn primary"
            disabled={locked || busy || !message.trim()}
            onClick={() => save(true)}
          >
            <Send size={16} />
            모의 발송
          </button>
        </div>
        {feedback && <p role="status">{feedback}</p>}
      </div>
    </section>
  );
}
/** 검색으로 정해진 고객만 다루며 생성 응답을 즉시 편집기에 전달한다. */
export function SupplementScreen({
  claimId,
  readOnly,
}: {
  claimId: string;
  readOnly: boolean;
}) {
  const requestUrl = `/supplements?claim_id=${encodeURIComponent(claimId)}`;
  const resource = useResource<Supplement[]>(requestUrl);
  const currentClaim = useResource<Claim>(
    `/claims/${encodeURIComponent(claimId)}`,
  );
  const [generated, setGenerated] = useState<Supplement | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  if (!resource.data || !currentClaim.data)
    return <LoadState error={resource.error ?? currentClaim.error} />;
  const claim = currentClaim.data;
  const rows = resource.data.filter((r) => r.claim_id === claimId);
  const missing = claim.display_issues.filter((i) => i.kind === "missing");
  const missingNames = [
    ...new Set(missing.map((i) => i.title.replace(/\s*(?:누락|미제출)$/, ""))),
  ];
  const row =
    generated ??
    rows.find((r) => r.id === selected) ??
    rows.find((r) => r.status === "draft");
  const sent = rows.filter((r) => r.status !== "draft");
  async function refresh() {
    // 저장/발송 응답 뒤에도 화면은 서버의 최신 내용과 상태를 사용한다.
    const fresh = await api<Supplement[]>(requestUrl);
    setGenerated(fresh.find((r) => r.id === row?.id) ?? null);
    resource.reload();
  }
  async function create() {
    setBusy(true);
    setMessage("");
    try {
      const result = await api<Supplement>(`/claims/${claimId}/supplements`, {
        method: "POST",
      });
      setGenerated(result);
      setSelected(result.id);
      resource.reload();
      setMessage("준비된 안내 양식에 청구 정보를 채웠어요.");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        title="보완 처리"
        description="누락 서류를 확인하고 안내 문자를 작성하세요."
      />
      <div className="supplement-grid supplement-workspace">
        <aside
          className="panel claimant-summary"
          data-tour="supplement-customer"
        >
          <p className="small muted">청구인</p>
          <h2>{claim.customer_name}</h2>
          <p className="mono small">{claim.id}</p>
          <div className="claimant-missing" data-tour="supplement-missing">
            <strong>
              누락 서류{" "}
              <span className="muted small">총 {missingNames.length}개</span>
            </strong>
            <p>{missingNames.join(", ") || "누락된 필수 서류가 없어요."}</p>
          </div>
          <button
            className="btn primary"
            disabled={
              readOnly ||
              busy ||
              !missingNames.length ||
              rows.some((r) => r.status === "sent_mock")
            }
            data-tour="supplement-generate"
            onClick={create}
          >
            {busy ? "안내 문자 준비 중…" : "안내 문자 생성"}
          </button>
          {message && (
            <p className="small" role="status">
              {message}
            </p>
          )}
        </aside>
        <div className="correspondence-column">
          <section
            className="panel correspondence-history"
            aria-label="발송 및 회신 이력"
            data-tour="supplement-history"
          >
            <h2>발송·회신 이력</h2>
            {!sent.length && (
              <p className="muted small">
                아직 발송하거나 회신받은 내역이 없어요.
              </p>
            )}
            {sent.map((item) => (
              <div key={item.id} className="correspondence-entry">
                <button
                  className="correspondence-message"
                  onClick={() => {
                    setGenerated(null);
                    setSelected(item.id);
                  }}
                >
                  <span>
                    <strong>
                      {item.channel === "sms" ? "문자" : "알림톡"} 발송 (모의)
                    </strong>
                    <time>
                      {item.sent_at
                        ? formatDateTime(item.sent_at)
                        : "시각 기록 없음"}
                    </time>
                  </span>
                  <p>{item.message}</p>
                </button>
                {item.status === "received" && (
                  <div className="correspondence-reply">
                    <strong>보완 서류 접수</strong>
                    <time>
                      {item.received_at
                        ? formatDateTime(item.received_at)
                        : "시각 기록 없음"}
                    </time>
                    <p>
                      {item.doc_types
                        .map((code) => docLabels[code] ?? code)
                        .join(", ")}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </section>
          {row ? (
            <MessageEditor
              key={row.id}
              row={row}
              readOnly={readOnly}
              reload={refresh}
            />
          ) : (
            <section className="panel empty-message">
              {missingNames.length
                ? "안내 문자 생성을 누르면 이 청구의 안내 문구가 여기에 표시돼요."
                : "추가로 요청할 필수 서류가 없어요."}
            </section>
          )}
        </div>
      </div>
    </>
  );
}

type Log = {
  id: number;
  claim_id: string;
  actor_type: string;
  actor_id: number | null;
  action: string;
  detail: Record<string, unknown>;
  created_at: string;
};
const actionLabels: Record<string, string> = {
  view: "검토 시작 · 청구 조회",
  upload: "서류 제출",
  document_upload: "서류 제출",
  silson24_receive: "실손24 데이터 수신",
  process_start: "문서 분석 시작",
  process_done: "문서 분석 완료",
  process_failed: "문서 분석 확인 필요",
  field_confirm: "추출 항목 확정",
  issue_resolve: "이슈 확인 완료",
  claim_edit: "청구 검토 단계 · 메모 저장",
  claim_submit: "지급 심사 단계로 전달",
  supplement_draft: "보완 안내 초안 작성",
  supplement_edit: "보완 안내 수정",
  supplement_send_mock: "보완 안내 모의 발송",
};
function logDetail(log: Log) {
  const d = log.detail;
  if (log.action === "field_confirm")
    return `${label(String(d.key))} · ${d.before} → ${d.after}`;
  if (log.action === "issue_resolve")
    return `${ruleLabel(String(d.rule_id))} 확인 기록`;
  if (log.action === "supplement_send_mock")
    return `${d.channel === "kakao" ? "알림톡" : "문자"} · 모의 발송 · 회신 대기`;
  if (log.action === "supplement_draft")
    return `${Array.isArray(d.doc_types) ? d.doc_types.map((t) => docLabels[String(t)] ?? t).join(", ") : ""} · ${d.message_source === "standard_template" ? "표준 문구" : "Solar 초안"}`;
  if (log.action === "process_done")
    return `서류 ${d.document_count ?? "—"}장 · 필수 ${Array.isArray(d.required) ? d.required.length : "—"}종 · 확인 사항 ${d.issue_count ?? "—"}건`;
  if (log.action === "process_start")
    return `접수 서류 ${d.document_count ?? "—"}장 분석 요청`;
  if (log.action === "view") return "청구 정보와 첨부 서류 확인";
  if (log.action === "silson24_receive")
    return `실손24 모의 데이터 ${d.document_count ?? "—"}종 연결`;
  if (["upload", "document_upload"].includes(log.action))
    return `앱 서류 ${d.document_count ?? "—"}장 접수`;
  if (d.before || d.after) {
    const before = (d.before ?? {}) as Record<string, unknown>,
      after = (d.after ?? {}) as Record<string, unknown>;
    const names: Record<string, string> = {
      message: "안내 문구",
      channel: "채널",
      step: "검토 단계",
      review_note: "검토 메모",
    };
    const present = (key: string, value: unknown) =>
      key === "channel"
        ? value === "kakao"
          ? "알림톡"
          : "문자"
        : key === "step"
          ? ["서류 확인", "정보 대조", "검토 결과", "완료"][Number(value)]
          : String(value ?? "없음");
    const changes = Object.keys(after).filter(
      (k) => JSON.stringify(before[k]) !== JSON.stringify(after[k]),
    );
    return changes.length
      ? changes
          .map(
            (k) =>
              `${names[k] ?? label(k)} · 변경 전 ${present(k, before[k])} → 변경 후 ${present(k, after[k])}`,
          )
          .join(" / ")
      : "검토 내용을 확인하고 저장했어요.";
  }
  if (log.action === "process_failed")
    return "처리가 완료되지 않은 서류를 확인해 주세요.";
  return "처리 기록을 저장했어요.";
}
export function HistoryScreen({ claimId }: { claimId: string }) {
  const logs = useResource<Log[]>(`/claims/${claimId}/logs`),
    claim = useResource<Claim>(`/claims/${claimId}`);
  const [filter, setFilter] = useState("all");
  if (!logs.data || !claim.data)
    return <LoadState error={logs.error ?? claim.error} />;
  const items = [...logs.data]
    .reverse()
    .filter(
      (l) =>
        filter === "all" ||
        (filter === "user" ? l.actor_type === "user" : l.actor_type !== "user"),
    );
  return (
    <>
      <PageTitle
        title="검토 이력"
        description={`${claim.data.customer_name} 고객 · ${claimId} · 처리 기록`}
      />
      <div className="filter-tabs" data-tour="history-filters">
        {[
          ["all", "전체"],
          ["user", "담당자"],
          ["ai", "시스템 · AI"],
        ].map(([v, t]) => (
          <button
            key={v}
            className={filter === v ? "selected" : ""}
            onClick={() => setFilter(v)}
          >
            {t}
          </button>
        ))}
        <Link href={`/workspace/review?claim=${claimId}`}>문서 검토로</Link>
      </div>
      <div className="panel" data-tour="history-records">
        <ol className="timeline">
          {items.map((log) => (
            <li key={log.id}>
              <time className="mono" dateTime={log.created_at}>
                {formatDateTime(log.created_at)}
              </time>
              <span className="timeline-icon">
                {log.actor_type === "user" ? (
                  <UserRound size={16} />
                ) : (
                  <Sparkles size={16} />
                )}
              </span>
              <div>
                <strong>{actionLabels[log.action] ?? log.action}</strong>
                <span className="muted">
                  {" "}
                  ·{" "}
                  {log.actor_type === "user"
                    ? "담당자"
                    : log.actor_type === "customer"
                      ? "고객"
                      : "가온 AI"}
                </span>
                <p>{formatDatesInText(logDetail(log))}</p>
              </div>
            </li>
          ))}
        </ol>
        {!items.length && (
          <p className="empty-message">해당하는 이력이 없어요.</p>
        )}
      </div>
    </>
  );
}

type ReviewSettings = {
  review_on_low_conf: boolean;
  review_on_not_in_source: boolean;
  review_on_format: boolean;
  auto_pass_threshold: number;
};
type Rule = {
  id: string;
  claim_type: string;
  doc_types: string[];
  conditions: Record<string, unknown>;
};
function RuleEditor({ rule, reload }: { rule: Rule; reload: () => void }) {
  const [editing, setEditing] = useState(false),
    [selected, setSelected] = useState(rule.doc_types),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  async function save() {
    setBusy(true);
    try {
      await api("/rules/required-docs", {
        method: "PUT",
        body: JSON.stringify([{ id: rule.id, doc_types: selected }]),
      });
      setEditing(false);
      setMessage("저장 · 재검사 완료");
      reload();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <tr>
      <td>
        <strong>
          {typeLabels[rule.claim_type] ??
            (rule.claim_type === "common" ? "공통" : rule.claim_type)}
        </strong>
      </td>
      <td>
        {editing ? (
          <div className="rule-choices">
            {Object.entries(docLabels)
              .filter(([v]) => v !== "other")
              .map(([v, t]) => (
                <label key={v}>
                  <input
                    type="checkbox"
                    checked={selected.includes(v)}
                    onChange={(e) =>
                      setSelected((s) =>
                        e.target.checked ? [...s, v] : s.filter((x) => x !== v),
                      )
                    }
                  />
                  {t}
                </label>
              ))}
          </div>
        ) : (
          rule.doc_types.map((t) => docLabels[t] ?? t).join(", ")
        )}
        {Object.keys(rule.conditions).length > 0 && (
          <small className="muted">
            조건:{" "}
            {Object.entries(rule.conditions)
              .map(
                ([k, v]) =>
                  `${({ waived_for_channels: "면제 접수 경로", is_proxy: "대리 청구 시", has_pharmacy_claim: "약제비 청구 시" } as Record<string, string>)[k] ?? k} ${Array.isArray(v) ? v.map((value) => (({ app: "앱 접수", silson24: "실손24" }) as Record<string, string>)[String(value)] ?? String(value)).join(", ") : v === true ? "적용" : String(v)}`,
              )
              .join(" · ")}
          </small>
        )}
      </td>
      <td>
        {editing ? (
          <>
            <button disabled={busy || !selected.length} onClick={save}>
              저장
            </button>
            <button disabled={busy} onClick={() => setEditing(false)}>
              취소
            </button>
          </>
        ) : (
          <button className="btn" onClick={() => setEditing(true)}>
            수정
          </button>
        )}
        {message && <small role="status">{message}</small>}
      </td>
    </tr>
  );
}
export function OperationsScreen() {
  const settings = useResource<ReviewSettings>("/settings"),
    rules = useResource<Rule[]>("/rules/required-docs"),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  if (!settings.data || !rules.data)
    return <LoadState error={settings.error ?? rules.error} />;
  const data = settings.data;
  async function change(key: string, value: boolean) {
    setBusy(true);
    try {
      await api("/settings", {
        method: "PATCH",
        body: JSON.stringify({ [key]: value }),
      });
      settings.reload();
      setMessage(
        "설정을 저장하고 현재 청구를 재검사했어요. 이후 검토에도 적용됩니다.",
      );
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        title="운영 관리"
        description="확인이 필요한 조건과 청구 유형별 필수 서류를 정해요."
      />
      <section className="panel settings-panel">
        <h2>
          <SlidersHorizontal size={18} />
          담당자 확인 기준
        </h2>
        <p className="muted small">
          조건을 켜면 해당 항목을 담당자 확인 대상으로 보냅니다.
        </p>
        {(
          [
            [
              "review_on_low_conf",
              "모델 신뢰도 낮음",
              "문서에서 읽은 값의 신뢰도가 낮은 항목",
            ],
            [
              "review_on_not_in_source",
              "원문 불일치",
              "서류 원문에서 값을 찾지 못하거나 세분류가 빠진 항목",
            ],
            [
              "review_on_format",
              "형식 오류",
              "날짜·질병코드·금액 형식 검증에 실패한 항목",
            ],
          ] as const
        ).map(([key, title, description]) => (
          <label key={key} className="setting-row">
            <span>
              <strong>{title}</strong>
              <small>{description}</small>
            </span>
            <input
              type="checkbox"
              role="switch"
              aria-label={title}
              checked={data[key]}
              disabled={busy}
              onChange={(e) => change(key, e.target.checked)}
            />
          </label>
        ))}
        {message && <p role="status">{message}</p>}
      </section>
      <section className="panel required-panel">
        <div className="panel-heading">
          <h2>청구 유형별 필수 서류</h2>
          <small>저장 시 규칙 재검사</small>
        </div>
        <table className="work-table">
          <thead>
            <tr>
              <th>청구 유형</th>
              <th>필수 서류 · 적용 조건</th>
              <th>관리</th>
            </tr>
          </thead>
          <tbody>
            {rules.data.map((rule) => (
              <RuleEditor
                key={JSON.stringify(rule)}
                rule={rule}
                reload={rules.reload}
              />
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
