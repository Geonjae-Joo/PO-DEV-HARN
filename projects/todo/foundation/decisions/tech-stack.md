# Tech Stack — 기술스택 결정 (todo 프로젝트)

> **이 파일이 스택의 단일 출처(single source of truth)다.**
> D-001, D-002 결정 참조 → DECISIONS/DECISIONS.md

---

## Backend

| 항목 | 결정 | 비고 |
|---|---|---|
| 언어 | TypeScript 5+ | strict 모드 |
| 프레임워크 | Express 4.x | |
| 빌드 | tsx (ts-node 대체) | |
| ORM | Prisma | SQLite 개발, PostgreSQL 운영 |
| DB (개발/테스트) | SQLite (파일 기반) | |
| DB (운영) | PostgreSQL 15+ | |
| 마이그레이션 | Prisma Migrate | |
| 인증 | JWT (accessToken 메모리 + refreshToken httpOnly 쿠키) | D-003 참조 |
| 테스트 | Vitest + supertest | |
| API 문서 | 없음 (골든패스 시연 범위) | |

## Frontend

| 항목 | 결정 | 비고 |
|---|---|---|
| 언어 | TypeScript 5+ | strict 모드 |
| 프레임워크 | React 18+ | |
| 빌드 | Vite | |
| 스타일 | Tailwind CSS v4 + shadcn/ui | DS design token 연동 |
| 상태 관리 | Zustand (전역) + React Query v5 (서버 상태) | |
| 라우팅 | React Router v6 | |
| 폼 | React Hook Form + Zod | |
| 테스트 | Vitest + Testing Library | |
| HTTP | Axios | |

## 공통 인프라

| 항목 | 결정 |
|---|---|
| 컨테이너 | 없음 (골든패스 로컬 실행) |
| CI/CD | 없음 (골든패스 범위) |
| 코드 품질 | ESLint + Prettier |

## Design System 연동

| 항목 | 값 |
|---|---|
| 사용 DS | shadcn/ui (Radix UI + Tailwind CSS) |
| 스타일 | new-york |
| 기반 색상 | zinc (다크모드 최적화 — D-006) |
| 컴포넌트 소스 위치 | `foundation/design-system/ds-source/src/components/ui/` |
| 허용 목록 원본 | `foundation/design-system/ds-allowlist.md` |

## 변경 이력

| 날짜 | 변경 | 이유 |
|---|---|---|
| 2026-06-22 | 초안 확정 | 골든패스 시작 |
