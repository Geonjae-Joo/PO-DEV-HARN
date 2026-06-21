> ⚠️ 이 문서는 구 `03-AI-WEB-DEV/` 레이어 기준 경로를 일부 포함합니다. 신구조(packages/plugin-ai-web-dev + projects/<id>/) 매핑은 `docs/MIGRATION-PLAN.md` 참조.

﻿# ③ AI-WEB-DEV — 개발 레이어 (SDD + TDD 하네스)

> Spec 팩마다 반복. 주체: 개발자 (VSCode + Claude Code).
> ①의 하네스 자산과 ②의 spec 팩을 받아 **SDD + TDD로 단 하나의 웹앱(`app_repo`)을 완성**한다.
> 파일럿은 개발자가 로컬에서 직접 구동 — 사람을 루프 안에 두고 측정한다.

---

## 이 레이어의 역할

상류의 **계약을 실행 가능한 코드로 전환**하는 단계다. 새로 정의하지 않는다 — ①의 규칙·기술스택·디자인 자산과 ②의 확정 screen model(=계약)을 **받아서**, test-first로 `app_repo` 하나에 구현·통합한다.

| 무엇을 | 어떻게 |
|---|---|
| 공통 기능·운영 확립 | **Phase 0** — SPEC-000(기능)·SPEC-OPS-000(배포·CI/CD·관측성)을 받아 각 요건의 *전달 방식*(가이드 코드블럭 vs 직접 코드 주입)을 명세화하고 그에 맞춰 산출 |
| 전체 화면 골격 일괄 생성 | **Phase α** — confirmed screen model → 프론트엔드 shell 일괄 scaffold (①의 tech-stack.md 프레임워크, layout만, wiring 없음) |
| 도메인 기능 구현 | **Phase β** — spec 팩 단위 backend + frontend wiring, T### TDD 루프. ②의 ENT-/EXT- 계약 → data-model·ERD·어댑터 *파생* |
| 통합·비기능 요건 | **Phase γ** — ②의 JRN-* 여정 → Playwright(+BDD) E2E + 성능·동시성·보안·관측성 |
| 계약 변경 흡수 | Change Order — 자동 재생성 금지, pin·freeze 위에서 개발자 판정 |

**경계 원칙:** 이 레이어는 **코드만** 만든다. 화면·요구사항의 *정의*는 ②, 불변 규칙·기술스택·DS·SPEC-000 *명세*는 ①의 책임이다. ③는 그 명세를 **구현(how)**할 뿐 새 계약을 만들지 않는다.

---

## 개발 4단계 개요

| 단계 | 이름 | 범위 | 주기 |
|---|---|---|---|
| Phase 0 | SPEC-000·SPEC-OPS-000 Baseline | 앱 골격·인증·공통 인프라 + 배포·CI/CD·관측성 | 프로젝트 1회 |
| Phase α | Layout Scaffold | 전체 화면 프론트엔드 shell 일괄 생성 (①의 프레임워크에서 파생) | 전체 screen 확정 후 1회 |
| Phase β | Spec Pack Iteration | 도메인 팩별 backend + frontend wiring (ENT-/EXT- → data-model·ERD 파생) | 팩마다 반복 |
| Phase γ | Integration & NFR | JRN-* → Playwright E2E + 성능·동시성·보안·관측성 | 배포 전 |

---

## Phase 0 — SPEC-000·SPEC-OPS-000 Baseline

프로젝트 1회. spec 팩 iteration 시작 전에 완료한다.
①이 작성한 **SPEC-000(공통 기능 명세)과 SPEC-OPS-000(운영 명세: 배포·CI/CD·형상관리·관측성)**, 그리고 `ops-stack.md`(도구 결정)를 받아, **각 요건을 어떤 방식으로 전달할지 먼저 명세화**하고 그 결정에 따라 산출한다. Phase 0의 핵심 산출은 "코드"가 아니라 **전달 방식 결정(delivery manifest) + 그에 맞는 자산**이다.

> **운영 요건(SPEC-OPS-000):** CI 파이프라인·Dockerfile/Helm·관측성 SDK(Phoenix/Langfuse) 주입은 대개 표준이라 **모드 B**(완성 코드 주입), 배포 타깃별 차이(k8s vs 온프렘 등)는 **모드 A** 가이드로 보강한다. 도구 선택은 `ops-stack.md`를 따른다.

