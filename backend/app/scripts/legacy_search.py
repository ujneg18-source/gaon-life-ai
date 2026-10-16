"""T-18 기준 검색 점수를 고정한 ablation 전용 코드. 운영 에이전트에서는 사용하지 않는다.
원본 6694f85의 검색 점수·정규화 BM25·가중치는 유지한다.
주소 묶음 키만 새 구조의 보장종목/항으로 바꿔 다른 보장종목 원문 혼합을 금지한다.
"""

import math
import re
from collections import Counter

from qdrant_client import models

from app.agent.rag import tokens


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


class LegacySearch:
    def search(self, query, collection=None, limit=None):
        if collection and collection not in self.config.KB_COLLECTIONS:
            raise ValueError("허용되지 않은 컬렉션")
        vector = self.embedder.embed([query], query=True)[0]
        candidates = {}
        identifier = re.search("제\\s*\\d+\\s*조|CV-0\\d", query)
        for name in [collection] if collection else self.config.KB_COLLECTIONS:
            if not self.client.collection_exists(name):
                continue
            points = []
            offset = None
            while True:
                (page, offset) = self.client.scroll(
                    name, offset=offset, limit=self.config.KB_KEYWORD_LIMIT, with_vectors=True
                )
                points.extend(page)
                if offset is None:
                    break
            lexical = lexical_scores(query, [p.payload for p in points])
            for point, word_score in zip(points, lexical):
                dense = sum(a * b for (a, b) in zip(vector, point.vector))
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
            if identifier:
                token = re.sub("\\s", "", identifier.group())
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
                (points, _) = self.client.scroll(
                    name, scroll_filter=filt, limit=self.config.KB_KEYWORD_LIMIT, with_vectors=False
                )
                for point in points:
                    p = point.payload
                    if token not in re.sub("\\s", "", p["article"] + " " + p["chunk_text"]):
                        continue
                    old = candidates.get(str(point.id), {**p, "score": 0.0})
                    old["score"] += self.config.KB_IDENTIFIER_BOOST
                    candidates[str(point.id)] = old
        groups = {}
        for hit in sorted(candidates.values(), key=lambda c: c["score"], reverse=True):
            key = (
                hit["source_path"],
                hit.get("coverage_section", ""),
                hit["article"],
                hit.get("paragraph", ""),
            )
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
