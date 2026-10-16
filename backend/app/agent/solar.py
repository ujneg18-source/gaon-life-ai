"""Solar HTTP 경계. 키는 Settings만 읽고 캐시·예외에 인증 정보는 저장하지 않는다."""

import hashlib
import json

import httpx

from app.services.upstage import locked


class Solar:
    def __init__(self, config, transport=None):
        self.config, self.transport = config, transport

    def post(self, path, body):
        config = self.config
        fingerprint = hashlib.sha256(
            json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        cache = config.CACHE_PATH / "chat" / (fingerprint + ".json")
        cache.parent.mkdir(parents=True, exist_ok=True)
        with locked(cache.with_suffix(".lock")):
            if cache.exists():
                return json.loads(cache.read_text())
            if config.USE_CACHED_RESULTS:
                raise RuntimeError("저장된 챗봇 응답이 없어요. 캐시 전용 모드예요.")
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
            except (httpx.HTTPError, ValueError):
                raise RuntimeError("AI 연결에 실패했어요. 잠시 후 다시 시도해 주세요.") from None
            cache.write_text(json.dumps(result, ensure_ascii=False))
            return result

    def structured(self, messages, schema, name):
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
