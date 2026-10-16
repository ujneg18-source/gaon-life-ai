# T-18c 검증 기록 (2026-10-16)

- backend: `.venv/bin/python -m pytest -q` → 94 passed, 1 deselected(live).
- backend: Ruff check 및 format check 통과.
- frontend: `npm run lint`, `npm run typecheck`, `npm run format:check` 통과.
- frontend: `npx next build --webpack` → 컴파일, TypeScript, 정적 페이지6개 생성, 트레이스 완료. 최종 근거 카드 소스 포함 재빌드 성공.
- 이전 Turbopack 보조 소켓 권한 오류 이력은 기존 보고서에 보존. Webpack 배포 빌드에는 재현되지 않았다.
- 코드 동결 후 홀드아웃 평가1회 완료; 코드 변경 없음.
