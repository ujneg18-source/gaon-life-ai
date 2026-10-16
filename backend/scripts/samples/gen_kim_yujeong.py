"""기존 생성기 이름의 호환 진입점. 고객 자료는 customers.json, 서식은 공통 모듈을 쓴다.

김유정 최초7장은 실측 해시·좌표의 기준 자산이므로 재캡처하지 않고 보존한다.
새 고객/서류는 python -m scripts.samples.gen_claim --customer <id>로 생성한다.
"""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.samples.gen_claim import generate

if __name__ == "__main__":
    print("\n".join(generate("kim_yujeong")))
