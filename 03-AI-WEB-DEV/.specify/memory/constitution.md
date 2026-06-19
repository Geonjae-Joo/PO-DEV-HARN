# PO-DEV Harness Constitution

<!--
  이 파일은 spec-kit의 모든 명령(/speckit-specify·clarify·plan·tasks·analyze·implement·checklist)이
  비-협상(non-negotiable) 권위로 읽는다. /speckit-analyze는 이 원칙 위반을 자동 CRITICAL로 분류한다.
  원본 하드 룰: 01-PREREQUISITE/.claude/rules/constitution.md (전 레이어 공통). 이 파일은 그 사본을
  spec-kit 권위 슬롯(.specify/memory/constitution.md)에 동기화한 것이다. 둘은 항상 일치해야 한다.
-->

3-레이어 하니스(① PREREQUISITE → ② PO-DEV-CHAT → ③ AI-WEB-DEV)에서 ③(AI-WEB-DEV)가
②의 **spec-pack(PACK-\*) 계약**을 **SDD(spec-kit) + TDD**로 구현할 때 따르는 불변 규칙이다.

## Core Principles

### I. Screen Model이 단일 진실원 (NON-NEGOTIABLE)

screen model(YAML)이 단일 원본(single source of truth)이다. HTML 렌더·프론트엔드 코드는 **파생 뷰**이며 model을 거치지 않고 직접 편집하지 않는다. spec-kit이 생성하는 어떤 아티팩트도 계약(screen model/spec-pack)을 재정의할 수 없다 — 구현만 한다. 계약 변경은 §Change Order로만.

### II. Design System 폐쇄 (Closure)

DS(`foundation/design-system/ds-allowlist.md`) 허용 집합 밖의 컴포넌트는 model·코드에 들어올 수 없다. 새 컴포넌트 발명 금지. lint L1과 code-reviewer가 강제한다. 스타일은 design token 그대로 사용, 하드코딩 금지.

### III. 스파인 ID 추적 (NON-NEGOTIABLE)

모든 아티팩트는 스파인 ID를 가지며 끝까지 추적된다:
`SCR → CMP → REQ → acceptance → PACK → task(T###) → test → commit`.
접두사: `SCR-`(화면) `CMP-`(컴포넌트) `REQ-`(요구사항) `NOTE-`/`NFR-`(노트) `PACK-`(도메인 팩) `SPEC-`(baseline) `T###`(태스크) `DP-`(design page). spec-kit의 spec/plan/tasks/test/commit은 이 ID를 보존해야 한다(`01-PREREQUISITE/.claude/rules/spine-ids.md`).

### IV. Test-First TDD (NON-NEGOTIABLE)

테스트 없는 구현을 금지한다. 모든 T### 구현 태스크는 **red → green → refactor**를 따른다:
1. **red** — 구현 전에 실패하는 테스트를 먼저 작성한다(test-author). 작성 직후 **실패를 기계적으로 증명**(러너 실행·실패 로그)해야 한다. 처음부터 통과하면 무효.
2. **green** — 테스트를 통과시키는 **최소 구현**만.
3. **refactor** — green을 유지하며 중복·복잡도 제거.
요구: **2계층 테스트(API 레벨 + 화면 레벨)**. decision table의 모든 row, state machine의 모든 전이는 최소 1 테스트로 커버한다. `tdd-gate.py` hook이 테스트 없는/실패 commit을 차단한다. 예외: Phase α scaffold(`[SCAFFOLD]` 마커)만 면제(`03-AI-WEB-DEV/.claude/rules/tdd-policy.md`).

### V. 단계 게이트 — 구현 전 승인 (NON-NEGOTIABLE)

계약은 ② **Gate A**(confirmed)를 통과한 것만 ③로 인계된다. ③에서 `/speckit-tasks` 완료 후 구현 전 **Gate B**(개발자 소유)를 통과해야 한다: Data Model·ERD·API 확정, `complexity:high` BL의 bl-analyst open decision = 0, 모든 구현 태스크에 대응 테스트 태스크 존재, 개발자 approve. Gate B 미통과 시 어떤 구현 commit도 금지(`03-AI-WEB-DEV/.claude/rules/gate-b-checklist.md`).

### VI. 커밋 규칙 — 스파인 ID 필수 (NON-NEGOTIABLE)

커밋 메시지 형식: `[<PACK|SPEC|MOD>/<task>] <요약> (REQ-...)`. 예: `[PACK-ORDER/T001] 주문 목록 조회 API (REQ-ORDER-LIST.001)`. `commit-spine-id.py` hook이 스파인 ID 없는 commit을 차단한다. 예외: `[SCAFFOLD]`(tdd-gate skip, spine-id 적용), `[CO/<dismiss|amend|regenerate>]`(Change Order, re-pin 버전 표기). 구조 변경과 행위 변경은 분리 커밋(Tidy First)한다(`03-AI-WEB-DEV/.claude/rules/commit-convention.md`).

