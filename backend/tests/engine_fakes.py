"""HTTP 모킹 전용 도우미. 정답은 테스트 계층에서만 응답 생성에 사용한다."""

import base64
import json

import httpx

from app.config import PROJECT_ROOT
from app.services.normalize import flatten
from app.services.upstage import UpstageClient

SAMPLE = PROJECT_ROOT / "data/samples/kim_yujeong"
BOX = [{"x": 0.1, "y": 0.1}, {"x": 0.4, "y": 0.1}, {"x": 0.4, "y": 0.2}, {"x": 0.1, "y": 0.2}]


def install_fake(app, *, fail_extract=False):
    entries = [
        (p.read_bytes(), json.loads((SAMPLE / "answers" / f"{p.stem}.json").read_text()))
        for p in sorted((SAMPLE / "png").glob("*.png"))
    ]
    calls = []

    def handle(request):
        calls.append(request)
        if "document-digitization" in str(request.url):
            values = next(value for blob, value in entries if blob in request.content)
            text = " ".join(
                ("급여" if v else "비급여") if isinstance(v, bool) else str(v)
                for k, v in flatten(values).items()
                if not k.startswith("_")
            )
            return httpx.Response(
                200,
                json={
                    "elements": [{"page": 1, "content": {"html": text}, "coordinates": BOX}],
                    "usage": {"pages": 1},
                },
            )
        body = json.loads(request.content)
        blob = base64.b64decode(body["messages"][0]["content"][0]["image_url"]["url"].split(",")[1])
        values = next(value for data, value in entries if blob == data)
        if "document-classification" in str(request.url):
            message = {"content": json.dumps(values["doc_type"])}
        else:
            if fail_extract:
                return httpx.Response(503, json={"error": "mock_failure"})
            clean = {k: v for k, v in values.items() if not k.startswith("_")}
            extras = {
                k: {"_value": v, "confidence": "high", "page": 1, "word_coordinates": BOX}
                for k, v in clean.items()
                if not isinstance(v, list)
            }
            message = {
                "content": json.dumps(clean, ensure_ascii=False),
                "tool_calls": [
                    {
                        "function": {
                            "name": "additional_values",
                            "arguments": json.dumps(extras, ensure_ascii=False),
                        }
                    }
                ],
            }
        return httpx.Response(
            200, json={"choices": [{"message": message, "finish_reason": "stop"}]}
        )

    # model_copy는 재검증하지 않으므로 비밀값 타입을 명시한다.
    from pydantic import SecretStr

    app.state.upstage_client_factory = lambda settings: UpstageClient(
        settings.model_copy(update={"UPSTAGE_API_KEY": SecretStr("mock-secret")}),
        transport=httpx.MockTransport(handle),
    )
    return calls


def app_files():
    return [
        ("files", (p.name, p.read_bytes(), "image/png"))
        for p in sorted((SAMPLE / "png").glob("*.png"))
        if p.stem in {"01_diagnosis", "02_pathology", "03_admission", "07_pharmacy_receipt"}
    ]
