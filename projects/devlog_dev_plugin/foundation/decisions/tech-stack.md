# Tech Stack — 기술스택 결정 (DevLog)

> **이 파일이 스택의 단일 출처(single source of truth)다.**
> ②·③와 모든 스킬·훅은 여기에 적힌 스택을 따른다. 특히 ③ **Phase α(scaffold)** 는 `frontend.framework`에서 페이지 shell의 확장자·디렉터리 구조를 파생한다.
> 본 프로젝트는 **DevLog SRS(`DevLog_raw.md`) Ⅲ장 + COR-001**이 강제하는 스택을 그대로 확정한 것이다 — 임의 선택이 아니라 명세 제약이다.
> 변경 시 반드시 DECISIONS.md에 이유를 기록하고 이 파일을 갱신한다.

---

## Frontend (= 본 앱의 주 스택, Full-stack Next.js)

> DevLog는 별도 백엔드 서버 없이 **Next.js 풀스택**(App Router + Server Components + Server Actions)으로 구현한다. "Backend"는 Next.js 내부의 서버 계층(Server Actions·route handler·DB 접근)을 가리킨다.

| 항목 | 결정 | 비고 (SRS 근거) |
|---|---|---|
| 런타임 | Node.js 22.x LTS | SRS Ⅲ-1 |
| 프레임워크 | **Next.js 14.2.x (App Router 전용)** | COR-001 — Pages Router 금지 |
| UI 라이브러리 | React 18.3.x | SRS Ⅲ-1 |
| 언어 | TypeScript 5.x (**strict** 모드) | QAR-001 |
| 스타일 | **Tailwind CSS 3.x** (`darkMode: "class"`) | SFR-011, SIR-003 |
| 렌더링 | Server Components 우선, 필요한 곳만 Client Components | COR-001 |
| 서버 로직 | **Server Actions 패턴** (인증 외 별도 API 라우트 최소화) | COR-001, SER-001 |
| 폼 | Server Action + 클라이언트 검증 | SFR-008, SER-003 |
| 차트 | **Recharts** (최신) | SFR-010 주간 차트 |
| 빌드 산출 | `output: "standalone"` | COR-003 |
| 테스트 | **Vitest + Testing Library** (단위/통합) · **Playwright** (E2E, Phase γ) | TDD 하네스 요건 |
| 린트 | ESLint (Next.js 기본 + `react-hooks/exhaustive-deps`), 에러 0건 | QAR-001 |

## Backend / 데이터 계층 (Next.js 서버 + DB)

| 항목 | 결정 | 비고 (SRS 근거) |
|---|---|---|
| ORM | **Drizzle ORM** (최신) | SRS Ⅲ-1, COR-005(`db:push`·`db:generate`) |
| DB (운영/개발) | **PostgreSQL 17.x** | SRS Ⅲ-1 |
| 마이그레이션 | Drizzle Kit (`drizzle-kit push`/`generate`) | COR-005 |
| 인증 | **NextAuth.js v4 (Credentials Provider)** — JWT 전략 | SFR-007, SER-001 |
| 세션 | JWT를 브라우저 쿠키에만 저장(별도 세션 스토어 없음), `NEXTAUTH_SECRET` 서명 | SFR-007 |
| 보호 라우트 | `middleware.ts` 1차 차단 + Server Action/Component 2차 재검증 | SER-001 (다층 방어) |
| 시드 | `npm run seed` (글 6+개, `import "dotenv/config"` 선행) | DAR-003 |

## 공통 인프라 (요약 — 단일 출처는 ops-stack.md)

| 항목 | 결정 |
|---|---|
| 프로세스 매니저 | **PM2** (`ecosystem.config.js`, 무중단 재시작, 로그 회전) — COR-004 |
| 시크릿 | `.env`(실제값, git 제외) + `.env.example`(키만, git 포함) — SER-002 |
| 패키지 매니저 | npm (Node.js 동봉) |
| 운영 망 | 사내망 (외부 의존 최소; 커버 이미지 `picsum.photos`만 외부) |

> **관측성:** DevLog는 **LLM 기반 앱이 아니다.** 따라서 LLM 트레이싱(Phoenix/Langfuse)은 범위 밖이다. 관측은 PM2 로그 + 콘솔 에러 0건(QAR-005) 수준으로 한정한다. 상세는 `ops-stack.md`·`SPEC-OPS-000.md`.

## 필수 환경변수 (SER-002)

| 키 | 용도 |
|---|---|
| `DATABASE_URL` | PostgreSQL 접속 문자열 |
| `NEXTAUTH_SECRET` | JWT 서명 키 |
| `NEXTAUTH_URL` | NextAuth 콜백 base URL |

## Design System 연동

> **DS 핀의 단일 출처는 `foundation/design-system/ds-allowlist.md`.** 화면 모델(②)·shell(③)은 이 허용집합 안의 컴포넌트만 쓴다(DS 폐쇄).

| 항목 | 값 |
|---|---|
| DS 성격 | DevLog 전용 composite DS (Header·PostCard·FilterBar·PomodoroTimer·ContributionGraph·WeeklyChart·StatCard) + shadcn 계열 primitive |
| 허용 목록 원본 | `foundation/design-system/ds-allowlist.md` |
| 디자인 토큰 | `foundation/design-system/ds-source/src/assets/tokens.css` (CSS custom properties) |
| 렌더 자산 (D8) | `ds-compiled.css` · `ds-fixtures.json` (렌더 엔진이 실제 DS 모양으로 그릴 때 사용) |
| **시각 레퍼런스 ↔ 구현 프레임워크** | DS 시각 레퍼런스는 `projects/devlog`에 shadcn-**vue**로 작성돼 있으나, **본 앱의 구현 프레임워크는 React/Next.js다(COR-001).** ③ `design-system-usage` 스킬이 동일한 컴포넌트 **계약(allowlist의 props·states·usage)** 을 React 컴포넌트로 구현한다. 화면 모델은 프레임워크 중립이므로 계약은 그대로 유효하다. |

토큰 → Tailwind: `tailwind.config.ts`의 `theme.extend`에서 `tokens.css`의 CSS 변수를 참조(시안 강조색·zinc 기반 — SIR-003).

## 변경 이력

| 날짜 | 변경 | 이유 |
|---|---|---|
| 2026-06-30 | 초안 확정 | DevLog SRS Ⅲ장·COR-001 스택을 그대로 핀 (Next.js 풀스택). ③ 테스트 픽스처. |
