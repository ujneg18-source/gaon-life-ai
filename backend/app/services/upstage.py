"""기능별 v1 클라이언트. 응답 캐시·파일 잠금·보수적 페이지 예산으로 중복 과금을 억제한다.

SDK 내부 재시도를 피하려고 httpx로 직접 전송한다. BackgroundTasks의 작업 스레드에서
동기 호출하므로 요청 처리 루프를 막지 않는다. API 키·요청 이미지·헤더는 로그에 넣지 않는다.
"""

import base64
import fcntl
import hashlib
import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import httpx
from PIL import Image
from pypdf import PdfReader

from app.config import Settings


class UpstageError(RuntimeError):
    """외부 예외의 요청 헤더·본문을 노출하지 않는 안전한 오류 코드."""


def file_pages(path: Path) -> int:
    """파일 확장자만 믿지 않고 실제 PNG/JPEG/PDF의 페이지 수를 계산한다."""
    if path.suffix.lower() == ".pdf":
        return len(PdfReader(path).pages)
    with Image.open(path) as image:
        return image.n_frames if hasattr(image, "n_frames") else 1


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, data: Any) -> None:
    """완성되지 않은 캐시를 다른 작업이 읽지 않도록 같은 디렉터리에서 원자적으로 교체한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".writing-")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


@contextmanager
def locked(path: Path):
    """프로세스가 달라도 같은 파일·예산에 대해 한 번에 한 작업만 진행한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


