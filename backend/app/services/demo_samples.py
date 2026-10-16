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
