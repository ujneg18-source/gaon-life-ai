# 챗봇 30문항 평가

단계: after / 모델: solar-pro4

질문 원문을 독립 검색한 top-3의 문서·조항으로 recall을 계산한다. 운영 재작성 검색은 trace에 별도 보존한다. 정답 근거가 없는 질문은 recall 분모에서 제외한다. 인용은 doc_name+article 허용 집합 기준으로 엄격히 검사한다.

```json
{
  "questions": 1,
  "fine_recall_at_3": 0.0,
  "fine_citation_precision": null,
  "intent_accuracy": 1.0,
  "recall_at_3_macro": 1.0,
  "retrieval_questions": 1,
  "hit_at_3": 1.0,
  "citation_precision_micro": null,
  "citation_question_pass": 0.0,
  "refusal_accuracy": 1.0,
  "gist_accuracy": 0.0,
  "prohibited_answers": 0,
  "errors": 0
}
```

| ID | intent | recall@3 | 인용 | refusal | 요지 | 금지 표현 |
|---|---|---|---|---|---|---|
| Q23 | True | 1.0 | 0/0 | True | 0 | 0 |

## 실패 사례 원문

### Q23 · 생성 오류
질문: 진단서 발급비도 실손으로 청구돼?

정답 요지: 각종 증명료는 진료와 무관한 비용으로 보상하지 않음

관련 규정을 찾지 못했어요

채점: answer_gist는 '각종 증명료는 진료와 무관한 비용으로 보상하지 않음'이라는 거절 취지가 명시되어 있으나, 답변은 '관련 규정을 찾지 못했어요'라고 하여 핵심 사실(보상하지 않음)을 제공하지 않고 근거를 회피하였으므로 지침에 따라 score=0을 부여함.
