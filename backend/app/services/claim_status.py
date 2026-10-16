"""서류 존재와 확인 상태에서 모든 화면이 공유할 상태를 계산한다."""

from app.models import ClaimStatus, IssueKind, IssueStatus


def claim_status(claim, docs, issues, current_missing=()):
    # 누락의 해소 조건은 담당자 클릭이 아니라 현재 엔진의 서류 존재 검사다.
    if not docs:
        return ClaimStatus.PENDING
    # 분류·추출이 진행 중이면 아직 실제 누락을 확정할 수 없다. 완료한 문서만
    # 남았을 때는 아래 실제 필수서류 검사가 진행 중 플래그보다 우선한다.
    if claim.status == ClaimStatus.PROCESSING and any(
        getattr(doc, "status", None) != "extracted" for doc in docs
    ):
        return ClaimStatus.PROCESSING
    if current_missing:
        return ClaimStatus.SUPPLEMENT
    active = [i for i in issues if i.status == IssueStatus.OPEN and i.kind != IssueKind.INFO]
    if active:
        return ClaimStatus.NEEDS_REVIEW
    if claim.status == ClaimStatus.TO_PAYMENT_REVIEW:
        return claim.status
    if any(i.resolved_by is not None and i.kind != IssueKind.INFO for i in issues):
        return ClaimStatus.READY_REVIEW
    return ClaimStatus.AUTO_PASS
