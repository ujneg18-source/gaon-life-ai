"""명시적 데모 모드에서 제공 샘플의 정확한 내용 해시만 모의 입력으로 허용한다."""

import json
from hashlib import sha256


def supplement_input(config, claim, path):
    """파일 이름으로 수술확인서를 추측하지 않는다. 제공 PNG와 바이트가 같아야 한다."""
    if not config.DEMO_SAMPLE_MOCKS:
        return None
    sample = config.SAMPLE_PATH / "supplement" / "수술확인서.png"
    answer = sample.with_suffix(".json")
    if (
        not sample.exists()
        or sha256(path.read_bytes()).digest() != sha256(sample.read_bytes()).digest()
    ):
        return None
    value = json.loads(answer.read_text())
    return value if value["patient_name"] == claim.customer_name else None


def sample_input(config, claim, path):
    """모의 고객 파일만 해시로 조회한다. 실측 허용 고객의 원본을 mock으로 바꾸지 않는다."""
    value = supplement_input(config, claim, path)
    if value or not config.DEMO_SAMPLE_MOCKS:
        return value
    profiles = json.loads(config.DEMO_CUSTOMERS_PATH.read_text())
    customer = next((c for c in profiles["customers"] if c["id"] == claim.customer_id), None)
    if not customer or customer["verification_mode"] == "live":
        return None
    digest = sha256(path.read_bytes()).digest()
    folder = config.SAMPLES_ROOT / customer["sample_id"]
    for doc in customer["documents"]:
        if doc["source"] != "image":
            continue
        originals = [folder / "png" / (doc["stem"] + ".png")]
        originals += [
            p
            for p in (folder / "photo").glob(doc["stem"] + ".*")
            if p.suffix.lower() in config.UPLOAD_EXTENSIONS
        ]
        if any(p.exists() and sha256(p.read_bytes()).digest() == digest for p in originals):
            return json.loads((folder / "answers" / (doc["stem"] + ".json")).read_text())
    return None
