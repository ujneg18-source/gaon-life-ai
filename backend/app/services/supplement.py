"""문구 생성은 지급 판단과 분리한다. 캐시 전용·실패 시 표준 문구를 그대로 쓴다."""

import hashlib
import json

import httpx

from app.services.upstage import locked


def draft_message(config, name, claim_id, labels, *, transport=None):
    base = (
        f"[가온생명] {name} 고객님, 보험금 청구({claim_id}) 검토를 위해 다음 서류가 필요합니다.\n\n"
        + ", ".join(labels)
        + "\n\n발급받으신 서류를 가온생명 앱의 [서류 추가 제출]에 올려 주세요. 제출 후 담당자가 확인하겠습니다."
    )
    body = {
        "model": config.SOLAR_CHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "표준 보완 안내문의 표현만 친절하게 다듬으세요. 서류 이름, 청구번호, 고객 이름을 유지하세요. 지급 여부·기한·금액·새로운 요구는 추가하지 마세요. 본문만 출력하세요.",
            },
            {"role": "user", "content": base},
        ],
        "reasoning_effort": "medium",
    }
    fingerprint = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    directory = config.CACHE_PATH / "solar"
    directory.mkdir(parents=True, exist_ok=True)
    cache = directory / f"{fingerprint}.json"
    with locked(cache.with_suffix(".lock")):
        if cache.exists():
            return json.loads(cache.read_text())["message"], "solar_cached"
        if config.USE_CACHED_RESULTS or not config.UPSTAGE_API_KEY.get_secret_value():
            return base, "standard_template"
        try:
            # 문서 엔진과 같은 config로만 키를 읽으며 예외 응답/헤더는 이력에 넣지 않는다.
            with httpx.Client(timeout=config.UPSTAGE_TIMEOUT_SEC, transport=transport) as client:
                response = client.post(
                    config.UPSTAGE_BASE_URL.rstrip("/").removesuffix("/v2").removesuffix("/v1")
                    + "/v1"
                    + config.SOLAR_CHAT_PATH,
                    headers={
                        "Authorization": "Bearer " + config.UPSTAGE_API_KEY.get_secret_value()
                    },
                    json=body,
                )
                response.raise_for_status()
                result = response.json()
                message = result["choices"][0]["message"]["content"].strip()
            if (
                not message
                or len(message) > config.SUPPLEMENT_MAX_CHARS
                or any(v not in message for v in [name, claim_id, *labels])
            ):
                return base, "standard_template"
            # 원 응답과 채택 문구를 별도로 캐시한다. 로그에는 사용 경로만 남긴다.
            temp = cache.with_suffix(".tmp")
            temp.write_text(
                json.dumps({"response": result, "message": message}, ensure_ascii=False)
            )
            temp.replace(cache)
            return message, "solar"
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            return base, "standard_template"
