"""실행: cd backend && uv run python -m app.scripts.demo_reset"""

import json

from app.config import get_settings
from app.services.demo_reset import reset_demo


def main():
    result = reset_demo(get_settings())
    print(json.dumps(result, ensure_ascii=False))
    if not result["within_limit"]:
        raise SystemExit("시연 초기화가 30초 목표를 초과했습니다.")


if __name__ == "__main__":
    main()
