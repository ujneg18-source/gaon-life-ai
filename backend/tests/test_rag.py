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
    assert all(c.node_id and c.address for c in chunks)


def test_qdrant_search_and_identifier(tmp_path):
    config = Settings(_env_file=None, EMBED_DIMENSIONS=2, KB_MIN_SCORE=0, RAG_USE_LLM=False)
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


def test_search_groups_article_pieces_and_retains_definition_context():
    from qdrant_client import models

    client = QdrantClient(":memory:")
    config = Settings(_env_file=None, EMBED_DIMENSIONS=2, KB_MIN_SCORE=0, RAG_USE_LLM=False)
    client.create_collection(
        "policy", vectors_config=models.VectorParams(size=2, distance=models.Distance.DOT)
    )
    points = []
    for i, article in enumerate(["제1조", "제1조", "제1조", "제2조", "제3조"]):
        points.append(
            models.PointStruct(
                id=i,
                vector=[1, 0],
                payload={
                    "doc_name": "가상 기준",
                    "article": article,
                    "title": "정의",
                    "chunk_text": f"입원 기준 조각 {i}",
                    "source_path": "data/kb/gaon/test.md",
                    "is_mock": True,
                },
            )
        )
    client.upsert("policy", points=points)
    kb = KnowledgeBase(config, FakeEmbedding(), client)
    hits = kb.search("영양제 기준")
    assert len({h["article"] for h in hits}) == 3
    merged = next(h for h in hits if h["article"] == "제1조")
    assert "조각" in merged["chunk_text"]  # 원문을 임의로 연결하지 않는다.
    chunks = load_chunks(config.KB_PATH)
    surgery = next(
        c.payload()
        for c in chunks
        if c.source_path.endswith("03_surgery_rider.md") and c.article == "제1조"
    )
    assert any(h["article"] == "제2조" for h in kb.context([surgery]))
    client.close()


def test_structured_json_retry_is_bounded(tmp_path):
    calls = []

    def respond(request):
        calls.append(True)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": "broken json" if len(calls) == 1 else '{"ok":true}'},
                    }
                ]
            },
        )

    config = Settings(_env_file=None, CACHE_PATH=tmp_path)
    result = Solar(config, httpx.MockTransport(respond)).structured([], {"type": "object"}, "test")
    assert result == {"ok": True} and len(calls) == 2


def test_empty_embedding_is_rejected_before_http(tmp_path):
    import pytest

    solar = Solar(
        Settings(_env_file=None, CACHE_PATH=tmp_path),
        httpx.MockTransport(lambda r: (_ for _ in ()).throw(AssertionError("HTTP 호출 금지"))),
    )
    with pytest.raises(ValueError, match="빈 텍스트"):
        solar.embed([" "], query=True)


def test_sibling_items_remain_rerank_candidates(tmp_path):
    from qdrant_client import models

    from app.agent.kb import load_structure

    config = Settings(_env_file=None, EMBED_DIMENSIONS=2, RAG_USE_LLM=False)
    client = QdrantClient(":memory:")
    client.create_collection(
        "policy", vectors_config=models.VectorParams(size=2, distance=models.Distance.DOT)
    )
    chunks = [
        c
        for c in load_structure(config.KB_PATH).chunks
        if c.node_id in {"rider2/질병비급여/제4조/3/2", "rider2/질병비급여/제4조/3/16"}
    ]
    client.upsert(
        "policy",
        points=[
            models.PointStruct(id=i, vector=[1, 0], payload=c.payload())
            for i, c in enumerate(chunks)
        ],
    )
    kb = KnowledgeBase(config, FakeEmbedding(), client)
    hits = kb.search("항암 주사에 쓴 비급여 약제는?", limit=10)
    assert set(kb.last_trace["candidate_ids"]) == {
        "rider2/질병비급여/제4조/3/2",
        "rider2/질병비급여/제4조/3/16",
    }
    # 두 호를 재정렬에 보낸 뒤, 반복 문장의 완전한 단서가 있는 실제2호를 선택한다.
    assert {h["item"] for h in hits} == {"2"}
    assert kb.last_trace["subsumed_ids"] == {
        "rider2/질병비급여/제4조/3/16": "rider2/질병비급여/제4조/3/2"
    }
    client.close()


def test_fixed_sampling_params_are_sent_to_solar(tmp_path):
    observed = []

    def respond(request):
        observed.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "solar-pro4-260806",
                "choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}],
            },
        )

    config = Settings(
        _env_file=None,
        CACHE_PATH=tmp_path,
        SOLAR_CHAT_MODEL="solar-pro4-260806",
        SOLAR_SEED=42,
        SOLAR_TEMPERATURE=0,
        SOLAR_TOP_P=1,
    )
    solar = Solar(config, httpx.MockTransport(respond))
    solar.structured([], {"type": "object"}, "test")
    assert (
        observed[0]["seed"] == 42 and observed[0]["temperature"] == 0 and observed[0]["top_p"] == 1
    )
    assert solar.last_response_meta["model"] == "solar-pro4-260806"


def test_repeated_exclusion_prefers_same_scope_full_proviso():
    from app.agent.rag import prefer_full_provisos

    common = {
        "source_path": "rider2",
        "coverage_section": "질병비급여",
        "article": "제4조",
        "paragraph": "③",
    }
    hits = {
        "short": {
            **common,
            "item": "16",
            "chunk_text": "제4조\n머리\n16. 항암제를 제외한 주사치료 비용",
        },
        "full": {
            **common,
            "item": "2",
            "chunk_text": "제4조\n머리\n2. 영양제 비용. 다만, 항암제를 제외한 주사치료 비용은 제외합니다.",
        },
    }
    order, replacements = prefer_full_provisos(["short", "full"], hits)
    assert order == ["full"] and replacements == {"short": "full"}
    hits["full"]["coverage_section"] = "상해비급여"
    assert prefer_full_provisos(["short", "full"], hits)[0] == ["short", "full"]
