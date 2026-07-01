# DECISIONS — 프로젝트 결정 로그 (DevLog)

> tech-stack.md·ops-stack.md 변경 시 그 **이유**를 여기에 남긴다. 하류(②③)는 결정의 *결과*만 보고, 그 *이유*는 이 로그가 단일 출처다.

| 날짜 | 영역 | 결정 | 이유 |
|---|---|---|---|
| 2026-06-30 | 스택 | 프론트엔드·풀스택을 Next.js 14 App Router로 확정 | DevLog SRS COR-001이 App Router 전용을 강제(Pages Router 금지). Server Components/Actions 우선. |
| 2026-06-30 | 스택 | ORM=Drizzle, DB=PostgreSQL 17 | SRS Ⅲ-1 명시. `db:push`/`db:generate` npm script(COR-005). |
| 2026-06-30 | 인증 | NextAuth v4 Credentials + JWT(쿠키) | SFR-007. 사내망이라 외부 OAuth 불가(COR-002). 데모 계정 3명 하드코딩(DAR-004). |
| 2026-06-30 | 배포 | Standalone 빌드 + PM2 | COR-003·COR-004. 사내망 무중단 운영. |
| 2026-06-30 | 관측성 | LLM 트레이싱 범위 밖 | DevLog는 LLM 앱이 아님. PM2 로그 + 콘솔 에러 0(QAR-005)로 한정. |
| 2026-06-30 | DS | 시각 레퍼런스(shadcn-vue)와 구현 프레임워크(React) 분리 | 화면 모델은 프레임워크 중립. allowlist 계약을 ③가 React로 구현. COR-001 준수. |
