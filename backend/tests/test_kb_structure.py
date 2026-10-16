"""실제 허용 원문으로 주소·부모·단서·규범 연결을 고정한다."""

from app.agent.kb import load_structure
from app.config import PROJECT_ROOT


def test_disease_vitamin_address_and_parent():
    tree = load_structure(PROJECT_ROOT / "data/kb")
    c = next(c for c in tree.chunks if c.node_id == "rider2/질병비급여/제4조/3/2")
    assert c.coverage_section == "질병비급여" and c.paragraph == "③" and c.item == "2"
    assert "영양제" in c.chunk_text and "보상하는 질병" in c.chunk_text
    assert "보상하는 상해" not in c.chunk_text
    assert c.address == "제4조 ③ 2호"
    assert c.parent_id == "rider2/질병비급여/제4조/3"
    assert "19." in tree.nodes[c.parent_id]["chunk_text"]
    assert c.node_id + "/가" in tree.nodes
    assert any(c.node_id == "rider2/상해비급여/제4조/3/2" for c in tree.chunks)
    assert any(c.node_id == "rider2/비급여자기공명영상진단/제4조/4/2" for c in tree.chunks)


def test_every_item_keeps_lead_and_proviso():
    tree = load_structure(PROJECT_ROOT / "data/kb")
    for c in tree.chunks:
        if c.item:
            assert c.paragraph_head in c.chunk_text
            assert c.parent_id in tree.nodes
        assert not c.chunk_text.lstrip().startswith(("다만", "단,"))
        assert c.authority_level in {1, 2, 3, 4} and c.governs
    c = next(c for c in tree.chunks if c.node_id == "rider2/질병비급여/제4조/3/2")
    assert "다만" in c.chunk_text and "라." in c.chunk_text


def test_manual_table_headers_and_definition_links():
    tree = load_structure(PROJECT_ROOT / "data/kb")
    rows = [c for c in tree.chunks if c.collection == "manual" and "/row" in c.node_id]
    assert rows and all(c.chunk_text.count("|") >= 6 for c in rows)
    assert "보장개시일" in tree.definitions
    assert any("보장개시일" in c.defined_terms and not c.is_definition for c in tree.chunks)
    rider = next(c for c in tree.chunks if c.source_path.endswith("01_cancer_rider.md"))
    assert any(p.endswith("std_life_insurance.txt") for p in rider.falls_back_to)
    assert any("/gaon/00_" in p for p in rider.falls_back_to)


def test_missing_rider_rule_follows_fallback_to_main_contract(tmp_path):
    from qdrant_client import QdrantClient

    from app.agent.rag import KnowledgeBase
    from app.config import Settings
    from tests.test_rag import FakeEmbedding

    tree = load_structure(PROJECT_ROOT / "data/kb")
    config = Settings(
        _env_file=None,
        EMBED_DIMENSIONS=2,
        RAG_USE_LLM=False,
        KB_STRUCTURE_PATH=tmp_path / "parents.json",
    )
    client = QdrantClient(":memory:")
    kb = KnowledgeBase(config, FakeEmbedding(), client)
    kb.build()
    rider = next(
        c.payload()
        for c in tree.chunks
        if c.source_path.endswith("03_surgery_rider.md") and "준용" in c.title
    )
    context = kb.context([rider], "특약에 없는 청구권 소멸시효를 주계약에서 준용해 알려줘")
    links = [h for h in context if h.get("via_fallback")]
    assert any("/gaon/00_" in h["source_path"] and "3년" in h["chunk_text"] for h in links)
    assert any(
        h["source_path"].endswith("std_life_insurance.txt") and h["article"] == "제37조"
        for h in links
    )
    assert len([h for h in context if h.get("is_context_link")]) <= 2
    assert [h["authority_level"] for h in context] == [3, 2, 1]
    client.close()
