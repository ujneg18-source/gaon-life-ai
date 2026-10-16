"""Solar HTTP 경계. 키는 Settings만 읽고 캐시·예외에 인증 정보는 저장하지 않는다."""

import hashlib
import json
import logging
from datetime import UTC, datetime

import httpx

from app.services.upstage import locked


class Solar:
    def __init__(self, config, transport=None):
        self.config, self.transport = config, transport

    def post(self, path, body):
        config = self.config
        if path == config.SOLAR_CHAT_PATH:
            body = dict(body)
            for key, value in [
                ("seed", config.SOLAR_SEED),
                ("temperature", config.SOLAR_TEMPERATURE),
                ("top_p", config.SOLAR_TOP_P),
            ]:
                if value is not None:
                    body[key] = value
        # 기본은 대화 비저장이다. 사용자가 요청한 가상 평가/시연만 명시적으로 응답 캐시를 켠다.
        if path == config.SOLAR_CHAT_PATH and config.SOLAR_RESPONSE_CACHE:
            fingerprint = hashlib.sha256(
                json.dumps(
                    {"base": config.UPSTAGE_BASE_URL, "body": body},
                    ensure_ascii=False,
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            cache = config.CACHE_PATH / "chat_responses" / (fingerprint + ".json")
            cache.parent.mkdir(parents=True, exist_ok=True)
            with locked(cache.with_suffix(".lock")):
                if cache.exists():
                    result = json.loads(cache.read_text())
                    self.record_usage(path, body, result, "cache_hit")
                    return result
                if config.USE_CACHED_RESULTS:
                    raise RuntimeError("저장된 LLM 응답이 없어요.")
                result = self._request(path, body)
                if result.get("choices", [{}])[0].get("finish_reason") == "stop":
                    cache.write_text(json.dumps(result, ensure_ascii=False))
                return result
        if path != "/embeddings":
            if config.USE_CACHED_RESULTS:
                raise RuntimeError("챗봇은 캐시 전용 모드에서 실제 LLM을 호출하지 않아요.")
            return self._request(path, body)
        fingerprint = hashlib.sha256(
            json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        cache = config.CACHE_PATH / "embedding_batches" / (fingerprint + ".json")
        cache.parent.mkdir(parents=True, exist_ok=True)
        with locked(cache.with_suffix(".lock")):
            if cache.exists():
                return json.loads(cache.read_text())
            if config.USE_CACHED_RESULTS:
                raise RuntimeError("저장된 임베딩이 없어요.")
            result = self._request(path, body)
            cache.write_text(json.dumps(result, ensure_ascii=False))
            return result

    def _request(self, path, body):
        """인증 헤더·실패 본문은 예외와 로그에 섞지 않는다."""
        config = self.config
        try:
            with httpx.Client(
                timeout=config.UPSTAGE_TIMEOUT_SEC, transport=self.transport
            ) as client:
                response = client.post(
                    config.UPSTAGE_BASE_URL.rstrip("/") + path,
                    headers={
                        "Authorization": "Bearer " + config.UPSTAGE_API_KEY.get_secret_value()
                    },
                    json=body,
                )
                response.raise_for_status()
                result = response.json()
                self.record_usage(path, body, result, "api_call")
                self.last_response_meta = {
                    k: result.get(k) for k in ("model", "system_fingerprint", "usage")
                }
                return result
        except (httpx.HTTPError, ValueError) as exc:
            self.record_usage(path, body, {}, "api_error")
            # 상태/오류 클래스만 기록한다. 응답 본문·헤더·질문·키는 남기지 않는다.
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            logging.getLogger(__name__).warning(
                "solar_failure endpoint=%s status=%s error=%s", path, status, type(exc).__name__
            )
            raise RuntimeError("AI 연결에 실패했어요. 잠시 후 다시 시도해 주세요.") from None

    def record_usage(self, path, body, result, event):
        """요청 본문/응답/인증 대신 종류·토큰만 장부에 남긴다. 실제 청구액과는 구별한다."""
        target = self.config.SOLAR_USAGE_PATH
        if not target:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "at": datetime.now(UTC).isoformat(),
            "event": event,
            "endpoint": path,
            "model": result.get("model", body.get("model")),
            "kind": body.get("response_format", {}).get("json_schema", {}).get("name", "embedding"),
            "usage": result.get("usage", {}),
        }
        with locked(target.with_suffix(".lock")), target.open("a") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    def structured(self, messages, schema, name):
        """구조화 JSON이 잘못된 경우만 한 번 재시도한다. 업무 오류/권한 오류는 숨기지 않는다."""
        for attempt in range(self.config.SOLAR_STRUCTURED_ATTEMPTS):
            try:
                return self._structured_once(messages, schema, name)
            except json.JSONDecodeError:
                if attempt + 1 == self.config.SOLAR_STRUCTURED_ATTEMPTS:
                    raise RuntimeError("AI 구조화 응답 형식이 올바르지 않아요.") from None

    def _structured_once(self, messages, schema, name):
        result = self.post(
            self.config.SOLAR_CHAT_PATH,
            {
                "model": self.config.SOLAR_CHAT_MODEL,
                "messages": messages,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": name, "strict": True, "schema": schema},
                },
            },
        )
        choice = result["choices"][0]
        if choice.get("finish_reason") != "stop":
            raise RuntimeError("AI 답변이 완성되지 않았어요. 다시 질문해 주세요.")
        return json.loads(choice["message"]["content"])

    def embed(self, texts, *, query=False):
        """내용+모델별로 저장해 배치 구성이 바뀌어도 이미 임베딩한 조각은 재과금하지 않는다."""
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("빈 텍스트는 임베딩할 수 없어요.")
        model = (
            self.config.SOLAR_EMBED_QUERY_MODEL if query else self.config.SOLAR_EMBED_PASSAGE_MODEL
        )
        folder = self.config.CACHE_PATH / "embeddings"
        folder.mkdir(parents=True, exist_ok=True)
        paths = [
            folder / (hashlib.sha256((model + "\0" + t).encode()).hexdigest() + ".json")
            for t in texts
        ]
        missing = list(dict.fromkeys(i for i, p in enumerate(paths) if not p.exists()))
        for offset in range(0, len(missing), self.config.EMBED_BATCH_SIZE):
            indices = missing[offset : offset + self.config.EMBED_BATCH_SIZE]
            result = self.post(
                "/embeddings", {"model": model, "input": [texts[i] for i in indices]}
            )
            rows = sorted(result["data"], key=lambda row: row["index"])
            if len(rows) != len(indices):
                raise RuntimeError("임베딩 개수가 맞지 않습니다")
            for i, row in zip(indices, rows):
                if len(row["embedding"]) != self.config.EMBED_DIMENSIONS:
                    raise RuntimeError("임베딩 차원이 맞지 않습니다")
                paths[i].write_text(json.dumps(row["embedding"]))
        return [json.loads(p.read_text()) for p in paths]
