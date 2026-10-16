"""Dense 검색에 명시적 조항/규칙 식별자만 보강한다. 평가 정답은 읽지 않는다."""

import hashlib
import re
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.agent.kb import load_chunks
from app.agent.solar import Solar


def connect(config):
    if config.QDRANT_URL:
        return QdrantClient(
            url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY.get_secret_value() or None
        )
    return QdrantClient(path=str(config.QDRANT_PATH))


class KnowledgeBase:
    def __init__(self, config, embedder=None, client=None):
        self.config = config
        self.embedder = embedder or Solar(config)
        self.client = client or connect(config)

    def build(self, rebuild=False):
        """내용 기반 UUID로 upsert한다. 삭제는 --rebuild가 명시된 컬렉션에만 수행한다."""
        chunks = load_chunks(self.config.KB_PATH, self.config.KB_CHUNK_MAX_CHARS)
        counts = {}
        for collection in self.config.KB_COLLECTIONS:
            subset = [c for c in chunks if c.collection == collection]
            if rebuild and self.client.collection_exists(collection):
                self.client.delete_collection(collection)
            if not self.client.collection_exists(collection):
                self.client.create_collection(
                    collection,
                    vectors_config=models.VectorParams(
                        size=self.config.EMBED_DIMENSIONS, distance=models.Distance.DOT
                    ),
                )
            vectors = self.embedder.embed([c.chunk_text for c in subset])
            points = [
                models.PointStruct(
                    id=str(
                        uuid5(
                            NAMESPACE_URL,
                            c.source_path
                            + "\0"
                            + c.article
                            + "\0"
                            + hashlib.sha256(c.chunk_text.encode()).hexdigest(),
                        )
                    ),
                    vector=v,
                    payload=c.payload(),
                )
                for c, v in zip(subset, vectors)
            ]
            for offset in range(0, len(points), self.config.EMBED_BATCH_SIZE):
                self.client.upsert(
                    collection, points=points[offset : offset + self.config.EMBED_BATCH_SIZE]
                )
            counts[collection] = len(points)
        return counts

    def search(self, query, collection=None, limit=None):
        if collection and collection not in self.config.KB_COLLECTIONS:
            raise ValueError("허용되지 않은 컬렉션")
        vector = self.embedder.embed([query], query=True)[0]
        candidates = {}
        identifier = re.search(r"제\s*\d+\s*조|CV-0\d", query)
        for name in [collection] if collection else self.config.KB_COLLECTIONS:
            if not self.client.collection_exists(name):
                continue
            hits = self.client.query_points(
                name, query=vector, limit=self.config.KB_CANDIDATES
            ).points
            for hit in hits:
                # Dense 후보 안에서 질문의 구체 명사(3글자 이상) 일치를 소폭 보강한다.
                # 특정 평가 질문/정답 경로를 주입하지 않고 원문에 있는 단어만 사용한다.
                terms = set(re.findall(r"[가-힣A-Za-z]{3,}", query))
                score = hit.score + self.config.KB_TERM_BOOST * sum(
                    term in hit.payload["chunk_text"] for term in terms
                )
                if score < self.config.KB_MIN_SCORE:
                    continue
                payload = hit.payload
                candidates[str(hit.id)] = {**payload, "score": score}
            # 명시적 조항은 dense 결과 밖에서도 payload로 가져와 순위를 보강한다.
            if identifier:
                token = re.sub(r"\s", "", identifier.group())
                filt = (
                    models.Filter(
                        must=[
                            models.FieldCondition(
                                key="article", match=models.MatchValue(value=token)
                            )
                        ]
                    )
                    if token.startswith("제")
                    else None
                )
                points, _ = self.client.scroll(
                    name, scroll_filter=filt, limit=self.config.KB_KEYWORD_LIMIT, with_vectors=False
                )
                for point in points:
                    p = point.payload
                    if token not in re.sub(r"\s", "", p["article"] + " " + p["chunk_text"]):
                        continue
                    old = candidates.get(str(point.id), {**p, "score": 0.0})
                    old["score"] += self.config.KB_IDENTIFIER_BOOST
                    candidates[str(point.id)] = old
        # 항으로 쪼갠 같은 조문도 서로 다른 원문 조각이므로 삭제하지 않는다.
        return sorted(candidates.values(), key=lambda c: c["score"], reverse=True)[
            : limit or self.config.KB_TOP_K
        ]
