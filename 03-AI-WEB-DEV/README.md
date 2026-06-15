# ③ AI-WEB-DEV — 개발 레이어 (SDD + TDD 하네스)

> Spec 팩마다 반복. 주체: 개발자 (VSCode + Claude Code).
> ①의 하네스 자산과 ②의 spec 팩을 받아 **SDD + TDD로 단 하나의 웹앱(`app_repo`)을 완성**한다.
> 파일럿은 개발자가 로컬에서 직접 구동 — 사람을 루프 안에 두고 측정한다.

---

## 이 레이어의 역할

상류의 **계약을 실행 가능한 코드로 전환**하는 단계다. 새로 정의하지 않는다 — ①의 규칙·기술스택·디자인 자산과 ②의 확정 screen model(=계약)을 **받아서**, test-first로 `app_repo` 하나에 구현·통합한다.

| 무엇을 | 어떻게 |
|---|---|
| 공통 기능(인증·권한·레이아웃) 확립 | **Phase 0** — SPEC-000을 받아 각 공통 기능의 *전달 방식*(가이드 코드블럭 vs 직접 코드 주입)을 명세화하고 그에 맞춰 산출 |
| 전체 화면 골격 일괄 생성 | **Phase α** — confirmed screen model → React shell 일괄 scaffold (layout만, wiring 없음) |
| 도메인 기능 구현 | **Phase β** — spec 팩 단위 backend + frontend wiring, T### TDD 루프 |
| 통합·비기능 요건 | **Phase γ** — E2E·성능·동시성·보안 |
| 계약 변경 흡수 | Change Order — 자동 재생성 금지, pin·freeze 위에서 개발자 판정 |

**경계 원칙:** 이 레이어는 **코드만** 만든다. 화면·요구사항의 *정의*는 ②, 불변 규칙·기술스택·DS·SPEC-000 *명세*는 ①의 책임이다. ③는 그 명세를 **구현(how)**할 뿐 새 계약을 만들지 않는다.

---

## 개발 4단계 개요

| 단계 | 이름 | 범위 | 주기 |
|---|---|---|---|
| Phase 0 | SPEC-000 Baseline | 앱 골격·인증·공통 인프라 | 프로젝트 1회 |
| Phase α | Layout Scaffold | 전체 화면 React shell 일괄 생성 | 전체 screen 확정 후 1회 |
| Phase β | Spec Pack Iteration | 도메인 팩별 backend + frontend wiring | 팩마다 반복 |
| Phase γ | Integration & NFR | E2E·성능·동시성·보안 | 배포 전 |

---

## Phase 0 — SPEC-000 Baseline

프로젝트 1회. spec 팩 iteration 시작 전에 완료한다.
①이 작성한 SPEC-000(=공통 기능 *명세*)을 받아, **각 공통 기능을 어떤 방식으로 전달할지 먼저 명세화**하고 그 결정에 따라 산출한다. Phase 0의 핵심 산출은 "코드"가 아니라 **전달 방식 결정(delivery manifest) + 그에 맞는 자산**이다.

### 공통 기능 전달 방식 — 2가지 모드

각 공통 기능(로그인, SSO, RBAC, admin, 공통 레이아웃 …)에 대해 **둘 중 하나**를 지정한다.

| 모드 | 무엇 | 언제 | 산출 위치 | 이후 사용 |
|---|---|---|---|---|
| **A. 가이드 코드블럭** | 동작하는 *예시 코드 블럭 + 패턴 설명*을 가이드로 제공 (전체 구현이 아님) | 프로젝트마다 구현이 달라지거나, 도메인 맥락에 맞춰 변형이 필요한 기능 (예: 권한 조건부 렌더 패턴, 감사 로그 삽입 패턴) | `app_repo/.claude/skills/baseline-guides/` 에 reference 스킬로 적재 | Phase β에서 모델이 스킬로 로드 → 도메인 코드에 맞게 적용 |
| **B. 직접 코드 주입** | *완성된 동작 코드*를 통째로 app_repo에 구현·주입 (테스트 green) | 모든 프로젝트가 동일하게 쓰는, 변형 불필요한 기능 (예: 로그인/SSO 모듈, JWT 필터, RBAC 엔티티/미들웨어) | `app_repo/backend/`·`frontend/` 에 실제 코드 + 테스트 | 그대로 동작. Phase β는 호출만 |

