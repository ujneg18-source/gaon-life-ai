"""공개/가상 텍스트만 인덱싱한다. HWP Parse는 실행하지 않는다."""

import argparse
import json

from app.agent.rag import KnowledgeBase
from app.config import get_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    kb = KnowledgeBase(get_settings())
    try:
        print(json.dumps(kb.build(args.rebuild), ensure_ascii=False))
    finally:
        kb.client.close()


if __name__ == "__main__":
    main()
