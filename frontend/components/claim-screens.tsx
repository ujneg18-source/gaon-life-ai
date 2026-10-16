"use client";
import Link from "next/link";
import { formatDate, formatDateTime } from "@/lib/dates";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import {
  CircleCheck,
  CircleX,
  ArrowRight,
  ArrowLeft,
  Upload,
  ScanLine,
} from "lucide-react";
import {
  api,
  Claim,
  ClaimList,
  docLabels,
  typeLabels,
  display,
  label,
} from "@/lib/workspace";
import { useResource, Status, PageTitle, LoadState } from "./workspace-ui";

export function Inbox() {
  const params = useSearchParams();
  const router = useRouter();
  const q = params.get("q") ?? "";
  const filter = params.get("status") ?? "";
  const resource = useResource<ClaimList>(
    "/claims?" +
      new URLSearchParams({ q, ...(filter ? { status: filter } : {}) }),
  );
  const { data, error } = resource;
  return (
    <>
      <PageTitle
        title="청구 검토함"
        description="AI가 먼저 읽고, 사람이 봐야 할 것만 위로 올렸어요."
      />
      <div className="filter-tabs" aria-label="상태 필터">
        {[
          ["", "전체", "total"],
          ["pending", "처리 전", "pending"],
          ["needs_review", "검토 필요", "needs_review"],
          ["supplement", "보완 요청", "supplement"],
          ["auto_pass", "자동 통과", "auto_pass"],
          ["processing", "처리 중", "processing"],
        ].map(([value, text, key]) => (
          <button
            key={key}
            className={value === filter ? "selected" : ""}
            onClick={() =>
              router.push(
                "/workspace?" +
                  new URLSearchParams({
                    q,
                    ...(value ? { status: value } : {}),
                  }),
              )
            }
          >
            {text} <b>{data?.counts[key] ?? "—"}</b>
          </button>
        ))}
      </div>
      {!data ? (
        <LoadState error={error} />
      ) : (
        <div className="panel table-scroll">
          <table className="work-table inbox-table">
            <thead>
              <tr>
                {[
                  "청구번호",
                  "고객",
                  "청구 유형",
                  "접수",
                  "상태",
                  "AI 검토 결과",
                ].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr
                  key={c.id}
                  tabIndex={0}
                  role="link"
                  aria-label={`${c.customer_name} ${c.id} 청구 상세`}
                  onClick={() => router.push("/workspace/detail?claim=" + c.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter")
                      router.push("/workspace/detail?claim=" + c.id);
                  }}
                >
                  <td className="mono">{c.id}</td>
                  <td>
                    <strong>{c.customer_name}</strong>
                    <small>{formatDate(c.customer?.birth_date)}</small>
                  </td>
                  <td>
                    {c.claim_types.map((t) => typeLabels[t] ?? t).join(" · ")}
                  </td>
                  <td className="mono muted">
                    {formatDateTime(c.received_at, "Asia/Seoul")}
                  </td>
                  <td>
                    <Status status={c.status} />
                  </td>
                  <td className="muted">
                    {c.open_issue_count
                      ? `확인할 사항 ${c.open_issue_count}건`
                      : c.submitted_count
                        ? "열린 이슈 없음"
                        : "서류 접수 대기"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data.items.length && (
            <p className="empty-message">조건에 맞는 청구가 없어요.</p>
          )}
        </div>
      )}
    </>
  );
}

export function ClaimPicker({ section }: { section: string }) {
  const { data, error } = useResource<ClaimList>("/claims");
  return (
    <>
      <PageTitle
        title="검토할 청구 선택"
        description="고객과 청구번호를 확인한 뒤 업무를 이어가세요."
      />
      {!data ? (
        <LoadState error={error} />
      ) : (
        <div className="panel">
          <ul className="claim-picker">
            {data.items.map((c) => (
              <li key={c.id}>
                <Link href={`/workspace/${section}?claim=${c.id}`}>
                  <strong>{c.customer_name}</strong>
                  <span>{formatDate(c.customer?.birth_date)}</span>
                  <span className="mono">{c.id}</span>
                  <Status status={c.status} />
                  <ArrowRight size={16} />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}

export function ClaimDetail({
  claimId,
  readOnly,
}: {
  claimId: string;
  readOnly: boolean;
}) {
  const resource = useResource<Claim>("/claims/" + claimId);
  const { data: c, error } = resource;
  const [localStep, setStep] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const step = localStep ?? c?.step ?? 0;
  async function move(value: number) {
    setMessage("");
    if (!readOnly) {
      try {
        await api("/claims/" + claimId, {
          method: "PATCH",
          body: JSON.stringify({ step: value }),
        });
      } catch (e) {
        setMessage((e as Error).message);
        return;
      }
    }
    setStep(value);
  }
  async function submit() {
    setBusy(true);
    try {
      await api("/claims/" + claimId + "/submit", { method: "POST" });
      resource.reload();
      setMessage("지급 심사로 전달했어요.");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(files: FileList | null) {
    if (!files) return;
    setBusy(true);
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    try {
      await api("/claims/" + claimId + "/documents", {
        method: "POST",
        body: form,
      });
      resource.reload();
      setMessage("서류를 첨부했어요.");
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!c) return <LoadState error={error} />;
  const open = c.issues.filter((i) => i.status === "open");
  return (
    <>
      <PageTitle
        title={`${c.customer_name} 고객 · 청구 상세`}
        description={`${c.id}  ·  첨부 서류 ${c.submitted_count}개  ·  ${formatDate(c.customer?.birth_date)}`}
      />
      <div className="detail-meta">
        <Status status={c.status} />
        <span>{c.policy?.product_name}</span>
        <span>
          보장 {formatDate(c.policy?.coverage_start)} ~{" "}
          {formatDate(c.policy?.coverage_end)}
        </span>
      </div>
      <div className="panel stepper">
        {["서류 확인", "정보 대조", "검토 결과", "완료"].map((text, i) => (
          <button
            key={text}
            onClick={() => move(i)}
            aria-current={step === i ? "step" : undefined}
            className={step === i ? "active" : ""}
          >
            <span>{i + 1}</span>
            {text}
          </button>
        ))}
      </div>
      {message && (
        <p className="action-message" role="status">
          {message}
        </p>
      )}
      {step === 0 && (
        <div className="detail-grid">
          <section className="panel">
            <h2>
              제출 서류{" "}
              <small>
                {c.submitted_count} / {c.required_count}
              </small>
            </h2>
            <ul className="document-checklist">
              {[
                ...new Set([
                  ...c.required,
                  ...c.documents.map((d) => d.doc_type),
                ]),
              ].map((type) => {
                const docs = c.documents.filter((d) => d.doc_type === type);
                return (
                  <li key={type}>
                    {docs.length ? (
                      <CircleCheck className="good" size={18} />
                    ) : (
                      <CircleX className="bad" size={18} />
                    )}
                    <span>{docLabels[type] ?? type}</span>
                    <small>
                      {docs.length
                        ? docs[0].source === "silson24"
                          ? "실손24 데이터"
                          : "앱 업로드 · 이미지"
                        : "미제출"}
                    </small>
                    {docs.length > 0 && (
                      <Link
                        className="text-link"
                        href={`/workspace/review?claim=${c.id}&doc=${docs[0].id}`}
                      >
                        보기
                      </Link>
                    )}
                  </li>
                );
              })}
            </ul>
            {!readOnly && (
              <div className="upload-actions">
                <label className="btn">
                  <Upload size={16} />
                  서류 추가
                  <input
                    aria-label="청구 서류 추가"
                    type="file"
                    multiple
                    accept=".png,.jpg,.jpeg,.pdf"
                    onChange={(e) => upload(e.target.files)}
                    disabled={busy}
                  />
                </label>
                <button
                  className="btn"
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    try {
                      await api("/claims/" + c.id + "/silson24", {
                        method: "POST",
                      });
                      resource.reload();
                    } catch (e) {
                      setMessage((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  실손24 모의 수신
                </button>
                <button
                  className="btn"
                  disabled={busy || !c.documents.length}
                  onClick={async () => {
                    setBusy(true);
                    try {
                      await api("/claims/" + c.id + "/process", {
                        method: "POST",
                      });
                      setMessage(
                        "분석을 시작했어요. 잠시 후 새로고침해 주세요.",
                      );
                    } catch (e) {
                      setMessage((e as Error).message);
                    } finally {
                      setBusy(false);
                      resource.reload();
                    }
                  }}
                >
                  <ScanLine size={16} />
                  분석 실행
                </button>
                <button className="btn sm" onClick={resource.reload}>
                  새로고침
                </button>
              </div>
            )}
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>추출된 청구 정보</h2>
              <Link className="btn sm" href={`/workspace/review?claim=${c.id}`}>
                직접 수정
              </Link>
            </div>
            <dl className="info-list">
              <dt>청구 유형</dt>
              <dd>
                {c.claim_types.map((t) => typeLabels[t] ?? t).join(" · ")}
              </dd>
              {[
                "diagnosis_code",
                "diagnosis_date",
                "admit_date",
                "discharge_date",
              ].map((key) => {
                const f = c.fields.find((row) => row.key === key);
                return (
                  <div className="info-row" key={key}>
                    <dt>{label(key)}</dt>
                    <dd>
                      {f ? display(f) : "—"}{" "}
                      {f?.kcd_name && <small>{f.kcd_name}</small>}
                    </dd>
                  </div>
                );
              })}
              <dt>가입 특약</dt>
              <dd>
                {c.policy?.riders.map((t) => typeLabels[t] ?? t).join(" · ")}
              </dd>
              <dt>접수 경로</dt>
              <dd>
                {c.channel
                  .map((x) => (x === "app" ? "가온생명 앱" : "실손24"))
                  .join(" + ")}
              </dd>
            </dl>
            <p className="muted helper-text">
              원문과 다르면 직접 수정할 수 있어요. 수정 내역은 검토 이력에
              남아요.
            </p>
          </section>
        </div>
      )}
      {step === 1 && (
        <section className="panel table-scroll">
          <h2>서류 간 정보 대조</h2>
          <table className="work-table">
            <thead>
              <tr>
                <th>대조 항목</th>
                <th>서류 A</th>
                <th>서류 B</th>
                <th>확인</th>
              </tr>
            </thead>
            <tbody>
              {c.issues
                .filter((i) => i.kind === "mismatch")
                .map((i) => (
                  <tr key={i.id}>
                    <td>{i.title}</td>
                    {[0, 1].map((index) => (
                      <td key={index}>
                        {i.doc_ids[index] ? (
                          <>
                            <strong>
                              {
                                docLabels[
                                  c.documents.find(
                                    (d) => d.id === i.doc_ids[index],
                                  )?.doc_type ?? ""
                                ]
                              }
                            </strong>
                            <small>
                              {c.fields
                                .filter(
                                  (f) =>
                                    f.document_id === i.doc_ids[index] &&
                                    i.field_keys.includes(f.key),
                                )
                                .map(display)
                                .join(" · ")}
                            </small>
                          </>
                        ) : (
                          i.detail
                        )}
                      </td>
                    ))}
                    <td>
                      <Link
                        className="btn sm"
                        href={`/workspace/review?claim=${c.id}&issue=${i.id}`}
                      >
                        원본 비교
                      </Link>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </section>
      )}
      {step === 2 && (
        <div className="detail-grid">
          <section className="panel">
            <h2>남은 확인 사항 {open.length}건</h2>
            <ul className="issue-summary">
              {open.map((i) => (
                <li key={i.id}>
                  <strong>{i.title}</strong>
                  <p>{i.detail}</p>
                  <Link
                    className="text-link"
                    href={`/workspace/review?claim=${c.id}&issue=${i.id}`}
                  >
                    검토하기 <ArrowRight size={14} />
                  </Link>
                </li>
              ))}
            </ul>
            {!open.length && <p className="good">열린 이슈가 없어요.</p>}
          </section>
          <section className="panel">
            <h2>담당자 메모</h2>
            <textarea
              className="work-textarea"
              aria-label="담당자 메모"
              value={note ?? c.review_note ?? ""}
              onChange={(e) => setNote(e.target.value)}
              readOnly={readOnly}
              placeholder="확인한 내용과 다음 조치를 남겨 주세요."
            />
            {!readOnly && (
              <button
                className="btn"
                onClick={async () => {
                  try {
                    await api("/claims/" + c.id, {
                      method: "PATCH",
                      body: JSON.stringify({
                        review_note: note ?? c.review_note ?? "",
                      }),
                    });
                    setMessage("메모를 저장했어요.");
                  } catch (e) {
                    setMessage((e as Error).message);
                  }
                }}
              >
                메모 저장
              </button>
            )}
          </section>
        </div>
      )}
      {step === 3 && (
        <section className="panel completion-panel">
          <h2>검토 내용을 확인하고 다음 단계로 이동하세요.</h2>
          <p>
            남은 확인 {open.length}건 · 제출 {c.submitted_count} / 필요{" "}
            {c.required_count}
          </p>
          <div className="row-actions">
            <Link className="btn" href={`/workspace/supplement?claim=${c.id}`}>
              보완 요청 작성
            </Link>
            <button
              className="btn primary"
              disabled={
                readOnly ||
                busy ||
                open.length > 0 ||
                !c.documents.length ||
                c.documents.some((d) => d.status !== "extracted")
              }
              onClick={submit}
            >
              지급 심사로 보내기
            </button>
          </div>
          {open.length > 0 && (
            <p className="muted">
              열린 이슈를 모두 확인한 뒤 지급 심사로 보낼 수 있어요.
            </p>
          )}
        </section>
      )}
      <div className="step-actions">
        <button
          className="btn"
          disabled={step === 0}
          onClick={() => move(step - 1)}
        >
          <ArrowLeft size={16} />
          이전
        </button>
        <button
          className="btn primary"
          disabled={step === 3}
          onClick={() => move(step + 1)}
        >
          다음:{" "}
          {
            ["서류 확인", "정보 대조", "검토 결과", "완료"][
              Math.min(step + 1, 3)
            ]
          }
          <ArrowRight size={16} />
        </button>
      </div>
    </>
  );
}
