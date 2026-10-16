"""T-18c 평가 격리·동일 설정·다수결. 운영 인덱스나 비밀 설정을 산출물로 복사하지 않는다."""

import hashlib
import importlib.util
import json
import random
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.agent.rag import KnowledgeBase
from app.agent.solar import Solar
from app.scripts.legacy_search import LegacySearch


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen(config):
    """모든 셀/개발/홀드아웃은 같은 DB 스냅샷을 쓴다. 현재 인덱스는 읽기 복제만 한다."""
    random.seed(config.EVAL_SEED)
    root = config.EVAL_SNAPSHOT_PATH
    root.mkdir(parents=True, exist_ok=True)
    db = root / "eval.db"
    if not db.exists():
        with (
            sqlite3.connect(config.DB_URL.removeprefix("sqlite:///")) as src,
            sqlite3.connect(db) as dst,
        ):
            src.backup(dst)
    index = root / "index"
    if not index.exists():
        shutil.copytree(config.QDRANT_PATH, index, ignore=shutil.ignore_patterns(".lock"))
    return config.model_copy(
        update={
            "DB_URL": f"sqlite:///{db}",
            "SOLAR_CHAT_MODEL": config.EVAL_MODEL,
            "EVAL_JUDGE_MODEL": config.EVAL_MODEL,
            "SOLAR_SEED": config.EVAL_SEED,
            "SOLAR_TEMPERATURE": config.EVAL_TEMPERATURE,
            "SOLAR_TOP_P": 1.0,
        }
    )


def manifest(config):
    # 키/세션 비밀값은 설정 해시에조차 입력하지 않는다.
    values = {
        k: v
        for k, v in config.model_dump(mode="json").items()
        if k.startswith(("RAG_", "KB_", "CHAT_", "SOLAR_", "EMBED_", "EVAL_"))
        and k not in {"EVAL_QUESTIONS_PATH", "EVAL_OUTPUT_PATH", "KB_STRUCTURE_PATH"}
    }
    values.update(
        {
            "requested_seed": config.SOLAR_SEED,
            "temperature": config.SOLAR_TEMPERATURE,
            "top_p": config.SOLAR_TOP_P,
            "seed_server_support": "공식 API에 seed 명세 없음: 요청 고정/완전 결정성 보장 아님",
        }
    )
    return {
        "settings": values,
        "settings_sha256": hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest(),
        "code_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "db_sha256": digest(config.EVAL_SNAPSHOT_PATH / "eval.db"),
    }


def old_chunks(config):
    """이전 kb.py 자체를 별도 모듈로 읽는다. 새 파서로 옛 청킹을 흉내 내지 않는다."""
    code = subprocess.check_output(
        ["git", "show", config.EVAL_OLD_REVISION + ":backend/app/agent/kb.py"]
    )
    path = config.EVAL_SNAPSHOT_PATH / "old_kb.py"
    path.write_bytes(code)
    spec = importlib.util.spec_from_file_location("_gaon_frozen_kb", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = []
    for c in module.load_chunks(config.KB_PATH, config.KB_CHUNK_MAX_CHARS):
        p = c.payload()
        p.update(
            coverage_section="",
            paragraph="",
            item="",
            address=c.article,
            parent_id="",
            refs=[],
            defined_terms=[],
            paragraph_head="",
            falls_back_to=[],
            authority_level=1
            if c.source_path.endswith(".txt")
            else 4
            if c.collection == "manual"
            else 2
            if "/00_" in c.source_path
            else 3,
        )
        p["node_id"] = (
            "old/"
            + hashlib.sha256(
                (c.source_path + "\0" + c.article + "\0" + c.chunk_text).encode()
            ).hexdigest()[:24]
        )
        p["chunk_id"] = p["node_id"]
        result.append(p)
    return result, hashlib.sha256(code).hexdigest()


def build_old(config):
    """old_policy/old_manual은 실험 스냅샷 안에만 만든다. 운영 컬렉션은 변경하지 않는다."""
    client = QdrantClient(path=str(config.EVAL_SNAPSHOT_PATH / "index"))
    try:
        chunks, sha = old_chunks(config)
        solar = Solar(config)
        for collection in config.KB_COLLECTIONS:
            name = "old_" + collection
            if client.collection_exists(name):
                continue
            client.create_collection(
                name,
                vectors_config=models.VectorParams(
                    size=config.EMBED_DIMENSIONS, distance=models.Distance.DOT
                ),
            )
            subset = [p for p in chunks if p["collection"] == collection]
            vectors = solar.embed([p["chunk_text"] for p in subset])
            for i in range(0, len(subset), config.EMBED_BATCH_SIZE):
                client.upsert(
                    name,
                    points=[
                        models.PointStruct(
                            id=str(uuid5(NAMESPACE_URL, p["node_id"])), vector=v, payload=p
                        )
                        for p, v in zip(
                            subset[i : i + config.EMBED_BATCH_SIZE],
                            vectors[i : i + config.EMBED_BATCH_SIZE],
                        )
                    ],
                )
        return {
            "old_parser_revision": config.EVAL_OLD_REVISION,
            "old_parser_sha256": sha,
            "chunks": len(chunks),
            "collections": ["old_policy", "old_manual"],
        }
    finally:
        client.close()


class ExperimentKB(KnowledgeBase):
    """검색 방식 이외는 고정한다. top10으로 서로 다른 조3개와 조각3개를 따로 평가한다."""

    def __init__(self, config, chunking="new", search="new"):
        if chunking == "old":
            config = config.model_copy(update={"KB_COLLECTIONS": ("old_policy", "old_manual")})
        super().__init__(config)
        self.chunking = chunking
        self.mode = search
        self.ranked = {}

    def search(self, query, collection=None, limit=None):
        name = "old_" + collection if collection and self.chunking == "old" else collection
        key = (query, name)
        if key not in self.ranked:
            self.ranked[key] = (
                LegacySearch.search(self, query, name, limit=self.config.RAG_CANDIDATES)
                if self.mode == "old"
                else super().search(query, name, limit=self.config.RAG_CANDIDATES)
            )
        return self.ranked[key][: limit or self.config.KB_TOP_K]


def grade(solar, question, answer, rubric, schema, repeats=3):
    """동일 답변·동일 seed로 독립 채점한다. 다수결/전원 일치 여부를 원표와 별도로 남긴다."""
    votes = []
    for _ in range(repeats):
        votes.append(
            solar.structured(
                [
                    {"role": "system", "content": rubric},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "question": question["question"],
                                "answer_gist": question["answer_gist"],
                                "answer": answer,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                schema,
                "gist_grade",
            )
        )
    return {
        "score": int(sum(v["score"] for v in votes) > len(votes) / 2),
        "reason": " / ".join(v["reason"] for v in votes),
        "votes": votes,
        "unanimous": len({v["score"] for v in votes}) == 1,
    }