### 공통 기능 전달 방식 — 2가지 모드

각 공통 기능(로그인, SSO, RBAC, admin, 공통 레이아웃 …)에 대해 **둘 중 하나**를 지정한다.

| 모드 | 무엇 | 언제 | 산출 위치 | 이후 사용 |
|---|---|---|---|---|
| **A. 가이드 코드블럭** | 동작하는 *예시 코드 블럭 + 패턴 설명*을 가이드로 제공 (전체 구현이 아님) | 프로젝트마다 구현이 달라지거나, 도메인 맥락에 맞춰 변형이 필요한 기능 (예: 권한 조건부 렌더 패턴, 감사 로그 삽입 패턴) | `app_repo/.claude/skills/baseline-guides/` 에 reference 스킬로 적재 | Phase β에서 모델이 스킬로 로드 → 도메인 코드에 맞게 적용 |
| **B. 직접 코드 주입** | *완성된 동작 코드*를 통째로 app_repo에 구현·주입 (테스트 green) | 모든 프로젝트가 동일하게 쓰는, 변형 불필요한 기능 (예: 로그인/SSO 모듈, JWT 필터, RBAC 엔티티/미들웨어) | `app_repo/backend/`·`frontend/` 에 실제 코드 + 테스트 | 그대로 동작. Phase β는 호출만 |

> **판정 기준 한 줄:** "프로젝트마다 변형되나?" → 예면 **A(가이드)**, 아니면 **B(직접 주입)**. 애매하면 B로 골격을 주입하고 변형 지점만 A 가이드로 보강한다.

### 흐름

```
foundation/platform-baseline/ 에서 SPEC-000.md + SPEC-OPS-000.md(①이 작성한 명세) + foundation/decisions/ops-stack.md(도구 결정) 수신
  │
  ▼
/speckit.specify  SPEC-000·SPEC-OPS-000 scope 확인 + ★ 요건별 전달 모드(A/B) 결정
                  → baseline-delivery-manifest.yaml 작성 (기능·운영요건 → mode:A|B + 사유)
  │
  ├─[mode B 기능]──────────────────────────────────────────┐
  │  /speckit.plan → /speckit.tasks(test-first) →            │
  │  Gate B → /speckit.implement → commit → code-reviewer    │  → app_repo 실제 코드(green)
  │                                                          │
  └─[mode A 기능]──────────────────────────────────────────┘
     예시 코드블럭 + 패턴 가이드 작성
     → app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md   → Phase β가 로드해 적용
```

**산출물**:
- `baseline-delivery-manifest.yaml` — 공통 기능별 전달 모드(A/B)와 사유 (전체 baseline의 단일 진실원)
- **(B)** 앱 라우팅 구조, 인증/SSO/RBAC 실제 구현 + 테스트, 공통 레이아웃 컴포넌트, DB 연결, CI 설정
- **(A)** `baseline-guides/` reference 스킬 — Phase β가 도메인 구현 시 로드하는 예시 코드블럭·패턴

> **①과의 경계:** *무엇이 공통 기능인지(scope·요구사항)*는 ①의 SPEC-000이 정한다. *그것을 A로 줄지 B로 줄지, 그리고 실제 코드/가이드*는 ③ Phase 0가 만든다. ①은 baseline을 구현하지 않는다 — 명세까지만.

---

## Phase α — Layout Scaffold

**모든 확정 screen model → 프론트엔드 페이지 컴포넌트 shell 일괄 생성.**
대상 프레임워크·파일 확장자·디렉터리 구조는 **①의 tech-stack.md `frontend.framework`에서 파생**한다(고정값 아님 — 예: React→`.tsx`/`src/pages`, Vue→`.vue`/`src/views`, Svelte→`.svelte`/`src/routes`). screen model 자체는 프레임워크 중립(위치·DS 컴포넌트 종류)이라, scaffold는 그 모델을 선택된 프레임워크로 투영할 뿐이다.
각 화면 컴포넌트를 layout만 있는 상태(데이터 없음, 이벤트 없음)로 만든다.
이후 Phase β에서 각 팩이 shell에 wiring만 추가한다 — layout을 다시 건드리지 않는다.

