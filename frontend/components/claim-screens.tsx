"use client";
import Link from "next/link";
import { formatDate, formatDateTime, formatDatesInText } from "@/lib/dates";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect, useRef, Fragment } from "react";
import {
  CircleCheck,
  CircleX,
  TriangleAlert,
  ArrowRight,
  ArrowLeft,
  Upload,
  ScanLine,
  Info,
  ZoomIn,
  ZoomOut,
  X,
  Pencil,
  Columns2,
  Check,
} from "lucide-react";
import {
  api,
  Claim,
  ClaimList,
  docLabels,
  typeLabels,
  display,
  label,
  FieldRow,
  ComparisonCell,
  confidencePercent,
} from "@/lib/workspace";
import { Original } from "./review-screen";
import { workspacePages } from "@/lib/navigation";
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
  const page = Math.max(1, Number(params.get("page") ?? 1));
  function openClaim(id: string) {
    // URL은 필터/페이지를, 세션 메모리는 화면의 스크롤 위치를 복원한다.
    try {
      sessionStorage.setItem(
        "inbox-return",
        JSON.stringify({
          url: window.location.pathname + window.location.search,
          scroll: window.scrollY,
        }),
      );
    } catch {}
    router.push("/workspace/detail?claim=" + id);
  }
  useEffect(() => {
    if (!data) return;
    try {
      const saved = JSON.parse(
        sessionStorage.getItem("inbox-return") ?? "null",
      );
      if (saved?.url === window.location.pathname + window.location.search)
        requestAnimationFrame(() => window.scrollTo(0, saved.scroll));
    } catch {}
  }, [data]);
  return (
    <>
      <PageTitle
        title="청구 검토함"
        description="보완 요청과 검토가 필요한 청구부터 확인하세요."
      />
      <div
        className="filter-tabs"
        aria-label="상태 필터"
        data-tour="inbox-filters"
      >
        {[
          ["", "전체", "total"],
          ["pending", "처리 전", "pending"],
          ["needs_review", "검토 필요", "needs_review"],
          ["supplement", "보완 요청", "supplement"],
          ["auto_pass", "자동 통과", "auto_pass"],
          ["processing", "처리 중", "processing"],
          ["ready_review", "이관 가능", "ready_review"],
          ["to_payment_review", "지급 심사", "to_payment_review"],
        ]
          .filter(
            ([, , key]) =>
              key === "total" || !data || (data.counts[key] ?? 0) > 0,
          )
          .map(([value, text, key]) => (
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
        <div className="panel table-scroll" data-tour="inbox-table">
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
              {data.items.slice((page - 1) * 10, page * 10).map((c) => (
                <tr
                  key={c.id}
                  tabIndex={0}
                  role="link"
                  aria-label={`${c.customer_name} ${c.id} 청구 상세`}
                  onClick={() => openClaim(c.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") openClaim(c.id);
                  }}
                >
                  <td className="mono" title={c.id}>
                    {c.id}
                  </td>
                  <td>
                    <span className="inbox-customer">
                      <strong>{c.customer_name}</strong>{" "}
                      <small>{formatDate(c.customer?.birth_date)}</small>
                    </span>
                    {c.development_origin && (
                      <span title={c.development_origin}>
                        <Info size={13} aria-label="개발 데이터 출처" />
                      </span>
                    )}
                  </td>
                  <td
                    title={c.claim_types
                      .map((t) => typeLabels[t] ?? t)
                      .join(" · ")}
                  >
                    {c.claim_types.map((t) => typeLabels[t] ?? t).join(" · ")}
                  </td>
                  <td
                    className="mono muted"
                    title={formatDateTime(c.received_at, "Asia/Seoul")}
                  >
                    {formatDateTime(c.received_at, "Asia/Seoul")}
                  </td>
                  <td>
                    <Status status={c.status} />
                  </td>
                  <td className="muted">
                    {c.open_issue_count
                      ? `확인할 사항 ${c.open_issue_count}건`
                      : c.submitted_count
                        ? c.issues.some(
                            (i) => i.status === "open" && i.kind === "info",
                          )
                          ? "서류 확인 완료 · 안내 확인"
                          : "지급 심사 이관 가능"
                        : "서류 접수 대기"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination" data-tour="inbox-sort">
            <span>보완 요청·검토 필요 우선, 최근 접수순</span>
            <button
              className="btn sm"
              disabled={page <= 1}
              onClick={() =>
                router.push(
                  "/workspace?" +
                    new URLSearchParams({
                      q,
                      status: filter,
                      page: String(page - 1),
                    }),
                )
              }
            >
              이전
            </button>
            <span>
              {page} / {Math.max(1, Math.ceil(data.items.length / 10))}
            </span>
            <button
              className="btn sm"
              disabled={page * 10 >= data.items.length}
              onClick={() =>
                router.push(
                  "/workspace?" +
                    new URLSearchParams({
                      q,
                      status: filter,
                      page: String(page + 1),
                    }),
                )
              }
            >
              다음
            </button>
          </div>
          {!data.items.length && (
            <p className="empty-message">조건에 맞는 청구가 없어요.</p>
          )}
        </div>
      )}
    </>
  );
}

/** 청구를 지정하지 않은 업무 화면은 검색 전 목록/API 조회를 만들지 않는다. */
export function ClaimPicker({ section }: { section: string }) {
  const q = (useSearchParams().get("q") ?? "").trim();
  const title =
    workspacePages.find((page) => page.slug === section)?.title ?? "청구 검색";
  return (
    <>
      <PageTitle
        title={title}
        description="고객 이름, 고객 ID 또는 청구번호로 검색해 주세요."
      />
      {q ? (
        <ClaimSearchResults section={section} q={q} />
      ) : (
        <div className="panel empty-message">
          검색한 뒤 청구를 선택하면 업무를 시작할 수 있어요.
        </div>
      )}
    </>
  );
}

/** 검색어가 있을 때만 마운트해 미검색 상태에서 고객 목록을 불러오지 않는다. */
function ClaimSearchResults({ section, q }: { section: string; q: string }) {
  const { data, error } = useResource<ClaimList>(
    `/claims?q=${encodeURIComponent(q)}`,
  );
  return (
    <>
      {!data ? (
        <LoadState error={error} />
      ) : (
        <div className="panel">
          {!data.items.length && (
            <p className="empty-message">검색 조건에 맞는 청구가 없어요.</p>
          )}
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
  const params = useSearchParams();
  const requestedIssue = params.get("issue");
  const resource = useResource<Claim>("/claims/" + claimId);
  const { data: c, error } = resource;
  const [localStep, setStep] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [preview, setPreview] = useState<ComparisonCell | null>(null);
  const [zoom, setZoom] = useState(100);
  const previewRef = useRef<HTMLDivElement>(null);
  const [returnUrl, setReturnUrl] = useState("/workspace");
  const [note, setNote] = useState<string | null>(null);
  const step = localStep ?? (requestedIssue ? 2 : (c?.step ?? 0));
  useEffect(() => {
    // 챗봇 근거에서 이동한 이슈만 데이터 로드 후 화면 가운데로 보여준다.
    if (c && requestedIssue)
      document
        .getElementById(`issue-${requestedIssue}`)
        ?.scrollIntoView({ block: "center" });
  }, [c, requestedIssue]);
  useEffect(() => {
    try {
      const saved = JSON.parse(
        sessionStorage.getItem("inbox-return") ?? "null",
      );
      if (saved?.url?.startsWith("/workspace?"))
        requestAnimationFrame(() => setReturnUrl(saved.url));
    } catch {}
    const listener = (e: Event) => setStep((e as CustomEvent<number>).detail);
    window.addEventListener("tour-detail-step", listener);
    return () => window.removeEventListener("tour-detail-step", listener);
  }, []);
  useEffect(() => {
    if (!preview) return;
    // 원본 창 안에서 키보드 초점을 유지하고 닫을 때 이전 값 버튼으로 돌려준다.
    const previous = document.activeElement as HTMLElement | null;
    const frame = requestAnimationFrame(() =>
      previewRef.current?.querySelector<HTMLButtonElement>("button")?.focus(),
    );
    const keys = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPreview(null);
      if (e.key === "Tab") {
        const buttons = Array.from(
          previewRef.current?.querySelectorAll<HTMLElement>(
            "button:not(:disabled), [tabindex='0']",
          ) ?? [],
        );
        const first = buttons[0],
          last = buttons[buttons.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener("keydown", keys);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("keydown", keys);
      previous?.focus();
    };
  }, [preview]);
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
      const uploaded = await api<{ job_id: string | null }>(
        "/claims/" + claimId + "/documents",
        {
          method: "POST",
          body: form,
        },
      );
      // 보완 회신은 자동 재검토가 끝난 뒤 화면을 갱신해 이전 누락 상태가 남지 않게 한다.
      if (uploaded.job_id) {
        setMessage("보완 서류를 검토하고 있어요.");
        let finished = false;
        for (let attempt = 0; attempt < 120; attempt++) {
          const status = await api<{ state: string }>(
            `/claims/${claimId}/process/status?job_id=${uploaded.job_id}`,
          );
          if (status.state === "failed")
            throw new Error("보완 서류 처리 결과를 확인해 주세요.");
          if (status.state === "done") {
            finished = true;
            break;
          }
          await new Promise((resolve) => setTimeout(resolve, 1500));
        }
        if (!finished)
          throw new Error(
            "검토가 진행 중이에요. 잠시 후 화면을 새로고침해 주세요.",
          );
      }
      resource.reload();
      setMessage(
        uploaded.job_id
          ? "보완 서류를 접수하고 재검토했어요."
          : "서류를 첨부했어요.",
      );
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!c) return <LoadState error={error} />;
  const open = c.issues.filter((i) => i.status === "open" && i.kind !== "info");
  return (
    <>
      <Link className="back-home" href={returnUrl}>
        ← 청구 검토함
      </Link>
      <PageTitle
        title={`${c.customer_name} 고객 · 청구 상세`}
        description={`${c.id}  ·  첨부 서류 ${c.submitted_count}개  ·  ${formatDate(c.customer?.birth_date)}`}
      />
      <div className="detail-meta">
        {c.policy?.contract_date && (
          <span>계약일 {formatDate(c.policy.contract_date)}</span>
        )}
        {c.development_origin && (
          <span title={c.development_origin}>
            <Info size={13} aria-label="개발 데이터 출처" />
          </span>
        )}
        <Status status={c.status} />
        <span>{c.policy?.product_name}</span>
        <span>
          보장 {formatDate(c.policy?.coverage_start)} ~{" "}
          {formatDate(c.policy?.coverage_end)}
        </span>
      </div>
      <div className="panel stepper" data-tour="detail-stepper">
        {["서류 확인", "정보 대조", "검토 결과", "완료"].map((text, i) => (
          <Fragment key={text}>
            {i > 0 && (
              <span
                className={`step-connector ${i <= step ? "done" : ""}`}
                aria-hidden="true"
              />
            )}
            <button
              onClick={() => move(i)}
              aria-current={step === i ? "step" : undefined}
              className={step === i ? "active" : i < step ? "done" : ""}
            >
              <span>
                {i < step ? <Check size={14} aria-hidden="true" /> : i + 1}
              </span>
              {text}
            </button>
          </Fragment>
        ))}
      </div>
      {message && (
        <p className="action-message" role="status">
          {message}
        </p>
      )}
      {step === 0 && (
        <div className="detail-grid">
          <section className="panel" data-tour="detail-documents">
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
        <>
          <section className="panel comparison-card" data-tour="detail-compare">
            <h2>
              서류 간 정보 대조{" "}
              <small>
                대조 {c.comparisons.length}건 · 일치{" "}
                {c.comparisons.filter((r) => r.result === "match").length} ·
                불일치{" "}
                {c.comparisons.filter((r) => r.result === "mismatch").length} ·
                안내 {c.comparisons.filter((r) => r.result === "info").length}
                {c.comparisons.some((r) => r.result === "na") &&
                  ` · 해당 없음 ${c.comparisons.filter((r) => r.result === "na").length}`}
              </small>
            </h2>
            {!c.comparisons.length ? (
              <p className="muted">
                대조할 서류 쌍이 없어요. 서류가 접수되면 확인할 수 있어요.
              </p>
            ) : (
              <div className="comparison-table-scroll">
                <table className="work-table comparison-table">
                  <thead>
                    <tr>
                      <th>대조 항목</th>
                      <th>서류 A</th>
                      <th>서류 B</th>
                      <th>결과</th>
                    </tr>
                  </thead>
                  <tbody>
                    {c.comparisons.map((row, index) => (
                      <tr key={index}>
                        <td>{row.title}</td>
                        {[row.a, row.b].map((cell, n) => (
                          <td key={n}>
                            <button
                              className="field-link"
                              disabled={!cell.document_id}
                              onClick={() => {
                                setPreview(cell);
                                setZoom(100);
                              }}
                            >
                              <strong>{cell.doc_name}</strong>
                              <span>{formatDatesInText(cell.value)}</span>
                            </button>
                          </td>
                        ))}
                        <td>
                          <span
                            className={
                              row.result === "match"
                                ? "good plain-state"
                                : row.result === "mismatch"
                                  ? "warn plain-state"
                                  : "muted plain-state"
                            }
                          >
                            {row.result === "match" ? (
                              <CircleCheck size={15} />
                            ) : row.result === "mismatch" ? (
                              <TriangleAlert size={15} />
                            ) : (
                              <Info size={15} />
                            )}
                            {
                              {
                                match: "일치",
                                mismatch: "불일치",
                                info: "안내",
                                na: "해당 없음",
                              }[row.result]
                            }
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          <Link
            className="btn comparison-original-link"
            href={`/workspace/review?claim=${c.id}`}
          >
            <ScanLine size={16} />
            문서 분석·검토에서 원본으로 확인
          </Link>
        </>
      )}
      {step === 2 && (
        <div className="detail-results">
          <section className="panel" data-tour="detail-fields">
            <h2>
              정규화 결과{" "}
              <small>
                {c.fields.filter((f) => !f.key.startsWith("items[")).length}개
                항목
              </small>
            </h2>
            <table className="work-table normalized-compact">
              <thead>
                <tr>
                  <th>항목</th>
                  <th>값</th>
                  <th>출처</th>
                  <th>신뢰도</th>
                </tr>
              </thead>
              <tbody>
                {c.fields
                  .filter((f) => !f.key.startsWith("items["))
                  .map((f) => (
                    <NormalizedRow
                      key={f.id}
                      field={f}
                      readOnly={readOnly}
                      done={resource.reload}
                      show={() => {
                        setPreview({
                          document_id: f.document_id,
                          doc_name: docLabels[f.doc_type],
                          key: f.key,
                          value: display(f),
                        });
                        setZoom(100);
                      }}
                    />
                  ))}
              </tbody>
            </table>
            {c.documents.map((d) => {
              const fields = c.fields.filter(
                (f) => f.document_id === d.id && f.key.startsWith("items["),
              );
              const indexes = [
                ...new Set(
                  fields.map((f) => f.key.match(/items\[(\d+)\]/)?.[1]),
                ),
              ];
              return (
                indexes.length > 0 && (
                  <div key={d.id} className="item-table">
                    <h3>
                      {docLabels[d.doc_type]} 품목 {indexes.length}건
                    </h3>
                    <table className="work-table normalized-compact">
                      <thead>
                        <tr>
                          {[
                            "품명",
                            "1회량",
                            "일일 횟수",
                            "일수",
                            "금액",
                            "급여 구분",
                          ].map((h) => (
                            <th key={h}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {indexes.map((index) => (
                          <tr key={index}>
                            {[
                              ["drug_name", "name"],
                              ["dose"],
                              ["per_day"],
                              ["days"],
                              ["amount"],
                              ["covered"],
                            ].map((keys, n) => (
                              <td key={n}>
                                {(() => {
                                  const f = fields.find((f) =>
                                    keys.some(
                                      (key) =>
                                        f.key === `items[${index}].${key}`,
                                    ),
                                  );
                                  return f ? display(f) : "—";
                                })()}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              );
            })}
          </section>
          <section className="panel" data-tour="detail-issues">
            <h2>
              확인 사항 <small>{c.display_issues.length}건</small>
            </h2>
            <ul className="compact-issues">
              {c.display_issues.map((i) => (
                <li key={i.id} id={`issue-${i.id}`}>
                  <Info
                    size={17}
                    className={i.kind === "info" ? "muted" : "warning"}
                  />
                  <div>
                    <strong title={i.title}>{i.title}</strong>
                    <p title={formatDatesInText(i.detail)}>
                      {formatDatesInText(i.detail)}
                    </p>
                  </div>
                  <Link
                    className="icon-button"
                    title="원본 비교"
                    aria-label={`${i.title} 원본 비교`}
                    href={`/workspace/review?claim=${c.id}&issue=${i.id}`}
                  >
                    <Columns2 size={17} />
                  </Link>
                  {!readOnly && i.kind !== "missing" && (
                    <button
                      className="icon-button"
                      title="확인"
                      aria-label={`${i.title} 확인`}
                      onClick={async () => {
                        try {
                          for (const id of [i.id, ...(i.related_ids ?? [])])
                            await api(`/issues/${id}/resolve`, {
                              method: "POST",
                            });
                          resource.reload();
                        } catch (e) {
                          setMessage((e as Error).message);
                        }
                      }}
                    >
                      <Check size={17} />
                    </button>
                  )}
                </li>
              ))}
            </ul>
            {!c.display_issues.length && (
              <p className="good">추가로 확인할 사항이 없어요.</p>
            )}
          </section>
          <section className="panel">
            <h2>담당자 메모</h2>
            <textarea
              className="work-textarea"
              aria-label="담당자 메모"
              value={note ?? c.review_note ?? ""}
              onChange={(e) => setNote(e.target.value)}
              readOnly={readOnly}
            />
            {!readOnly && (
              <button
                className="btn"
                onClick={async () => {
                  try {
                    await api(`/claims/${c.id}`, {
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
      {preview && (
        <div
          className="document-modal"
          role="dialog"
          aria-modal="true"
          aria-label="서류 원본"
          ref={previewRef}
        >
          <div className="panel">
            <div className="viewer-toolbar">
              <strong>{preview.doc_name} 원본</strong>
              <button
                className="icon-button"
                aria-label="축소"
                onClick={() => setZoom(Math.max(50, zoom - 10))}
              >
                <ZoomOut />
              </button>
              <span>{zoom}%</span>
              <button
                className="icon-button"
                aria-label="확대"
                onClick={() => setZoom(Math.min(200, zoom + 10))}
              >
                <ZoomIn />
              </button>
              <button
                className="icon-button"
                aria-label="원본 닫기"
                onClick={() => setPreview(null)}
              >
                <X />
              </button>
            </div>
            {!c.fields.some(
              (f) =>
                f.document_id === preview.document_id &&
                f.key === preview.key &&
                f.bbox,
            ) && <small>위치 정보 없음</small>}
            <Original
              doc={c.documents.find((d) => d.id === preview.document_id)!}
              fields={c.fields.filter(
                (f) =>
                  f.document_id === preview.document_id &&
                  !!c.fields.find(
                    (target) =>
                      target.document_id === preview.document_id &&
                      target.key === preview.key,
                  )?.bbox,
              )}
              selected={
                c.fields.find(
                  (f) =>
                    f.document_id === preview.document_id &&
                    f.key === preview.key,
                )?.id ?? null
              }
              select={() => {}}
              zoom={zoom}
              focusKeys={[preview.key]}
              allowReferencePosition={false}
            />
          </div>
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

function NormalizedRow({
  field: f,
  readOnly,
  done,
  show,
}: {
  field: FieldRow;
  readOnly: boolean;
  done: () => void;
  show: () => void;
}) {
  const [editing, setEditing] = useState(false),
    [value, setValue] = useState(f.display_value),
    [error, setError] = useState("");
  const needs = !f.confirmed_by && f.review_reasons.length > 0;
  return (
    <tr className={needs ? "review-needed" : ""}>
      <td title={label(f.key)}>
        <button className="field-link" onClick={show} title="원본 보기">
          {label(f.key)}
        </button>
      </td>
      <td title={display(f)}>
        {editing ? (
          <>
            <input
              aria-label={`${label(f.key)} 확정값`}
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
            <button
              onClick={async () => {
                try {
                  await api(`/fields/${f.id}`, {
                    method: "PATCH",
                    body: JSON.stringify({ confirmed_value: value }),
                  });
                  setEditing(false);
                  done();
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              저장
            </button>
            <button onClick={() => setEditing(false)}>취소</button>
          </>
        ) : (
          <>
            {display(f)}
            {!readOnly && (
              <button
                className="icon-button field-edit"
                aria-label={`${label(f.key)} 수정`}
                title="수정"
                onClick={() => setEditing(true)}
              >
                <Pencil size={13} />
              </button>
            )}
          </>
        )}
        {error && <small role="alert">{error}</small>}
      </td>
      <td>
        {f.method === "data" ? "실손24" : docLabels[f.doc_type]}
        <small>
          {f.method === "data" ? "" : f.method === "ocr" ? "OCR" : "Parse"}
        </small>
      </td>
      <td
        title={
          f.extract_conf === "low"
            ? "추출 신뢰도 낮음 · 숫자 점수 미제공"
            : "숫자 점수 미제공"
        }
      >
        {confidencePercent(f)}
      </td>
    </tr>
  );
}
