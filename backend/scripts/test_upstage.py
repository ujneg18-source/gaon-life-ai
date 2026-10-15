"""Upstage API 연결 테스트 (키는 출력하지 않음).

사용법 (upstage_demo 폴더에서):
    pip install requests
    python backend/scripts/test_upstage.py design/screens/12_review.png

결과 원본은 data/cache/test_parse.json, data/cache/test_extract.json 에 저장된다.
"""
import base64, json, pathlib, sys
import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
env = {}
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("\"'")
KEY = env.get("UPSTAGE_API_KEY", "")
BASE = env.get("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1")
if not KEY.startswith("up_"):
    sys.exit(".env의 UPSTAGE_API_KEY가 비어 있거나 형식이 달라요.")

img = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "design/screens/12_review.png")
cache = ROOT / "data/cache"
cache.mkdir(parents=True, exist_ok=True)
H = {"Authorization": f"Bearer {KEY}"}

# 1) Document Parse
with img.open("rb") as f:
    r = requests.post(f"{BASE}/document-digitization", headers=H,
                      files={"document": f}, data={"model": "document-parse", "ocr": "force"}, timeout=120)
print("[Parse] status", r.status_code)
parse = r.json()
(cache / "test_parse.json").write_text(json.dumps(parse, ensure_ascii=False, indent=2), encoding="utf-8")
els = parse.get("elements", [])
print("[Parse] elements:", len(els), "| 좌표 키 있음:", any("coordinates" in e for e in els))

# 2) Information Extract
b64 = base64.b64encode(img.read_bytes()).decode()
schema = {"type": "object", "properties": {
    "diagnosis_code": {"type": "string", "description": "질병분류기호 (KCD 코드, 예: C18.7)"},
    "diagnosis_date": {"type": "string", "description": "진단일 YYYY-MM-DD"}}}
body = {"model": "information-extract",
        "messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:application/octet-stream;base64,{b64}"}}]}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "test", "schema": schema}},
        "confidence": True, "location": True, "location_granularity": "word"}
r = requests.post(f"{BASE}/information-extraction/chat/completions", headers=H, json=body, timeout=120)
print("[Extract] status", r.status_code)
ext = r.json()
(cache / "test_extract.json").write_text(json.dumps(ext, ensure_ascii=False, indent=2), encoding="utf-8")
try:
    msg = ext["choices"][0]["message"]
    print("[Extract] 결과:", msg["content"])
    for tc in msg.get("tool_calls") or []:
        print("[Extract] tool_call:", tc["function"]["name"], tc["function"]["arguments"][:500])
except Exception:
    print("[Extract] 응답 형식이 예상과 달라요. data/cache/test_extract.json 확인")
print("완료: data/cache/test_parse.json, test_extract.json 저장")