```
② model_repo/screens/*.yaml (전체 confirmed) 수신
② model_repo/renders/*.render.html (참조용)
  │
  ▼
/speckit.scaffold  전체 화면 shell 일괄 생성
  - screen model position 그대로 DS 컴포넌트 배치
  - props stub (placeholder 데이터)
  - 라우팅 연결
  - 이벤트 핸들러 없음, API 호출 없음
  │
  ▼
hook: layout-hash-guard.py (진입 가드 — 각 화면 재렌더 layout_hash 가 ②확정 pinned_contract와 일치해야 진행. 불일치 시 빌드 차단)
hook: tdd-gate.py (scaffold는 테스트 불필요 — skip 마커)
hook: commit-spine-id.py → [SCAFFOLD] 커밋
```

**산출물**: `app_repo/frontend/` 아래 모든 화면의 페이지 shell 컴포넌트 (경로·확장자는 ①의 프레임워크 규약 — 예: React `src/pages/*.tsx`)

**왜 선행하는가**:
- 한 화면이 여러 팩에 걸쳐 개발될 때 layout 중복·충돌 방지
- 팩별 speckit.implement가 layout 결정 없이 wiring에만 집중 가능
- 앱을 띄우면 모든 화면이 layout 상태로 즉시 확인 가능 (walking skeleton)

---

## Phase β — Spec Pack Iteration

spec 팩 단위로 반복한다. **팩 = 하나의 도메인 모듈** (단일 feature가 아님).

```
PACK-X 수신 (model_repo/specs/PACK-X/)
  │
  ▼
/speckit.specify
  - 팩 scope 확인 (묶인 화면, REQ/CMP 범위)
  - 필요 시 sub-pack으로 재분할
  - open_items의 deferred 항목 처리 방향 결정
  │
  ▼
/speckit.plan
  - Data Model + ERD — ②의 ENT-*.yaml/EXT-*.yaml 계약에서 *파생* (물리 타입·테이블·인덱스·FK 결정)
    ※ 새 엔티티를 발명하지 않는다. 계약에 없는 데이터가 필요하면 Change Order로 ②에 요청
  - API 설계 (endpoint, request/response) — EXT- 계약은 어댑터로 구현
  - BL 복잡 노트(complexity:high) → bl-analyst subagent 호출
  - frontend wiring 계획 (shell_ref 기준, 어느 컴포넌트에 무엇을 연결할지)
  │
  ▼
/speckit.tasks
  - T### 태스크 목록 생성
  - test-first 정렬: 각 구현 태스크 앞에 테스트 태스크 배치
  - [P] 병렬 마커: 독립적 태스크는 병렬 표시
  - backend 태스크 → frontend wiring 태스크 순서
  │
  ▼
Gate B  (개발자 소유 — .claude/rules/gate-b-checklist.md)
  Data Model·ERD·BL·Task 전체 확정
  bl-analyst 미해결 항목 있으면 통과 불가
  PO는 acceptance 비차단 소프트 리뷰만
  approve 전 구현 금지
  │
  ▼
/speckit.implement  (T### 순서대로 반복)
  ① subagent: test-author
     acceptance(Gherkin) + worked examples → 실패 테스트 먼저 생성
     (API 레벨 + 화면 레벨 2계층)
  ② 구현: red → green → refactor
  ③ hook: tdd-gate.py — 테스트 없음/실패 시 commit 차단
  ④ hook: commit-spine-id.py → [PACK-ORDER/T001] 메시지 자동 커밋
  │
  ▼
subagent: code-reviewer
  DS 준수 · 보안 · 코딩 스타일 · TDD 충족 · 스파인 ID 검증
  │
  ▼
integration 브랜치 머지 → PR
```

**Frontend wiring 원칙**:
- Phase α에서 만든 shell 컴포넌트에 API hook, 상태 관리, 권한 조건부 렌더, 에러 처리를 추가
- layout 구조(컴포넌트 위치·배치)는 건드리지 않는다
- 신규 컴포넌트(modal, drawer 등 screen model에 없던 것): 이 팩에서 shell + wiring 동시 생성

---

## Phase γ — Integration & NFR

