# 간헐 오류 재현·방어 기록

| 실행 | 현상 | 확인된 근거 | 조치 |
|---|---|---|---|
| 이전 T-18 Q22/Q25 | HTTPException, 최종 응답 실패 | 기존 raw에 claim_id/HTTP 상태 기록. 과거 HTTP 본문/전체 도구 계획이 없으므로 원인을 확정할 수 없음 | 모델이 검증된 ID를 다시 추측하는 자유 도구 계획을 제거. 의도별 Pydantic 읽기 절차·권한 검사로 고정 |
| T-18b demo-4 2번 | `확인하지 못했어요` | 첫 smoke 원문/기대 항목 실패를 그대로 보존. 당시 직접 검색 경로에는 상태 로그가 없어 정확한 HTTP 원인은 미확인 | 주소로 이미 찾는 규칙/템플릿의 중복 Solar 검색 제거. 검색도 도구의 최대1회 재시도·오류 클래스/상태 로그 적용 |
| T-18b revision-3b Q13 독립 검색 | embedding HTTP400, 평가 중단 | 실제 로그 `solar_failure endpoint=/embeddings status=400 error=HTTPStatusError` | 빈 재작성은 원 질문으로 복귀, embed가 빈 입력을 HTTP 전에 거절. 평가 검색도 한 번 재시도하고 실패 기록. API 오류 본문을 저장하지 않아 이번400의 정확한 사유는 미확인 |
| 준용 smoke 첫 시도 | 로컬 Qdrant 잠금 | API 호출 전 AlreadyLocked, 동시 ablation 프로세스 소유 | 인덱스 스냅샷으로 전환. 후속 실제 준용 검증 통과 |

로그는 도구명·시도 횟수·endpoint·상태/오류 클래스만 남긴다. 키·헤더·오류 본문·고객/의료 입력은 운영 로그에 저장하지 않는다. `test_tools_only_retry_once_and_log_without_arguments`로 두 번 실패 시 안전 응답, 1회 한도와 입력 비노출을 고정했다. 403은 즉시 전파한다.
