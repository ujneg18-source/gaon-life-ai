# 프론트 빌드 진단

- Node 26.10.0, Next.js 16.4.1, Tailwind/PostCSS 4.3.3. 프론트 소스/의존성은 이번 작업에서 변경하지 않았다.
- `npm run lint`, `npm run typecheck`, `npm run format:check`: 모두 통과.
- `npm run build`: 실패. Next.js Turbopack이 `app/globals.css`의 PostCSS 평가 워커를 만들면서 `binding to a port → Operation not permitted (os error 1)`로 중단한다. TypeScript 오류나 포트 사용 중(EADDRINUSE) 오류가 아니다.
- 같은 셸의 단독 Node 소켓은 기본 샌드박스에서 EPERM, 권한 확장 후 IPv4 loopback/전체 인터페이스/IPv6에서 모두 성공한다. 그러나 권한 확장한 Next 빌드의 네이티브 워커 경로에서는 여전히 EPERM이다. 따라서 **관측된 실패 지점은 Turbopack 워커의 포트 바인딩**이며, 정확히 어떤 OS 실행 정책이 네이티브 워커에 남는지는 이 실행 환경에서 확정하지 못했다.
- 이전 T-18에서 Node24/26, Webpack 대체, 임시 webpackBuildWorker 비활성화도 확인했으나 대체 빌드는 정체됐다. 임시 설정은 복구했고 성공으로 보고하지 않는다.
- 다음 단계: 사용자의 일반 터미널/배포 CI에서 같은 lockfile로 `npm ci && npm run build`를 검증하고, 일반 터미널에서도 재현되면 최소 PostCSS 재현 프로젝트와 네이티브 panic 로그로 Next 측 이슈를 조사한다. 원인을 확인하지 않고 의존성을 내리거나 제품 화면을 바꾸지 않았다.

이번 panic 핵심:

```text
Failed to write app endpoint /_not-found/page
[project]/app/globals.css [app-client] (css)
creating new process
binding to a port
Operation not permitted (os error 1)
```
