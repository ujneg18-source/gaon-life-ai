"""시연 외부 요청의 전체 대기 한도. 늦은 응답은 기존 캐시에 보존한다."""

import logging
from queue import Empty, Queue
from threading import Thread

logger = logging.getLogger(__name__)


def cached_deadline(config, request, fallback, endpoint):
    if not config.DEMO_MODE:
        return request()
    completed = Queue(maxsize=1)

    def run():
        try:
            completed.put((True, request()))
        except Exception as exc:  # noqa: BLE001 — 작업 스레드의 예외를 호출자에게 그대로 전달
            completed.put((False, exc))

    Thread(target=run, daemon=True, name="demo-upstage").start()
    try:
        success, result = completed.get(timeout=config.DEMO_API_DEADLINE_SEC)
    except Empty:
        success, result = False, TimeoutError("demo_api_deadline")
    if success:
        return result
    # 같은 요청 지문의 캐시만 사용한다. 타 고객/다른 입력 결과로 대신하지 않는다.
    saved = fallback()
    logger.warning(
        "demo_fallback endpoint=%s reason=%s cache=%s",
        endpoint,
        type(result).__name__,
        saved is not None,
    )
    if saved is not None:
        return saved
    if isinstance(result, TimeoutError):
        raise RuntimeError("demo_api_deadline") from None  # noqa: TRY004 — 기존 API 오류 경계로 전달
    raise result


def record_attempt(config, endpoint):
    """전송 직전의 실제 시도만 센다. 본문·인증·고객 정보는 기록하지 않는다."""
    import json
    from datetime import UTC, datetime

    from app.services.upstage import locked

    target = config.DEMO_CALL_LOG
    if target is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with locked(target.with_suffix(".lock")), target.open("a") as stream:
        stream.write(json.dumps({"at": datetime.now(UTC).isoformat(), "endpoint": endpoint}) + "\n")
