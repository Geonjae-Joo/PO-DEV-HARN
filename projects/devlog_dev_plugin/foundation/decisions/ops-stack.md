# Ops Stack — 배포·CI/CD·형상관리·관측성 결정 (DevLog)

> **이 파일이 운영 스택의 단일 출처(single source of truth)다.**
> `tech-stack.md`가 앱 스택을 정한다면, 이 파일은 운영 스택(배포·파이프라인·관측성)을 정한다.
> 무엇을(scope) 운영 요건으로 둘지의 *명세*는 `SPEC-OPS-000.md`에 있고, 이 파일은 그 명세를 *어떤 도구로* 구현할지의 **결정**이다.
> 본 결정은 DevLog SRS Ⅲ-2(인프라 구성)·COR-003·COR-004를 따른다.

---

## 형상관리 (SCM)

| 항목 | 결정 | 비고 |
|---|---|---|
| 호스팅 | 사내 Git (GitHub Enterprise \| GitLab — 사내망) | SRS: 사내망 운영 |
| 브랜치 전략 | trunk-based (main + 단기 feature 브랜치) | PR 필수 |
| 커밋 규칙 | `[<PACK\|SPEC\|MOD>/<task>] 요약 (REQ-...)` | ③ `commit-spine-id.py`가 강제 |
| 보호 규칙 | main 직접 push 금지, PR 리뷰 1+ 승인 | |

## CI/CD

| 항목 | 결정 | 비고 |
|---|---|---|
| CI 엔진 | GitHub Actions (사내) \| GitLab CI | SCM 선택에 종속 |
| CI 게이트 | `npm run build` → `npm run lint`(에러 0) → `vitest` → tdd-gate 통과 | QAR-001, PR 필수 체크 |
| E2E 게이트 | Playwright — JRN-* 여정 (③ Phase γ) | 머지 전 또는 nightly |
| CD 트리거 | main 머지 시 dev 배포, tag 시 stg/prod | 환경별 승인 게이트 |

## 배포 타깃 — Next.js Standalone + PM2 (COR-003·COR-004)

| 항목 | 결정 | 비고 |
|---|---|---|
| 빌드 산출물 | **Next.js Standalone** (`output: "standalone"`, `.next/standalone/`) | COR-003, 200MB 이내 권장 |
| 프로세스 관리 | **PM2** — `ecosystem.config.js`, 무중단 재시작 | COR-004 |
| 로그 | PM2 로그 자동 회전(rotation) 설정 | COR-004 |
| 배포 환경 | Linux 또는 Windows 서버 (사내망) | SRS Ⅲ-2 |
| DB | PostgreSQL 17, `npm run db:push`로 스키마 동기화 | SRS Ⅲ-2, COR-005 |
| 시드 | `npm run seed` (초기 글 6+개 일괄 입력) | DAR-003 |

## 시크릿 / 환경변수 (SER-002)

| 항목 | 결정 |
|---|---|
| 관리 | `.env`(실제값, `.gitignore`로 git 제외) + `.env.example`(키만, git 포함) |
| 필수 키 | `DATABASE_URL` · `NEXTAUTH_SECRET` · `NEXTAUTH_URL` |
| 평문 시크릿 | 커밋 금지 (CI에서 검사) |

## 관측성 (Observability)

> **DevLog는 LLM 기반 앱이 아니다.** 따라서 LLM 트레이싱(Phoenix/Langfuse)은 **범위 밖**이다.

| 항목 | 결정 | 비고 |
|---|---|---|
| 앱 로그 | PM2 stdout/stderr 로그 + 회전 | COR-004 |
| 에러 가시성 | 브라우저/서버 콘솔 비정상 에러 0건 | QAR-005 |
| 성능 기준 | 메인 페이지 LCP 로컬 1초 이내 (수동/Lighthouse 확인) | PER-001 |
| 인프라 메트릭 | 범위 밖 (사내 데모 — 필요 시 SPEC-OPS-000에서 확장) | |

## 변경 이력

| 날짜 | 변경 | 이유 |
|---|---|---|
| 2026-06-30 | 초안 확정 | DevLog SRS 인프라(Standalone+PM2)·사내망·비-LLM 관측 범위로 핀. |
