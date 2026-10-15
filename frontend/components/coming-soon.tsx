import { Clock3, FolderOpen } from "lucide-react";

/** T-04 이후 기능은 준비 상태로 명시해 가상 성공이나 처리 결과를 보여주지 않는다. */
export function ComingSoon({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">보상 업무 / 워크스페이스</p>
        <h1>{title}</h1>
        <p className="muted">{description}</p>
      </div>
      <section className="empty-panel">
        <FolderOpen
          size={40}
          strokeWidth={1.3}
          className="text-accent-strong"
          aria-hidden="true"
        />
        <h2>업무 공간을 준비하고 있어요</h2>
        <p className="muted">
          이곳에서 청구 서류와 검토 정보를 확인할 수 있도록 준비 중입니다.
        </p>
        <p className="plain-status">
          <Clock3 size={16} aria-hidden="true" />
          준비 중
        </p>
      </section>
    </>
  );
}