> **판정 기준 한 줄:** "프로젝트마다 변형되나?" → 예면 **A(가이드)**, 아니면 **B(직접 주입)**. 애매하면 B로 골격을 주입하고 변형 지점만 A 가이드로 보강한다.

### 흐름

```
input/harness/ 에서 SPEC-000.md(①이 작성한 명세) 수신
  │
  ▼
/speckit.specify  SPEC-000 scope 확인 + ★ 기능별 전달 모드(A/B) 결정
                  → baseline-delivery-manifest.yaml 작성 (기능 → mode:A|B + 사유)
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

**모든 확정 screen model → React 페이지 컴포넌트 shell 일괄 생성.**
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
hook: tdd-gate.py (scaffold는 테스트 불필요 — skip 마커)
hook: commit-spine-id.py → [SCAFFOLD] 커밋
```

**산출물**: `app_repo/frontend/src/pages/` 아래 모든 화면의 React shell 컴포넌트

**왜 선행하는가**:
- 한 화면이 여러 팩에 걸쳐 개발될 때 layout 중복·충돌 방지
- 팩별 speckit.implement가 layout 결정 없이 wiring에만 집중 가능
- 앱을 띄우면 모든 화면이 layout 상태로 즉시 확인 가능 (walking skeleton)

---

## Phase β — Spec Pack Iteration

spec 팩 단위로 반복한다. **팩 = 하나의 도메인 모듈** (단일 feature가 아님).

```
PACK-X 수신 (input/spec-pack/PACK-X/)
  │
  ▼
/speckit.specify
  - 팩 scope 확인 (묶인 화면, REQ/CMP 범위)
  - 필요 시 sub-pack으로 재분할
  - open_items의 deferred 항목 처리 방향 결정
  │
  ▼
/speckit.plan
  - Data Model + ERD (도메인 전체, 한 번에)
  - API 설계 (endpoint, request/response)
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
Gate B  (개발자 소유 — rules/gate-b-checklist.md)
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
  ④ hook: commit-spine-id.py → [SPEC-014/T1] 메시지 자동 커밋
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
E2E 시나리오 (여러 팩에 걸친 플로우)
  → subagent: code-reviewer 전체 검토
  → NFR 처리 (성능·동시성·보안·감사)
  → 배포 준비
```

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
| `speckit.scaffold.md` | **[Phase α 전용]** 전체 확정 screen model → React shell 컴포넌트 일괄 생성. |
| `speckit.plan.md` | 도메인 Data Model, ERD, API 설계. complexity:high 노트 → bl-analyst 호출. |
| `speckit.tasks.md` | T### 태스크 목록 생성. test-first 정렬. [P] 병렬 마커. |
| `speckit.implement.md` | T### 단위 TDD 구현 루프. test-author → red → green → refactor → commit. |

### Skills — 모델이 필요 시 로드하는 상세 가이드

| 파일 | 설명 |
|---|---|
| `design-system-usage/SKILL.md` | DS 컴포넌트를 React로 구현하는 방법. design token 참조 규칙. shell 생성 패턴. |
| `coding-style/SKILL.md` | Spring Boot + React 코딩 컨벤션. 패키지 구조, 네이밍, 예외 처리 패턴. |
| `complex-bl/SKILL.md` | decision table·state machine을 코드로 구현하는 방법. bl-analyst 산출물 해석·적용. |
| `baseline-guides/<feature>/SKILL.md` | **[Phase 0 산출 — 모드 A]** 공통 기능의 예시 코드블럭 + 적용 패턴 가이드. Phase β가 도메인 코드 구현 시 로드해 변형 적용 (예: 권한 조건부 렌더, 감사 로그 삽입). manifest에서 mode:A로 지정된 기능만 존재. |

### Hooks — 생애주기 이벤트 자동 실행 (AI 없는 결정론)

| 파일 | 트리거 | 설명 |
|---|---|---|
| `tdd-gate.py` | pre-commit | 테스트 없음 또는 실패 시 commit 차단. scaffold commit은 skip 마커로 예외 처리. |
| `commit-spine-id.py` | pre-commit | 커밋 메시지에 스파인 ID 포함 여부 검증. 형식: `[SPEC-014/T1] 요약 (REQ-...)`. |
| `manifest-sync.py` | post-commit | spec 팩의 link-manifest를 app_repo/specs/ 와 동기화. |

### Subagents — 격리 컨텍스트 전문 에이전트

