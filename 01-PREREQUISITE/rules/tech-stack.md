# Tech Stack — 기술스택 결정

변경 시 반드시 DECISIONS.md에 이유를 기록하고 이 파일을 갱신한다.

---

## Backend

| 항목 | 결정 | 비고 |
|---|---|---|
| 언어 | Java 17+ | record, sealed class 사용 가능 |
| 프레임워크 | Spring Boot 3.x | |
| 빌드 | Gradle (Kotlin DSL) | |
| ORM | Spring Data JPA + Hibernate | |
| DB (운영) | PostgreSQL 15+ | |
| DB (개발/테스트) | H2 in-memory | |
| 마이그레이션 | Flyway | |
| 인증 | Spring Security + JWT (or SSO SAML2) | 프로젝트별 선택 |
| Excel 생성 | Apache POI or EasyExcel | 건수에 따라 선택 |
| 테스트 | JUnit 5 + Mockito + Spring Boot Test | |
| API 문서 | SpringDoc OpenAPI (Swagger UI) | |
| 관측성 | Micrometer + Prometheus + Grafana | |

## Frontend

| 항목 | 결정 | 비고 |
|---|---|---|
| 언어 | TypeScript 5+ | strict 모드 |
| 프레임워크 | React 18+ | |
| 빌드 | Vite | |
| 스타일 | Tailwind CSS + shadcn/ui | DS design token 연동 |
| 상태 관리 | Zustand (전역) + React Query (서버 상태) | |
| 라우팅 | React Router v6 | |
| 폼 | React Hook Form + Zod | |
| 테스트 | Vitest + Testing Library + Playwright (E2E) | |
| HTTP | Axios | |

## 공통 인프라

| 항목 | 결정 |
|---|---|
| 컨테이너 | Docker + Docker Compose (로컬) |
| CI/CD | GitHub Actions |
| 코드 품질 | ESLint + Prettier (FE) / Checkstyle + SpotBugs (BE) |
| 시크릿 | .env (로컬) / Vault or K8s Secret (운영) |

## Design System 연동

- DS design token → CSS custom properties (`--color-primary`, `--spacing-md` 등)
- Tailwind config에서 design token을 `extend`로 참조
- shadcn/ui 컴포넌트 기반으로 DS 컴포넌트 wrapper 작성

## 변경 이력

| 날짜 | 변경 | 이유 |
|---|---|---|
| 2026-06-12 | 초안 확정 | 프로젝트 시작 |