class UpstageClient:
    """문서 해시와 요청 스키마·모델·옵션을 함께 캐시 키로 사용한다.

    성공 캐시는 USE_CACHED_RESULTS=false에서도 먼저 읽는다. true는 캐시 미스 시
    네트워크에 접근하지 않는 엄격한 모드다. 응답 유실 요청은 pending으로 남겨 재과금을 막는다.
    """

    def __init__(self, settings: Settings, *, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        # 기존 v2 설정을 남긴 환경도 이번 확정 방침대로 v1 기능별 경로를 사용한다.
        base = settings.UPSTAGE_BASE_URL.rstrip("/")
        self.base_url = base.removesuffix("/v2").removesuffix("/v1") + "/v1"
        self.http = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(
                settings.UPSTAGE_TIMEOUT_SEC, connect=settings.UPSTAGE_CONNECT_TIMEOUT_SEC
            ),
        )
        self.requests_made = 0
        self.cache_hits = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.http.close()

    def budget(self) -> dict:
        path = self.settings.CACHE_PATH / "_budget.json"
        with locked(self.settings.CACHE_PATH / "_budget.lock"):
            return (
                json.loads(path.read_text())
                if path.exists()
                else {"reserved_pages": 0, "attempts": []}
            )

    def _reserve(self, operation: str, file_hash: str, pages: int) -> None:
        """응답 usage가 없거나 요청이 실패해도 예약을 환불하지 않아 상한을 보수적으로 지킨다."""
        path = self.settings.CACHE_PATH / "_budget.json"
        with locked(self.settings.CACHE_PATH / "_budget.lock"):
            budget = (
                json.loads(path.read_text())
                if path.exists()
                else {"reserved_pages": 0, "attempts": []}
            )
            if budget["reserved_pages"] + pages > self.settings.UPSTAGE_PAGE_LIMIT:
                raise UpstageError("page_budget_exceeded")
            budget["reserved_pages"] += pages
            budget["attempts"].append(
                {"operation": operation, "file_hash": file_hash, "pages": pages}
            )
            atomic_json(path, budget)

    def classify(self, path: Path) -> dict:
        schema = {
            "type": "string",
            "oneOf": [
                {"const": code, "description": text}
                for code, text in self.settings.UPSTAGE_DOC_CLASSES.items()
            ],
        }
        return self._call(
            "classify",
            path,
            self.settings.UPSTAGE_CLASSIFY_MODEL,
            self.settings.UPSTAGE_CLASSIFY_PATH,
            schema,
            {},
        )

    def parse(self, path: Path) -> dict:
        return self._call(
            "parse",
            path,
            self.settings.UPSTAGE_PARSE_MODEL,
            self.settings.UPSTAGE_PARSE_PATH,
            None,
            {"ocr": self.settings.UPSTAGE_OCR_MODE},
        )

    def extract(self, path: Path, schema: dict, name: str) -> dict:
        return self._call(
            "extract",
            path,
            self.settings.UPSTAGE_EXTRACT_MODEL,
            self.settings.UPSTAGE_EXTRACT_PATH,
            schema,
            {**self.settings.UPSTAGE_EXTRACT_OPTIONS, "schema_name": name},
        )

    def _call(self, operation, path, model, endpoint, schema, options):
        from app.services.demo_deadline import cached_deadline

        signature = {"model": model, "endpoint": endpoint, "schema": schema, "options": options}
        request_hash = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
        root = self.settings.CACHE_PATH / digest_file(path)
        cache = root / f"{operation}-{request_hash}.json"

        def fallback():
            if not cache.is_file():
                return None
            try:
                saved = json.loads(cache.read_text())
                result = saved["response"]
                if (
                    saved["status_code"] == 200
                    and isinstance(result, dict)
                    and not result.get("invalid_json")
                ):
                    return result
            except (ValueError, KeyError):
                pass
            return None

        saved = fallback()
        if saved is not None:
            self.cache_hits += 1
            return saved
        return cached_deadline(
            self.settings,
            lambda: self._call_inner(operation, path, model, endpoint, schema, options),
            fallback,
            operation,
        )

    def _call_inner(
        self,
        operation: str,
        path: Path,
        model: str,
        endpoint: str,
        schema: dict | None,
        options: dict,
    ) -> dict:
        file_hash = digest_file(path)
        signature = {"model": model, "endpoint": endpoint, "schema": schema, "options": options}
        request_hash = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
        root = self.settings.CACHE_PATH / file_hash
        cache = root / f"{operation}-{request_hash}.json"
        pending = cache.with_suffix(".pending")
        with locked(cache.with_suffix(".lock")):
            if cache.exists():
                self.cache_hits += 1
                saved = json.loads(cache.read_text())
                if saved["status_code"] != 200:
                    raise UpstageError(f"cached_http_{saved['status_code']}")
                if not isinstance(saved["response"], dict) or saved["response"].get("invalid_json"):
                    raise UpstageError("invalid_response_json")
                return saved["response"]
            if self.settings.USE_CACHED_RESULTS:
                raise UpstageError(f"cache_miss:{operation}")
            if pending.exists():
                raise UpstageError(f"ambiguous_previous_request:{operation}")
            key = self.settings.UPSTAGE_API_KEY.get_secret_value()
            if not key:
                raise UpstageError("missing_api_key")
            pages = file_pages(path)
            if pages < 1:
                raise UpstageError("empty_document")
            for attempt in range(self.settings.UPSTAGE_MAX_RETRIES + 1):
                self._reserve(operation, file_hash, pages)
                atomic_json(pending, {"operation": operation, "pages": pages})
                try:
                    from app.services.demo_deadline import record_attempt

                    record_attempt(self.settings, endpoint)
                    self.requests_made += 1
                    headers = {"Authorization": f"Bearer {key}"}
                    if operation == "parse":
                        with path.open("rb") as handle:
                            response = self.http.post(
                                self.base_url + endpoint,
                                headers=headers,
                                files={"document": (path.name, handle)},
                                data={"model": model, **options},
                            )
                    else:
                        body = {
                            "model": model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": "data:application/octet-stream;base64,"
                                                + base64.b64encode(path.read_bytes()).decode()
                                            },
                                        }
                                    ],
                                }
                            ],
                            "response_format": {
                                "type": "json_schema",
                                "json_schema": {
                                    "name": options.get("schema_name", "document-classify"),
                                    "schema": schema,
                                },
                            },
                            **{k: v for k, v in options.items() if k != "schema_name"},
                        }
                        response = self.http.post(
                            self.base_url + endpoint, headers=headers, json=body
                        )
                except (httpx.ConnectError, httpx.ConnectTimeout):
                    pending.unlink(missing_ok=True)
                    if attempt < self.settings.UPSTAGE_MAX_RETRIES:
                        time.sleep(self.settings.UPSTAGE_RETRY_DELAY_SEC)
                        continue
                    raise UpstageError("connection_failed") from None
                except httpx.HTTPError:
                    # 읽기/쓰기 타임아웃은 서버가 이미 처리했을 수 있어 자동 재전송하지 않는다.
                    raise UpstageError(f"ambiguous_network_failure:{operation}") from None
                try:
                    payload = response.json()
                except ValueError:
                    payload = {"invalid_json": True, "body": response.text}
                # 응답에 자격 증명이 반사되더라도 캐시 파일에 남기지 않는다.
                payload = json.loads(json.dumps(payload).replace(key, "[REDACTED]"))
                envelope = {
                    "status_code": response.status_code,
                    "response": payload,
                    "file_hash": file_hash,
                    "operation": operation,
                }
                # 모든 응답은 저장한다. 429 재시도도 과금 상한 예약에 포함한다.
                atomic_json(
                    root / f"{operation}-{request_hash}-attempt-{attempt}.response.json", envelope
                )
                if response.status_code == 429 and attempt < self.settings.UPSTAGE_MAX_RETRIES:
                    pending.unlink(missing_ok=True)
                    time.sleep(self.settings.UPSTAGE_RETRY_DELAY_SEC)
                    continue
                atomic_json(cache, envelope)
                # 성공 캐시가 원자적으로 완성된 뒤에만 pending을 지운다. 중간 종료도 재전송하지 않는다.
                pending.unlink(missing_ok=True)
                if response.status_code != 200:
                    raise UpstageError(f"upstage_http_{response.status_code}")
                if not isinstance(payload, dict) or payload.get("invalid_json"):
                    raise UpstageError("invalid_response_json")
                return payload
            raise UpstageError("retry_exhausted")
