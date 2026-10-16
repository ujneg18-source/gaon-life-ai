"use client";
import Link from "next/link";
import { formatDatesInText } from "@/lib/dates";
import { useState, useRef, useEffect, useMemo } from "react";
import { referenceForm } from "@/lib/reference-form";
import { useSearchParams, useRouter } from "next/navigation";
import {
  ZoomIn,
  ZoomOut,
  Columns2,
  CircleCheck,
  TriangleAlert,
  CircleX,
  Pencil,
  X,
  Info,
} from "lucide-react";
import {
  api,
  Claim,
  Doc,
  FieldRow,
  Issue,
  docLabels,
  display,
  label,
  confidenceDisplay,
  reason,
} from "@/lib/workspace";
import { useResource, LoadState, PageTitle } from "./workspace-ui";

/** 실제 이미지와 정규화 좌표를 동일 비율로 확대한다. 좌표가 없으면 박스를 지어내지 않는다. */
export function Original({
  doc,
  fields,
  selected,
  select,
  zoom,
  focusKeys,
  allowReferencePosition = false,
  showFocusSummary = false,
}: {
  doc: Doc;
  fields: FieldRow[];
  selected: number | null;
  select: (id: number) => void;
  zoom: number;
  focusKeys: string[];
  allowReferencePosition?: boolean;
  showFocusSummary?: boolean;
}) {
  const [page, setPage] = useState(
    () => fields.find((f) => focusKeys.includes(f.key))?.page ?? 1,
  );
  const [loaded, setLoaded] = useState(false);
  const [verifiedForm, setVerifiedForm] = useState(false);
  const viewport = useRef<HTMLDivElement>(null),
    sheet = useRef<HTMLDivElement>(null);
  const focusField = fields.find((f) => focusKeys.includes(f.key));
  const focusBox = useMemo(
    () =>
      focusField?.bbox ??
      (verifiedForm && focusField?.key === "inpatient_days"
        ? referenceForm.medical_detail.regions.inpatient_days
        : null),
    [focusField, verifiedForm],
  );
  // 공유 확대율이 바뀌면 각 문서의 실제 대상 칸을 각 스크롤 영역 가운데로 맞춘다.
  // 문서 밖 페이지를 움직이는 scrollIntoView는 사용하지 않는다.
  useEffect(() => {
    const container = viewport.current,
      paper = sheet.current;
    if (!container || !paper || !loaded || !focusBox) return;
    const center = () => {
      const xs = focusBox.map((p) => p.x),
        ys = focusBox.map((p) => p.y);
      container.scrollTo({
        left:
          paper.offsetLeft +
          ((Math.min(...xs) + Math.max(...xs)) / 2) * paper.clientWidth -
          container.clientWidth / 2,
        top:
          paper.offsetTop +
          ((Math.min(...ys) + Math.max(...ys)) / 2) * paper.clientHeight -
          container.clientHeight / 2,
        behavior: "instant",
      });
    };
    // 이미지 로드 직후 브라우저의 스크롤 복원보다 뒤에서 한 번 더 정렬한다.
    let secondFrame = 0;
    const firstFrame = requestAnimationFrame(() => {
      secondFrame = requestAnimationFrame(center);
    });
    const observer = new ResizeObserver(center);
    observer.observe(container);
    observer.observe(paper);
    return () => {
      cancelAnimationFrame(firstFrame);
      cancelAnimationFrame(secondFrame);
      observer.disconnect();
    };
  }, [focusBox, loaded, zoom]);
  async function imageLoaded(image: HTMLImageElement) {
    setLoaded(true);
    if (
      !allowReferencePosition ||
      doc.source !== "silson24" ||
      doc.doc_type !== "medical_detail"
    )
      return;
    try {
      // 이미 표시한 원본만 해시 검사한다. API 추출이나 외부 서비스 호출은 하지 않는다.
      const response = await fetch(image.currentSrc, {
        credentials: "same-origin",
      });
      if (!response.ok) return;
      const digest = await crypto.subtle.digest(
        "SHA-256",
        await response.arrayBuffer(),
      );
      const hash = Array.from(new Uint8Array(digest), (v) =>
        v.toString(16).padStart(2, "0"),
      ).join("");
      setVerifiedForm(hash === referenceForm.medical_detail.sha256);
    } catch {
      setVerifiedForm(false);
    }
  }
  return (
    <div className="original-pane">
      <div className="original-caption">
        <strong>{docLabels[doc.doc_type] ?? doc.doc_type}</strong>
        <span>
          {doc.source === "silson24"
            ? "실손24 데이터 · 대응 가상 서식"
            : "앱 업로드 원본"}
        </span>
      </div>
      {/* 비교하는 양쪽에 같은 높이의 안내 칸을 둬 원본 시작 위치를 맞춘다. */}
      {(focusField || showFocusSummary) && (
        <div className="compare-focus-value">
          <span title={focusField ? label(focusField.key) : "대조 항목"}>
            {focusField ? label(focusField.key) : "대조 항목"}
          </span>
          <strong
            title={focusField ? display(focusField) : "대응하는 추출 항목 없음"}
          >
            {focusField ? display(focusField) : "대응하는 추출 항목 없음"}
          </strong>
          <small>
            {focusField?.bbox
              ? "원문 위치"
              : verifiedForm
                ? "가상 서식 위치"
                : "위치 확인 필요"}
          </small>
        </div>
      )}
      {doc.page_size && (
        <div className="viewer-scroll" ref={viewport} data-document-id={doc.id}>
          <div
            className="image-sheet"
            ref={sheet}
            style={{ width: `${zoom}%` }}
          >
            {/* 인증된 동일 출처 이미지. Next 이미지 최적화 캐시에 의료 서류를 저장하지 않는다. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`/api/documents/${doc.id}/image`}
              alt={`${docLabels[doc.doc_type]} 원본`}
              onLoad={(event) => imageLoaded(event.currentTarget)}
            />
            <svg
              viewBox="0 0 1 1"
              preserveAspectRatio="none"
              className="boxes"
              aria-label="추출 항목 좌표"
            >
              {fields
                .filter((f) => f.bbox && f.page === page)
                .map((f) => (
                  <polygon
                    key={f.id}
                    points={f.bbox!.map((p) => `${p.x},${p.y}`).join(" ")}
                    role="button"
                    tabIndex={0}
                    aria-label={`${label(f.key)} 원문 위치`}
                    onClick={() => select(f.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") select(f.id);
                    }}
                    className={`${selected === f.id ? "box-selected" : ""} ${focusKeys.includes(f.key) ? "box-comparison" : ""} ${f.review_reasons.length ? "box-warning" : "box-ok"}`}
                  >
                    <title>
                      {label(f.key)}: {display(f)}
                    </title>
                  </polygon>
                ))}
              {focusField && !focusField.bbox && verifiedForm && focusBox && (
                <polygon
                  className="box-comparison reference-box"
                  points={focusBox.map((p) => `${p.x},${p.y}`).join(" ")}
                  role="button"
                  tabIndex={0}
                  aria-label={`${label(focusField.key)} 가상 서식 위치`}
                  onClick={() => select(focusField.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") select(focusField.id);
                  }}
                >
                  <title>
                    가상 서식 위치 · {label(focusField.key)}:{" "}
                    {display(focusField)}
                  </title>
                </polygon>
              )}
            </svg>
          </div>
        </div>
      )}
      {fields.some((f) => f.page > 1) && (
        <label>
          좌표 페이지{" "}
          <select
            aria-label="좌표 페이지"
            value={page}
            onChange={(e) => setPage(Number(e.target.value))}
          >
            {Array.from(new Set(fields.map((f) => f.page)))
              .sort()
              .map((n) => (
                <option key={n}>{n}</option>
              ))}
          </select>
          <small>
            다중 페이지 PDF는 원본 뷰어에서 해당 페이지를 확인하세요.
          </small>
        </label>
      )}
    </div>
  );
}
function FieldCell({
  f,
  readOnly,
  done,
  select,
  active,
}: {
  f: FieldRow;
  readOnly: boolean;
  done: () => void;
  select: () => void;
  active: boolean;
}) {
  const [edit, setEdit] = useState(false),
    [value, setValue] = useState(display(f)),
    [error, setError] = useState("");
  async function save() {
    try {
      await api(`/fields/${f.id}`, {
        method: "PATCH",
        body: JSON.stringify({ confirmed_value: value }),
      });
      setEdit(false);
      setError("");
      done();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <tr className={active ? "field-selected" : ""} onClick={select}>
      <td>
        <button className="field-link" onClick={select}>
          {label(f.key)}
        </button>
      </td>
      <td>
        {edit ? (
          <>
            <input
              aria-label={`${label(f.key)} 확정값`}
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
            <button onClick={save}>저장</button>
            <button onClick={() => setEdit(false)}>취소</button>
          </>
        ) : (
          <>
            <span>{display(f) || "—"}</span>
            {!readOnly && (
              <button
                className="icon-button"
                aria-label={`${label(f.key)} 수정`}
                onClick={() => setEdit(true)}
              >
                <Pencil size={13} />
              </button>
            )}
            {f.kcd_name && <small>{f.kcd_name}</small>}
          </>
        )}
        {error && (
          <small role="alert" className="bad">
            {error}
          </small>
        )}
      </td>
      <td>
        <span className="field-source">
          {f.method === "data"
            ? "실손24 데이터"
            : `${docLabels[f.doc_type]} (${f.method === "ocr" ? "OCR" : "Parse"})`}
        </span>
      </td>
      <td
        className={
          f.method === "data"
            ? "muted"
            : f.extract_conf === "low"
              ? "warn"
              : f.extract_conf === "high"
                ? "ok"
                : "muted"
        }
        title={
          f.method === "data"
            ? "실손24 정형 데이터는 추출 신뢰도 대상이 아니에요."
            : f.review_reasons.length
              ? f.review_reasons.map(reason).join(" · ")
              : "API가 제공한 추출 신뢰도예요."
        }
      >
        {confidenceDisplay(f)}
      </td>
    </tr>
  );
}
export function ReviewScreen({
  claimId,
  readOnly,
}: {
  claimId: string;
  readOnly: boolean;
}) {
  const params = useSearchParams();
  const router = useRouter();
  const resource = useResource<Claim>(`/claims/${claimId}`),
    { data: c, error } = resource;
  // 비교 진입도 기존 맞춤 비율(100%)로 시작한다. 대상 이동·강조와 수동 확대는 유지한다.
  const [docId, setDoc] = useState<number | null>(null),
    [selected, setSelected] = useState<number | null>(null),
    [zoom, setZoom] = useState(100),
    [compare, setCompare] = useState<Issue | null>(null),
    [message, setMessage] = useState("");
  if (!c) return <LoadState error={error} />;
  const doc =
    c.documents.find((d) => d.id === (docId ?? Number(params.get("doc")))) ??
    c.documents[0];
  const allIssues = c.display_issues;
  const issue =
    compare ?? allIssues.find((i) => i.id === Number(params.get("issue")));
  const comparing = !!issue && issue.doc_ids.length === 2;
  const docs = comparing
    ? c.documents.filter((d) => issue.doc_ids.includes(d.id))
    : doc
      ? [doc]
      : [];
  const fields = c.fields.filter((f) =>
    docs.some((d) => d.id === f.document_id),
  );
  // 안내의 실제 문서 ID와 필드 키만 사용한다. 누락 서류는 원본 대신 보완 화면으로 연결한다.
  function openIssue(i: Issue) {
    if (i.kind === "missing") {
      router.push(`/workspace/supplement?claim=${claimId}`);
      return;
    }
    const target = c!.documents.find((d) => i.doc_ids.includes(d.id));
    if (!target) {
      setMessage("연결된 원본 서류가 없어요. 제출 서류를 확인해 주세요.");
      return;
    }
    setDoc(target.id);
    setCompare(i);
    setSelected(null);
    // 배율은 사용자가 고른 값 그대로 유지한다.
  }
  async function resolve(i: Issue) {
    try {
      for (const id of [i.id, ...(i.related_ids ?? [])])
        await api(`/issues/${id}/resolve`, { method: "POST" });
      resource.reload();
      setMessage("확인 기록을 남겼어요.");
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  return (
    <>
      <PageTitle
        title="문서 분석 · 검토"
        description={`${c.customer_name} · ${c.id} · 제출 ${c.submitted_count} / 필요 ${c.required_count}`}
      />
      <div className="document-tabs">
        {c.documents.map((d) => (
          <button
            key={d.id}
            className={!comparing && doc?.id === d.id ? "selected" : ""}
            onClick={() => {
              setDoc(d.id);
              setCompare(null);
              if (params.get("issue"))
                window.history.replaceState(null, "", `?claim=${claimId}`);
              setSelected(null);
              setZoom(100);
            }}
          >
            {docLabels[d.doc_type] ?? d.doc_type}
          </button>
        ))}
      </div>
      {!doc ? (
        <div className="panel empty-message">
          접수된 원본 서류가 없어요. 청구 상세에서 서류를 추가해 주세요.
        </div>
      ) : (
        <div className="review-grid">
          <div className="review-viewer-slot">
            <section className="panel viewer-panel" data-tour="review-original">
              <div className="panel-heading">
                <h2>{comparing ? "원본 비교" : "원본 서류"}</h2>
                <div className="viewer-tools">
                  <button
                    aria-label="축소"
                    disabled={zoom <= 60}
                    onClick={() => setZoom((z) => z - 20)}
                  >
                    <ZoomOut size={16} />
                  </button>
                  <span className="mono">{zoom}%</span>
                  <button
                    aria-label="확대"
                    disabled={zoom >= 400}
                    onClick={() => setZoom((z) => z + 20)}
                  >
                    <ZoomIn size={16} />
                  </button>
                  {comparing && (
                    <button
                      aria-label="비교 닫기"
                      onClick={() => {
                        setCompare(null);
                        window.history.replaceState(
                          null,
                          "",
                          `?claim=${claimId}`,
                        );
                      }}
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              </div>
              <div className={comparing ? "originals comparing" : "originals"}>
                {docs.map((d) => (
                  <Original
                    key={`${d.id}-${issue?.id ?? "single"}`}
                    doc={d}
                    fields={c.fields.filter((f) => f.document_id === d.id)}
                    selected={selected}
                    select={setSelected}
                    zoom={zoom}
                    focusKeys={issue?.field_keys ?? []}
                    showFocusSummary={comparing}
                  />
                ))}
              </div>
              <div className="viewer-legend">
                <span className="ok">□ 추출 위치</span>
                <span className="warn">□ 확인 필요</span>
                <span>항목을 누르면 원문 위치가 강조돼요.</span>
              </div>
            </section>
          </div>
          <div className="review-results-stack">
            <section
              className="panel results-panel normalization-card"
              data-tour="review-normalized"
            >
              <div className="normalized-heading">
                <h2>정규화 결과</h2>
                <small>
                  {comparing ? "비교 중인 두 문서" : "선택 문서"} ·{" "}
                  {fields.length}개 항목
                </small>
              </div>
              {/* 원본과 같은 문서 순서로 나누고 문서별 스크롤/수정 상태를 분리한다. */}
              <div
                className={`normalized-documents ${comparing ? "split" : ""}`}
              >
                {docs.map((d) => {
                  const documentFields = fields.filter(
                    (f) => f.document_id === d.id,
                  );
                  return (
                    <section
                      className="normalized-document"
                      key={d.id}
                      aria-label={`${docLabels[d.doc_type]} 정규화 결과`}
                    >
                      {comparing && (
                        <h3>
                          {docLabels[d.doc_type]}{" "}
                          <small>{documentFields.length}개 항목</small>
                        </h3>
                      )}
                      {/* 비교 대상이 바뀌면 각 문서의 스크롤도 첫 행부터 시작한다. */}
                      <div
                        className="field-scroll"
                        key={`${d.id}-${issue?.id ?? "single"}`}
                      >
                        <table
                          className="work-table field-table"
                          aria-label={`${docLabels[d.doc_type]} 정규화 결과`}
                        >
                          <thead>
                            <tr>
                              <th>항목</th>
                              <th>값</th>
                              <th>출처</th>
                              <th>신뢰도</th>
                            </tr>
                          </thead>
                          <tbody>
                            {documentFields.map((f) => (
                              <FieldCell
                                key={`${f.id}-${f.confirmed_value}`}
                                f={f}
                                readOnly={readOnly}
                                done={resource.reload}
                                select={() => setSelected(f.id)}
                                active={selected === f.id}
                              />
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </section>
                  );
                })}
              </div>
            </section>
            <section
              className="panel review-issues-card"
              data-tour="review-issues"
            >
              <div className="panel-heading">
                <h2>
                  확인 사항 · 안내{" "}
                  <span className="muted">{allIssues.length}</span>
                </h2>
                <small>서류 간 교차검증 결과</small>
              </div>
              <div className="compact-issues">
                {allIssues.map((i) => (
                  <div
                    key={i.id}
                    className={`compact-issue ${issue?.id === i.id ? "issue-active" : ""}`}
                  >
                    <span
                      className={
                        i.kind === "info"
                          ? "muted"
                          : i.kind === "missing"
                            ? "bad"
                            : "warn"
                      }
                    >
                      {i.kind === "info" ? (
                        <Info size={15} aria-label="안내" />
                      ) : i.kind === "missing" ? (
                        <CircleX size={15} />
                      ) : (
                        <TriangleAlert size={15} />
                      )}
                    </span>
                    <button
                      className="issue-open"
                      type="button"
                      onClick={() => openIssue(i)}
                      aria-label={`${i.title} ${i.kind === "missing" ? "보완 처리" : "관련 서류 보기"}`}
                      aria-pressed={issue?.id === i.id}
                    >
                      <strong>
                        {i.kind === "info" && "안내 · "}
                        {formatDatesInText(i.title).replace(
                          /diagnosis_code/g,
                          "질병분류기호",
                        )}
                      </strong>
                      <small>
                        {formatDatesInText(i.detail)
                          .replace(/not_in_source/g, "원문 불일치")
                          .replace(/surgery_cert/g, "수술확인서")}
                      </small>
                    </button>
                    <div className="issue-actions">
                      {i.kind === "missing" && (
                        <Link href={`/workspace/supplement?claim=${claimId}`}>
                          보완 요청
                        </Link>
                      )}
                      {i.doc_ids.length === 2 && (
                        <button
                          onClick={() => openIssue(i)}
                          aria-label={`${i.title} 원본 비교`}
                        >
                          <Columns2 size={14} />
                          원본 비교
                        </button>
                      )}
                      {!readOnly && i.kind !== "missing" && (
                        <button
                          aria-label={`${i.title} 확인 완료`}
                          onClick={() => resolve(i)}
                        >
                          <CircleCheck size={14} />
                          확인
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {!allIssues.length && (
                  <p className="ok">열린 확인 사항이 없어요.</p>
                )}
              </div>
            </section>
          </div>
        </div>
      )}
      {message && <p role="status">{message}</p>}
    </>
  );
}