```
② model_repo/journeys/JRN-*.yaml (여러 팩/화면에 걸친 여정) 수신
  │
  ▼
E2E 구현 — JRN-* 1개 → Playwright(+BDD) E2E 스펙 1개
  - 각 step → 거치는 화면 action의 acceptance(Gherkin) 재사용 (새 시나리오 발명 금지)
  - 커밋: [E2E/JRN-…] (commit-convention.md)
  - 추적: JRN- → SCR/action → e2e-test → commit
  │
  ▼
subagent: code-reviewer 전체 검토
NFR 처리 (성능·동시성·보안·감사)
관측성 검증 (SPEC-OPS-000 OPS-OBS — Phoenix/Langfuse 트레이싱 동작 확인)
배포 준비 (SPEC-OPS-000 OPS-CD — ops-stack.md 배포 타깃별)
```

**E2E 원칙**: 시나리오의 출처는 ②의 `JRN-*` 계약이다. ③는 여정을 새로 정의하지 않고 Playwright로 *구현*만 한다. 도구(Playwright)·CI 연동은 `ops-stack.md`/SPEC-OPS-000을 따른다.

---

## 변경 처리 — Change Order (자동 재생성 안 함)

```
1. Pin      spec은 생성 시점 계약 버전에 고정. 얼어붙은 스냅샷 위에서 작업.
2. Freeze   구현 중 화면은 소프트 프리즈. PO 편집은 change-order 큐에 누적.
3. Change Order  PO 재확정 시 스파인 ID 단위 diff + blast radius 계산 → 변경 지시서.
4. 개발자 판정
   - dismiss    외관/무관 변경 → re-pin
   - amend      경미한 수정 → 제자리 수정 후 re-pin
   - regenerate 중대한 변경 → 해당 팩만 재생성 + 새 Gate B
5. TDD 백스톱  acceptance 변경 시 기존 테스트가 깨짐(breaking). REQ 추가만이면 새 task(additive).
```

---

## Harness 자산 (.claude/)

### Commands — 개발자가 호출하는 단계별 명령

| 파일 | 설명 |
|---|---|
| `speckit.specify.md` | 팩 scope 확인·확정. 너무 크면 sub-pack 분할. open_items 처리 방향 결정. |
| `speckit.scaffold.md` | **[Phase α 전용]** 전체 확정 screen model → 프론트엔드 shell 컴포넌트 일괄 생성 (①의 `frontend.framework`에서 확장자·구조 파생). |
| `speckit.plan.md` | 도메인 Data Model·ERD·API 설계. **②의 ENT-/EXT- 계약에서 물리 설계 파생**(발명 금지). complexity:high 노트 → bl-analyst 호출. |
| `speckit.tasks.md` | T### 태스크 목록 생성. test-first 정렬. [P] 병렬 마커. |
| `speckit.implement.md` | T### 단위 TDD 구현 루프. test-author → red → green → refactor → commit. |

### Skills — 모델이 필요 시 로드하는 상세 가이드

| 파일 | 설명 |
|---|---|
| `design-system-usage/SKILL.md` | DS 컴포넌트를 ①의 프론트엔드 프레임워크(예: React)로 구현하는 방법. design token 참조 규칙. shell 생성 패턴. |
| `coding-style/SKILL.md` | ①의 tech-stack.md가 정한 스택의 코딩 컨벤션(패키지 구조, 네이밍, 예외 처리). 현재 예시: Spring Boot + React. |
| `complex-bl/SKILL.md` | decision table·state machine을 코드로 구현하는 방법. bl-analyst 산출물 해석·적용. |
| `baseline-guides/SKILL.md` | **[Phase 0 모드 A 템플릿]** 공통 기능 가이드의 *산출 형식*을 정의하는 하네스 스킬. Phase 0가 mode:A 기능마다 이 템플릿에 맞춰 `app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md`(예시 코드블럭 + 적용 패턴)를 생성하고, Phase β가 도메인 코드 구현 시 로드해 변형 적용 (예: 권한 조건부 렌더, 감사 로그 삽입). |

### Hooks — 생애주기 이벤트 자동 실행 (AI 없는 결정론)