| 파일 | 설명 |
|---|---|
| `bl-analyst.md` | complexity:high 노트를 분석해 decision table·state machine·worked examples 생성. speckit.plan 중 호출. |
| `test-author.md` | actions의 acceptance(Gherkin) + worked examples에서 실패 테스트 먼저 생성. API·화면 2계층. speckit.implement 시작 시 호출. |
| `code-reviewer.md` | DS 준수·보안·코딩 스타일·TDD 충족·스파인 ID·Change Order blast radius 검증. |
| `spec-generator.md` | [②에서 호출] 확정 screen model → 수직 슬라이스 팩 분해. 이 레이어에서는 Change Order 재생성 시에만 사용. |

### Rules — 변경 없는 규칙 (hook·CI가 강제)

| 파일 | 설명 |
|---|---|
| `gate-b-checklist.md` | Gate B 통과 조건. Data Model·ERD·BL·Task 확정 + bl_sections 미해결 0 + 개발자 approve. |
| `tdd-policy.md` | red→green→refactor 3겹 강제. 테스트 없는 구현 금지. |
| `commit-convention.md` | `[<SPEC\|MOD>/<task>] 요약 (REQ-...)` 형식. scaffold는 `[SCAFFOLD]` prefix. |
| `change-order-policy.md` | Pin·Freeze·Change Order·dismiss/amend/regenerate 판정 규칙. |

---

## 폴더 트리

```
03-AI-WEB-DEV/
├── README.md
├── input/
│   ├── spec-pack/          # ②의 spec 팩 (PACK-X/ 단위)
│   └── harness/            # ①의 .claude/(commands·skills·hooks·subagents·rules) + foundation(design-system·design-guide·design-pages) + SPEC-000 명세
├── commands/
│   ├── speckit.specify.md
│   ├── speckit.scaffold.md  # Phase α 전용
│   ├── speckit.plan.md
│   ├── speckit.tasks.md
│   └── speckit.implement.md
├── skills/
│   ├── design-system-usage/SKILL.md
│   ├── coding-style/SKILL.md
│   └── complex-bl/SKILL.md
├── hooks/
│   ├── tdd-gate.py
│   ├── commit-spine-id.py
│   └── manifest-sync.py
├── subagents/
│   ├── bl-analyst.md
│   ├── test-author.md
│   ├── code-reviewer.md
│   └── spec-generator.md
├── rules/
│   ├── gate-b-checklist.md
│   ├── tdd-policy.md
│   ├── commit-convention.md
│   └── change-order-policy.md
└── output/
    └── app_repo/            # ★ 단 하나의 웹앱
        ├── .claude/         # 하네스 자산 (app_repo 안에 실제 위치)
        │   └── skills/
        │       └── baseline-guides/   # [Phase 0 모드 A] 공통 기능 예시 코드블럭·패턴 가이드
        ├── baseline-delivery-manifest.yaml  # [Phase 0] 공통 기능별 전달 모드(A/B)+사유
        ├── backend/         # Spring Boot — 테스트 green 코드 ([모드 B] baseline 구현 포함)
        ├── frontend/
        │   └── src/pages/   # Phase α shell → Phase β wiring 완료
        └── specs/           # 동기화된 spec 팩
```

---

## Input / Output

| 구분 | 무엇 | 출처/목적지 |
|---|---|---|
| **Input ← ①** | `.claude/` 하네스(commands/skills/hooks/subagents **+ rules**) + foundation(design-system·design-guide·design-pages, design token 포함) + **SPEC-000 명세(구현 아님)** + 빈 app_repo 골격 | `input/harness/` |
| **Input ← ②** | spec 팩 (screens yaml_ref·render_ref·pinned_contract / scope / actions+acceptance / notes verbatim / open_items) | `input/spec-pack/` |
| **Output (Phase 0)** | `baseline-delivery-manifest.yaml`(기능별 A/B 결정) + [B] baseline 구현 코드·테스트 + [A] `baseline-guides/` 가이드 스킬 | `output/app_repo/` |
| **Output** | `app_repo/` — 테스트 green 코드 + 스파인 ID 커밋 히스토리 | `output/app_repo/` |
| **Output → ②** | Change Order 판정 결과 (dismiss/amend/regenerate + re-pin 버전) | model_repo spec 보드 반영 |

**추적 그래프**: `SCR → CMP → REQ → acceptance → test → SPEC → task → commit`
