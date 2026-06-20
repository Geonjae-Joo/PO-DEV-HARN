# Tech Stack — 기술스택 결정 (projects/todo)

> **이 파일이 스택의 단일 출처(single source of truth)다.** ②·③·모든 스킬·훅은 여기에 적힌 스택을 따른다.
> 본 프로젝트는 골드패스 리허설로, "간단한 TODO"를 **실제 실행·green 테스트**까지 보이기 위해 경량 TypeScript 풀스택으로 핀한다.
> (constitution 원칙 8: 스택은 하네스 고정값이 아니라 ① 프로젝트별 결정. 근거: DECISION-LOG D-002)

---

## Backend

| 항목 | 결정 | 비고 |
|---|---|---|
| 언어 | TypeScript 5+ | Node.js 22 런타임 |
| 프레임워크 | Express 4.x | 경량 REST |
| 실행 | tsx (개발/테스트 트랜스파일) | 별도 빌드 단계 없이 실행 |
| 저장소 | In-memory repository | 단일 사용자·리허설 범위. 영속 DB 미사용 |
| 테스트 | Vitest + Supertest | **API 레벨** 통합 테스트 (요청/응답/검증/에러) |
| 린트 | (생략 — 리허설 범위 최소화) | |

## Frontend

| 항목 | 결정 | 비고 |
|---|---|---|
| 언어 | TypeScript 5+ | strict |
| 프레임워크 | React 18+ | |
| 빌드 | Vite | |
| 상태 | React 내장 hooks (useState/useEffect) | Zustand/React Query는 과함 |
| HTTP | fetch (브라우저 내장) | Axios 미도입 |
| 테스트 | Vitest + Testing Library + jsdom | **화면 레벨** 컴포넌트 테스트 |

## E2E

| 항목 | 값 |
|---|---|
| 도구 | Playwright | Phase γ 여정(JRN-) 검증 |

## 테스트 명령 핀 (tdd-gate가 참조)

> tdd-gate.py 자동탐지는 Node **frontend**만 인식하고 Node **backend**는 인식하지 못한다(JVM/Maven/pytest/go 한정).
> 따라서 백+프론트를 함께 도는 명령을 `HARNESS_TEST_CMD`로 명시 핀한다.

```
HARNESS_TEST_CMD="cd app_repo/backend && npm test --silent && cd ../frontend && npm test --silent"
```

## Design System 연동

| 항목 | 값 |
|---|---|
| 사용 DS | shadcn/ui 허용집합 (ds-allowlist.md) |
| 허용 목록 원본 | `foundation/design-system/ds-allowlist.md` |
| 비고 | 리허설 app_repo 프론트는 허용집합 이름과 동형의 경량 로컬 컴포넌트로 구현(실 프로젝트에선 ds-source의 shadcn 컴포넌트). DECISION-LOG D-002 참조 |

## 변경 이력

| 날짜 | 변경 | 이유 |
|---|---|---|
| 2026-06-20 | 초안 확정 | TODO 골드패스 리허설 시작 (경량 TS 풀스택 핀) |
</content>