| 파일 | 트리거 | 설명 |
|---|---|---|
| `tdd-gate.py` | commit-msg | 테스트 없음/실패 시 commit 차단(blocking). 테스트 러너 미탐지+`HARNESS_TEST_CMD` 미설정 시에도 **차단**(silent-pass 폐지) — 의도적 우회는 `HARNESS_TDD_ALLOW_NO_RUNNER=1`. 테스트 파일은 네이밍 컨벤션(`*.test.*`/`*_test.*`/`test/` 등)으로 판별(spec-pack `specs/` 오인 안 함). `[SCAFFOLD]` skip. |
| `commit-spine-id.py` | commit-msg | 커밋 메시지에 스파인 ID 포함 여부 검증(blocking). 형식: `[<PACK\|SPEC\|MOD>/<task>] 요약 (REQ-...)`. PACK/MOD은 REQ- 필수, **SPEC-은 REQ- 또는 `(baseline)`/`(ops baseline)` 사유 토큰 필수**. `[SCAFFOLD]`·`[CO/...]`·`[E2E/JRN-...]`·`[spec-kit/...]` prefix는 예외. |
| `layout-hash-guard.py` | Phase α 진입 | 각 pack의 `screens[].yaml_ref`(SCR)를 ②와 동일 엔진(`harness-core/render/pins`)으로 재렌더해 `pinned_contract.layout_hash`와 비교(blocking). 불일치(②확정 위치 변경)면 **빌드 차단**(exit 1). `layout_hash` 미발행(placeholder)이면 warn·비차단. `render_hash` 불일치는 엔진 버전 의존성이 커 warn(비차단). 사용: `layout-hash-guard.py --root <project>` 또는 `<spec.yaml ...>`. (ADR-002 §5 ③) |
| `manifest-sync.py` | post-commit | `model_repo/specs/PACK-*` → `app_repo/specs/` 동기화 + shell_ref 갱신. 비차단(non-blocking) — 실패해도 commit 유지. |
| `git-hooks.manifest.json` | — | 위 3개 git 훅의 생애주기 선언(pre-commit 차단 체인 + post-commit 동기화)과 인자·blocking 여부를 한곳에 정의한 **문서용 매니페스트**(설치기가 파싱하지 않음). 파일명은 Claude Code 플러그인 훅 규약(`hooks/hooks.json`)과 구분하기 위해 `git-hooks.manifest.json` 사용. |
| `install-git-hooks.sh` | — | 이 매니페스트가 선언한 git 훅을 실제로 설치(bash/Git Bash·Linux·macOS). 메시지 파일이 필요한 tdd-gate·commit-spine-id는 `commit-msg`, manifest-sync는 `post-commit` 훅으로 `.git/hooks/`에 설치. `PYTHON`·`HARNESS_TEST_CMD` 환경변수 지원. |
| `install-git-hooks.ps1` | — | 동일 설치기의 Windows/PowerShell 버전(설치되는 훅 본문은 셸 스크립트). |

### Subagents — 격리 컨텍스트 전문 에이전트

| 파일 | 설명 |
|---|---|
| `bl-analyst.md` | complexity:high 노트를 분석해 decision table·state machine·worked examples 생성. speckit.plan 중 호출. |
| `test-author.md` | actions의 acceptance(Gherkin) + worked examples에서 실패 테스트 먼저 생성. API·화면 2계층. speckit.implement 시작 시 호출. |
| `code-reviewer.md` | DS 준수·보안·코딩 스타일·TDD 충족·스파인 ID·Change Order blast radius 검증. |

> **팩 (재)생성은 ③에 없다.** confirmed 화면 → PACK-* 분해는 ②의 `spec-generator` 스킬 책임이다. Change Order가 `regenerate`로 판정되면 PO 재확정 → ②의 spec-generator가 해당 팩만 재발행 → ③가 소비한다. ③는 *판정(dismiss/amend/regenerate) + blast radius*까지만 수행한다(경계 원칙: ③는 새 계약을 만들지 않는다).

### Rules — 변경 없는 규칙 (hook·CI가 강제)

| 파일 | 설명 |
|---|---|
| `gate-b-checklist.md` | Gate B 통과 조건. Data Model·ERD·BL·Task 확정 + bl_sections 미해결 0 + 개발자 approve. |
| `tdd-policy.md` | red→green→refactor 3겹 강제. 테스트 없는 구현 금지. |
| `commit-convention.md` | `[<PACK\|SPEC\|MOD>/<task>] 요약 (REQ-...)` 형식. scaffold는 `[SCAFFOLD]`, Change Order는 `[CO/<dismiss\|amend\|regenerate>]` prefix. |
| `change-order-policy.md` | Pin·Freeze·Change Order·dismiss/amend/regenerate 판정 규칙. |

