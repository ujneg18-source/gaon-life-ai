"""보완 화면과 챗봇은 같은 누락 조회·표준 문구 도구를 사용한다. 별도 Solar 재작성은 없다."""


class SupplementTemplates:
    """표준 문구만 로컬에서 읽는다. 벡터 검색/임베딩/LLM 호출이나 Qdrant 잠금이 필요 없다."""

    def __init__(self, config):
        from app.agent.kb import load_chunks

        self.chunks = load_chunks(config.KB_PATH)

    def lookup(self, source_suffix, article):
        return [
            chunk.payload()
            for chunk in self.chunks
            if chunk.source_path.endswith(source_suffix) and chunk.article == article
        ]


def claim_supplement_draft(session, user, config, claim_id):
    """고객/청구 권한 및 실제 누락은 챗봇의 도구에서 동일하게 확인한다."""
    from app.agent.tools import Tools

    tool = Tools(session, user, config, SupplementTemplates(config))
    return tool.draft_supplement(claim_id, [])
