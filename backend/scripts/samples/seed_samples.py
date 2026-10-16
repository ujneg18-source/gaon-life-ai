"""명시적 seed --demo에만 샘플을 적재한다. 시드 자체는 새 API 호출을 절대로 하지 않는다."""

import json
import shutil
from hashlib import sha256
from pathlib import Path

from sqlmodel import Session, select

from app.models import Claim, Document, DocumentStatus, ExtractedField
from app.services.rules import review_from_db
from app.services.upstage import UpstageError
from scripts.samples.verify_samples import prepared_rows


def seed_samples(engine, config, *, use_photo=False):
    profiles = json.loads(config.DEMO_CUSTOMERS_PATH.read_text())
    count = 0
    with Session(engine) as session:
        for customer in profiles["customers"]:
            claim = session.get(Claim, customer["primary_claim_id"])
            if session.exec(select(Document).where(Document.claim_id == claim.id)).first():
                continue  # 증분 실행은 담당자가 수정한 문서와 이력을 덮어쓰지 않는다.
            try:
                rows, _ = prepared_rows(
                    customer,
                    config,
                    cached=customer["verification_mode"] == "live",
                    use_photo=use_photo,
                )
            except UpstageError:
                # 실제 캐시가 없는 새 환경에서도 가짜 실측 표기를 만들지 않는다.
                rows, _ = prepared_rows(customer, config, use_photo=use_photo)
            for row in rows:
                path = Path(row["path"])
                if row["source"] == "image":
                    target = (
                        config.UPLOAD_PATH
                        / sha256(claim.id.encode()).hexdigest()
                        / (sha256(path.read_bytes()).hexdigest() + path.suffix)
                    )
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
                else:
                    target = (
                        config.MOCK_SILSON24_PATH / customer["sample_id"] / (row["stem"] + ".json")
                    )
                    # 기존 김유정 실손24 3종과 중복 수신 파일을 만들지 않는다.
                    if customer["sample_id"] == "kim_yujeong":
                        target = config.MOCK_SILSON24_PATH / (row["stem"] + ".json")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = {
                        **row["raw"]["normalized"],
                        "doc_type": row["doc_type"],
                        "is_mock": True,
                        "claim_id": claim.id,
                    }
                    if not target.exists():
                        target.write_text(json.dumps(data, ensure_ascii=False, indent=2))
                    row["raw"]["data"] = data
                from PIL import Image

                with Image.open(path) as image:
                    size = {"width": image.width, "height": image.height}
                doc = Document(
                    claim_id=claim.id,
                    doc_type=row["doc_type"],
                    source=row["source"],
                    file_path=str(target),
                    provenance=row["origin"],
                    raw_result=row["raw"],
                    page_size=size,
                    status=DocumentStatus.EXTRACTED,
                )
                session.add(doc)
                session.flush()
                for f in row["fields"]:
                    f = {**f, "id": None, "document_id": doc.id}
                    session.add(ExtractedField(**f))
                count += 1
            session.flush()
            review_from_db(session, claim, config)
        session.commit()
    return count
