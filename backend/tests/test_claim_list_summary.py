"""목록 요약이 상세의 상태/건수/배정 범위와 같고 상세 렌더링을 실행하지 않는지 검사한다."""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import Settings
from app.main import create_app
from app.models import Claim, Issue, IssueStatus
from app.scripts.deploy_start import prepare


def test_summary_matches_detail_without_building_detail_tables(tmp_path, monkeypatch):
    config = Settings(
        _env_file=None,
        DEPLOY_RUNTIME_DIR=tmp_path,
        UPSTAGE_API_KEY="",
        USE_CACHED_RESULTS=True,
    )
    prepare(config)
    with TestClient(create_app(config)) as client:
        client.post("/api/auth/demo-login", json={"role": "reviewer"})
        full = client.get("/api/claims")
        expected = full.json()

        def forbidden(*args, **kwargs):
            raise AssertionError("목록 조회에서 상세 표시/비교표 생성 금지")

        monkeypatch.setattr("app.agent.claim_answer.render_claim", forbidden)
        monkeypatch.setattr("app.services.workspace.comparisons", forbidden)
        summary = client.get("/api/claims?summary=true")
        assert summary.status_code == 200
        actual = summary.json()
        assert actual["counts"] == expected["counts"]
        assert actual["items"] == [
            {k: v for k, v in item.items() if k not in {"fields", "comparisons", "display_issues"}}
            for item in expected["items"]
        ]
        assert len(summary.content) < len(full.content) / 2
        selected = client.get("/api/claims?summary=true&status=supplement&q=김유정").json()
        assert all(
            c["customer_name"] == "김유정" and c["status"] == "supplement"
            for c in selected["items"]
        )
        assert len(selected["items"]) == 1
        # 저장 이슈를 모두 확인해도 실제 누락 서류가 있는 청구는 보완 상태를 유지한다.
        with Session(client.app.state.engine) as session:
            for issue in session.exec(select(Issue).where(Issue.claim_id == "GA-2610-0482")):
                issue.status = IssueStatus.RESOLVED
                session.add(issue)
            session.commit()
        updated = client.get("/api/claims?summary=true&q=GA-2610-0482").json()["items"][0]
        assert updated["status"] == "supplement"
        # 목록 최적화 이후에도 다른 담당자에게 배정된 청구는 반환하지 않는다.
        with Session(client.app.state.engine) as session:
            claim = session.get(Claim, "GA-2610-0482")
            claim.assignee_id = 2
            session.add(claim)
            session.commit()
        assert client.get("/api/claims?summary=true&q=GA-2610-0482").json()["items"] == []