---

## 폴더 트리

```
03-AI-WEB-DEV/
├── README.md
├── PLAN-speckit-tdd-fusion.md      # speckit + TDD 융합 설계 노트
├── SPECKIT-HARNESS-INTEGRATION.md  # speckit ↔ 하네스 통합 가이드
├── input/
│   ├── spec-pack/          # ②의 spec 팩 (PACK-X/ 단위)
│   └── harness/            # ①의 .claude/(commands·skills·hooks·agents·불변 rules: constitution·spine-ids·ds-closure) + foundation(design-system·design-pages·decisions: tech-stack·ops-stack·link-manifest) + SPEC-000·SPEC-OPS-000 명세
├── commands/
│   ├── speckit.specify.md
│   ├── speckit.scaffold.md  # Phase α 전용
│   ├── speckit.plan.md
│   ├── speckit.tasks.md
│   └── speckit.implement.md
├── skills/
│   ├── design-system-usage/SKILL.md
│   ├── coding-style/SKILL.md
│   ├── complex-bl/SKILL.md
│   └── baseline-guides/SKILL.md   # [Phase 0 모드 A] feature별 가이드 스킬 생성 템플릿
├── .claude/
│   ├── hooks/
│   │   ├── tdd-gate.py
│   │   ├── commit-spine-id.py
│   │   ├── manifest-sync.py
│   │   ├── git-hooks.manifest.json # git 훅 생애주기 선언 (문서용, pre/post-commit 체인)
│   │   ├── install-git-hooks.sh   # git 훅 설치기 (bash)
│   │   └── install-git-hooks.ps1  # git 훅 설치기 (PowerShell)
│   ├── agents/
│   │   ├── bl-analyst.md
│   │   ├── test-author.md
│   │   └── code-reviewer.md
│   ├── rules/
│   │   ├── gate-b-checklist.md
│   │   ├── tdd-policy.md
│   │   ├── commit-convention.md
│   │   └── change-order-policy.md
│   └── skills/                    # (기존 skills/ → .claude/skills/)
└── output/
    └── app_repo/            # ★ 단 하나의 웹앱
        ├── .claude/         # 하네스 자산 (app_repo 안에 실제 위치)
        │   └── skills/
        │       └── baseline-guides/   # [Phase 0 모드 A] 공통 기능 예시 코드블럭·패턴 가이드
        ├── baseline-delivery-manifest.yaml  # [Phase 0] 공통 기능별 전달 모드(A/B)+사유
        ├── backend/         # 백엔드(①의 tech-stack.md, 예: Spring Boot) — 테스트 green 코드 ([모드 B] baseline 구현 포함)
        ├── frontend/
        │   └── src/pages/   # Phase α shell → Phase β wiring 완료
        ├── e2e/             # [Phase γ] Playwright(+BDD) — JRN-* 여정 E2E
        └── specs/           # 동기화된 spec 팩 (ENT-/EXT-/JRN- ref 포함)
```

---

## Input / Output

| 구분 | 무엇 | 출처/목적지 |
|---|---|---|
| **Input ← ①** | `.claude/` 하네스(commands/skills/hooks/agents **+ 불변 rules: constitution·spine-ids·ds-closure**) + foundation(design-system·design-pages·**decisions: tech-stack·ops-stack**·link-manifest, design token 포함) + **SPEC-000·SPEC-OPS-000 명세(구현 아님)** + 빈 app_repo 골격 | `foundation/` (+ 플러그인 `.claude/`) |
| **Input ← ②** | spec 팩 (screens yaml_ref·render_ref·pinned_contract / scope / **데이터 계약 ENT-/EXT- ref** / actions+acceptance / notes verbatim / **여정 JRN- ref** / open_items) | `model_repo/specs/` |
| **Output (Phase 0)** | `baseline-delivery-manifest.yaml`(기능·운영요건별 A/B 결정) + [B] baseline·ops 구현 코드·테스트(CI·트레이싱 등) + [A] `baseline-guides/` 가이드 스킬 | `output/app_repo/` |
| **Output** | `app_repo/` — 테스트 green 코드 + �