### VII. Optimistic Locking & Headless Patch

저장은 `version` 필드 체크 기반(last-write-wins 금지, 충돌 시 409). headless 호출은 raw HTML이 아니라 screen model patch를 반환한다.

## Scope & Boundaries

- *명세*는 ①, *계약(정의)*은 ②, *구현(코드)*은 ③의 책임이다. ③는 **새 계약·요구사항·규칙을 만들지 않는다**.
- ③의 입력: `input/spec-pack/PACK-*/spec.yaml`(② 발행) + `input/harness/`의 SPEC-000 명세 + ①의 tech-stack·design 자산. spec-kit의 feature spec(`spec.md`)은 이 spec-pack에서 파생되어야 하며, 새 화면·REQ를 발명하지 않는다.
- 프레임워크·테스트 스택은 **프로젝트마다 다르다**. 특정 스택을 가정하지 않는다. ① PREREQUISITE에서 `/speckit-constitution`으로 정의해 `01-PREREQUISITE/output/foundation/decisions/tech-stack.md`에 핀으로 박는다(§Technology Stack). 모든 스택 의존 값(테스트 러너·`HARNESS_TEST_CMD`·shell 확장자 등)은 그 핀을 참조한다.

## Development Workflow (spec-kit ↔ harness 매핑)

| spec-kit 명령 | 하니스 단계 | 입력 | 강제 |
|---|---|---|---|
| `/speckit-constitution` | 규범 동기화 | 01 constitution | git initialize |
| `/speckit-specify` | Phase β scope 확정 | PACK-\* meta+scope+open_items | feature 브랜치 |
| `/speckit-clarify` | open_items·deferred 해소 (HITL) | spec-pack open_items | Gate A 전제 확인 |
| `/speckit-plan` | Data Model·ERD·API·wiring | screens+actions+notes(complexity) | complexity:high→bl-analyst |
| `/speckit-tasks` | T### test-first 분해 | actions+acceptance+bl-analyst | 대응 테스트 태스크 필수 |
| `/speckit-analyze` | **Gate B 일관성 검사** | spec+plan+tasks+이 constitution | 위반=CRITICAL, 미해소 시 구현 금지 |
| `/speckit-checklist` | Gate A/B 체크리스트 | 위 전부 | 게이트 통과 확인 |
| `/speckit-implement` | TDD 루프 구현 | acceptance+shell_ref | tdd-gate + commit-spine-id |

원칙: `/speckit-clarify` → (`/speckit-checklist`) → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze`(Gate B) → `/speckit-implement`. 각 단계 전후 git auto-commit은 스파인 ID 메시지를 사용한다.

## Technology Stack (per-project — `/speckit-constitution`이 정의)

기술 스택은 하니스에 고정돼 있지 않다. **프로젝트마다 ① PREREQUISITE에서 `/speckit-constitution`으로 결정**하고 `01-PREREQUISITE/output/foundation/decisions/tech-stack.md`에 핀으로 기록한다. ②·③의 모든 산출물(scaffold·plan·tasks·test·tdd-gate)은 이 핀만 참조하며 특정 프레임워크를 가정하지 않는다.

| 슬롯 | 무엇 | 예시(고정값 아님) |
|---|---|---|
| frontend.framework | 프론트 프레임워크·언어·빌드 | [프로젝트마다] — 예: React+Vite+TS / Vue / Svelte |
| frontend.test | 화면 레벨 테스트 러너(컴포넌트 + E2E) | 예: Vitest+RTL / Playwright |
| backend.framework | 백엔드 프레임워크·언어 | [프로젝트마다] — 예: Spring Boot / NestJS / FastAPI |
| backend.test | API 레벨 테스트 러너 | 예: JUnit+RestAssured / Jest+supertest / pytest+httpx |
| storage | DB·마이그레이션 | [프로젝트마다] |
| `HARNESS_TEST_CMD` | tdd-gate가 실행할 2계층 테스트 명령 | 위 러너에서 파생 |
| shell.ext / structure | scaffold가 만들 shell 확장자·구조 | frontend.framework에서 파생 (예: `.tsx`/`src/pages`) |

상세 슬롯·기입 규칙: `01-PREREQUISITE/output/foundation/decisions/tech-stack.md`. 변경은 `/speckit-constitution` 재실행으로만(전 레이어 동기화).

## Governance

이 constitution은 ③의 모든 다른 관행에 우선한다. 위반은 `/speckit-analyze`에서 CRITICAL로 분류되며, 원칙 희석·재해석·무시가 아니라 spec/plan/tasks를 수정해 해소한다. 원칙 자체의 변경은 ①의 `.claude/rules/constitution.md`를 먼저 고치고 이 파일을 동기화하는 별도 절차로만 가능하다(전 레이어 README·CLAUDE.md 동반 갱신).

**Version**: 1.0.0 | **Ratified**: 2026-06-15 | **Last Amended**: 2026-06-15 | **Source**: `01-PREREQUISITE/.claude/rules/constitution.md`
