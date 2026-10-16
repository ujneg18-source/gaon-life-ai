"""요청 본문 없이 토큰 장부에서 호출 수와 보수적 정가 비용을 계산한다."""

import json
from collections import Counter

from app.config import PROJECT_ROOT, get_settings


def main():
    config = get_settings()
    if not config.SOLAR_USAGE_PATH:
        raise SystemExit("SOLAR_USAGE_PATH를 지정해 주세요.")
    rows = [json.loads(line) for line in config.SOLAR_USAGE_PATH.read_text().splitlines()]
    calls = [r for r in rows if r["event"] == "api_call"]
    tokens_in = sum(r["usage"].get("prompt_tokens", 0) for r in calls)
    tokens_out = sum(r["usage"].get("completion_tokens", 0) for r in calls)
    priced = lambda r: (
        (
            r["usage"].get("prompt_tokens", 0)
            * (
                config.SOLAR_EMBED_INPUT_USD_PER_MILLION
                if r["endpoint"] == "/embeddings"
                else config.SOLAR_INPUT_USD_PER_MILLION
            )
            + r["usage"].get("completion_tokens", 0) * config.SOLAR_OUTPUT_USD_PER_MILLION
        )
        / 1_000_000
    )
    observed = sum(priced(r) for r in calls)
    interrupted = [r for r in rows if r["event"] == "api_interrupted"]
    peers = [r for r in calls if r["kind"] == "gist_grade"]
    estimate_unknown = sum(priced(r) for r in peers) / len(peers) * len(interrupted) if peers else 0
    payload = {
        "events": dict(Counter(r["event"] for r in rows)),
        "actual_http_attempts": sum(
            r["event"] in {"api_call", "api_error", "api_interrupted"} for r in rows
        ),
        "api_calls_by_kind": dict(Counter(r["kind"] for r in calls)),
        "prompt_tokens_received": tokens_in,
        "completion_tokens_received": tokens_out,
        "list_price_usd_per_million": {
            "input": config.SOLAR_INPUT_USD_PER_MILLION,
            "output": config.SOLAR_OUTPUT_USD_PER_MILLION,
        },
        "observed_token_cost_usd": observed,
        "estimated_interrupted_cost_usd": estimate_unknown,
        "total_estimate_usd": observed + estimate_unknown,
        "pricing_source": "https://www.upstage.ai/pricing/api",
        "limitations": "정가 기준 추정이며 프로모션/서버 캐시 할인/VAT/실제 콘솔 차감액은 미확인. 중단1회는 토큰을 못 받아 같은 채점 호출 평균 비용으로 추정. 로컬 캐시 hit는 새 API 과금이 아님.",
    }
    out = PROJECT_ROOT / "artifacts/t18/presentation"
    (out / "usage_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    # 본문이 없는 장부만 명시적 평가 산출물에 보존하고 응답 캐시는 Git에서 제외한다.
    (out / "usage.jsonl").write_text(config.SOLAR_USAGE_PATH.read_text())
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
