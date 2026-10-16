"""Dense+BM25 검색과 명시적 조항 보강. 평가 질문/정답은 운영 검색에서 읽지 않는다."""

import hashlib
import math
import re
from collections import Counter
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.agent.kb import load_chunks
from app.agent.solar import Solar


def tokens(text):
    """형태소 모델 없이도 조사 붙은 한국어를 비교하도록 낱말과 글자 2개 조각을 함께 쓴다."""
    words = re.findall(r"[가-힣A-Za-z0-9]+", text.casefold())
    return [
        token
        for word in words
        for token in [word, *[word[i : i + 2] for i in range(len(word) - 1)]]
        if len(token) > 1
        or token
        not in {"이", "그", "저", "두", "세", "수", "것", "건", "때", "뭐", "왜", "돼", "좀"}
    ]


def lexical_scores(query, payloads):
    """일반 BM25 보강. 고객명·평가 정답·특정 문서 경로를 순위에 주입하지 않는다."""
    query_terms = set(tokens(query))
    docs = [
        Counter(tokens(p["doc_name"] + " " + p["title"] + " " + p["chunk_text"])) for p in payloads
    ]
    lengths = [sum(d.values()) for d in docs]
    avg = sum(lengths) / max(1, len(docs))
    freq = Counter(term for d in docs for term in query_terms if term in d)
    scores = []
    for d, size in zip(docs, lengths):
        score = 0.0
        for term in query_terms:
            tf = d[term]
            if tf:
                idf = math.log(1 + (len(docs) - freq[term] + 0.5) / (freq[term] + 0.5))
                score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * size / max(avg, 1)))
        scores.append(score)
    top = max(scores, default=0)
    return [v / top if top else 0 for v in scores]


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

    def context(self, hits):
        """짧은 특약의 정의/예외를 함께 읽는다. 검색 순위와 추가 문맥을 구분한다."""
        chunks = load_chunks(self.config.KB_PATH, self.config.KB_CHUNK_MAX_CHARS)
        result = list(hits)
        seen = {(h["source_path"], h["article"]) for h in hits}
        for path in dict.fromkeys(h["source_path"] for h in hits):
            related = [c for c in chunks if c.source_path == path and c.collection == "policy"]
            if len({c.article for c in related}) > self.config.KB_CONTEXT_ARTICLES:
                continue
            for c in related:
                if (c.source_path, c.article) not in seen:
                    result.append(c.payload())
                    seen.add((c.source_path, c.article))
        return result

    def search(self, query, collection=None, limit=None):
        if collection and collection not in self.config.KB_COLLECTIONS:
            raise ValueError("허용되지 않은 컬렉션")
        vector = self.embedder.embed([query], query=True)[0]
        candidates = {}
        identifier = re.search(r"제\s*\d+\s*조|CV-0\d", query)
        for name in [collection] if collection else self.config.KB_COLLECTIONS:
            if not self.client.collection_exists(name):
                continue
            # 500개 안팎의 현재 KB에서 dense와 BM25를 같은 후보에 적용한다.
            # scroll 페이지를 모두 읽어 뒷부분 조항이 누락되지 않게 한다.
            points = []
            offset = None
            while True:
                page, offset = self.client.scroll(
                    name, offset=offset, limit=self.config.KB_KEYWORD_LIMIT, with_vectors=True
                )
                points.extend(page)
                if offset is None:
                    break
            lexical = lexical_scores(query, [p.payload for p in points])
            for point, word_score in zip(points, lexical):
                dense = sum(a * b for a, b in zip(vector, point.vector))
                topic = sum(
                    term in point.payload["doc_name"]
                    for term in set(tokens(query))
                    if term not in {"보험", "보험금", "청구", "가온", "생명"}
                )
                score = (
                    dense
                    + self.config.KB_LEXICAL_BOOST * word_score
                    + self.config.KB_TITLE_BOOST * min(topic, 2)
                )
                if score >= self.config.KB_MIN_SCORE:
                    candidates[str(point.id)] = {**point.payload, "score": score}
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
        # 긴 조문 조각이 top-3 세 칸을 모두 차지하지 않게 조별로 묶는다.
        # 각 조의 상위 조각 원문을 합쳐 정의/예외 문맥도 함께 제공한다.
        groups = {}
        for hit in sorted(candidates.values(), key=lambda c: c["score"], reverse=True):
            key = (hit["source_path"], hit["article"])
            groups.setdefault(key, []).append(hit)
        return [
            {
                **parts[0],
                "chunk_text": "\n\n".join(
                    p["chunk_text"] for p in parts[: self.config.KB_CHUNKS_PER_ARTICLE]
                ),
            }
            for parts in groups.values()
        ][: limit or self.config.KB_TOP_K]
