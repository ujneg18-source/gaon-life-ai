"""기존 시연 DB에 김유정 원본을 캐시 전용으로 연결한다. 정답 값은 입력하지 않는다."""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import get_settings
from app.main import create_app
from app.models import Claim
from app.services.rules import review_from_db
from scripts.seed import seed_database


def main():
    settings = get_settings().model_copy(update={"USE_CACHED_RESULTS": True})
    with TestClient(create_app(settings)) as client:
        seed_database(client.app.state.engine, settings)
        client.post("/api/auth/demo-login", json={"role": "reviewer"})
        root = "/api/claims/GA-2610-0482"
        stems = {"01_diagnosis", "02_pathology", "03_admission", "07_pharmacy_receipt"}
        files = [
            ("files", (p.name, p.read_bytes(), "image/png"))
            for p in sorted((settings.SAMPLE_PATH / "png").glob("*.png"))
            if p.stem in stems
        ]
        assert client.post(root + "/documents", files=files).status_code == 200
        assert client.post(root + "/silson24").status_code == 200
        assert client.post(root + "/process").status_code == 202
        state = client.get(root + "/process/status").json()
        assert state["state"] == "done", state
        with Session(client.app.state.engine) as session:
            for claim in session.exec(select(Claim)).all():
                review_from_db(session, claim, settings)
            session.commit()
        data = client.get(root).json()
        assert data["submitted_count"] == 7 and data["required_count"] == 8
        print(
            "Demo data loaded from cache: submitted 7 / required 8; new external calls:",
            state["result"]["requests_made"],
        )


if __name__ == "__main__":
    main()
