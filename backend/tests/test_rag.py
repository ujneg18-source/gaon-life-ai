"""문서 경계·메타데이터·캐시·검색 배관은 외부 과금 없이 검증한다."""

import json

import httpx
from qdrant_client import QdrantClient

from app.agent.kb import load_chunks
from app.agent.rag import KnowledgeBase
from app.agent.solar import Solar
from app.config import PROJECT_ROOT, Settings


class FakeEmbedding:
    def embed(self, texts, query=False):
        # 테스트용 동일 의미 벡터. 실제 품질은 별도 smoke로만 주장한다.
        return [[1.0, 0.0] if "영양제" in t or "비타민" in t else [0.0, 1.0] for t in texts]


def test_chunks_metadata_and_exclusion(tmp_path):
    root = PROJECT_ROOT / "data/kb"
    chunks = load_chunks(root)
    assert chunks and all(
        set(c.payload())
        >= {"doc_name", "edition", "article", "title", "is_mock", "source_path", "chunk_text"}
        for c in chunks
    )
    assert all("reference/" not in c.source_path and ".hwp" not in c.source_path for c in chunks)
    assert all(c.is_mock == c.source_path.endswith(".md") for c in chunks)
    assert any(c.article == "제3조" and "암진단" in c.doc_name for c in chunks)
    assert all(len(c.chunk_text) < 4000 for c in chunks)


def test_qdrant_search_and_identifier(tmp_path):
    config = Settings(_env_file=None, EMBED_DIMENSIONS=2, KB_MIN_SCORE=0)
    client = QdrantClient(":memory:")
    kb = KnowledgeBase(config, FakeEmbedding(), client)
    assert kb.build()["policy"] > 100
    found = kb.search("영양제 실손 보상돼?", limit=20)
    assert any("rider2" in h["source_path"] and h["article"] == "제4조" for h in found)
    assert any(h["article"] == "제3조" for h in kb.search("암진단특약 제3조"))
    client.close()


def test_embedding_batch_and_content_cache(tmp_path):
    calls = []

    def respond(request):
        body = json.loads(request.content)
        calls.append(body)
        return httpx.Response(
            200,
            json={"data": [{"index": i, "embedding": [1, 0]} for i, _ in enumerate(body["input"])]},
        )

    config = Settings(_env_file=None, CACHE_PATH=tmp_path, EMBED_DIMENSIONS=2)
    solar = Solar(config, httpx.MockTransport(respond))
    texts = [str(i) for i in range(101)]
    assert len(solar.embed(texts)) == 101
    assert [len(c["input"]) for c in calls] == [100, 1]
    solar.embed(list(reversed(texts)))
    assert len(calls) == 2
    solar.embed(["0"], query=True)
    assert calls[-1]["model"] == config.SOLAR_EMBED_QUERY_MODEL
