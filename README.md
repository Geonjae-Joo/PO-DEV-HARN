# PO-Dev Harness — 3-Layer 통합 README

> 디자인 자산·계약·코드를 **하나의 웹앱(`app_repo`)으로 수렴**시키는 3-레이어 개발 하네스.
> 세 레이어는 독립 단계가 아니라 **계약 기반 파이프라인**이다: ①이 토대를 깔고 → ②가 계약(screen model)을 만들고 → ③이 계약을 코드로 구현한다.
>
> 이 문서는 세 레이어의 역할·워크플로우·산출물·인계 지점을 한눈에 보는 진입 문서다. 각 레이어의 상세는 하위 README를 참조한다.

---

## 1. 전체 그림

```
┌──────────────────────┐    foundation 자산     ┌──────────────────────┐
│  ① PREREQUISITE       │ ─────────────────────▶ │  ② PO-DEV-CHAT        │
│  준비 (프로젝트 1회)    │   DS·design-guide·     │  화면·요구사항 정의      │
│  개발 리드/운영자        │   design-pages         │  PO (도메인 전문가)      │
└──────────┬───────────┘                        └──────────┬───────────┘
           │                                               │
           │ .claude 하네스(+rules)                          │ PACK-* spec 팩
           │ + SPEC-000 명세 + 빈 app_repo 골격                │ (확정 계약)
           │                                               │
           ▼                                               ▼
        ┌──────────────────────────────────────────────────────┐
        │  ③ AI-WEB-DEV — 개발 (spec 팩마다 반복) · 개발자        │
        │  SDD + TDD로 단 하나의 웹앱을 완성                         │
        │  ┌────────────────────────────────────────────────┐   │
        │  │  app_repo/  ★ 최종 수렴점                          │   │
        │  │   .claude/ (하네스: command·skill·hook·subagent·rule)│ │
        │  │   backend + frontend (스택은 ①의 tech-stack.md)   │   │
        │  │   design-system · specs                           │   │
        │  └────────────────────────────────────────────────┘   │
        └──────────────────────────────┬───────────────────────┘
                                       │ Change Order (③ 판정)
                                       │ dismiss/amend/regenerate
                                       ▼
                          ② 기존 Gate A로 재확정 → 재발행(re-pin)
```

세 레이어가 만드는 산출물은 모두 **스파인 ID로 연결**되어 화면→요구사항→팩→task→test→commit까지 끝까지 추적된다. 화면 model(②)이 단일 진실원이고, 코드(③)와 렌더 HTML은 그로부터 파생된다.

---

## 2. 세 레이어 한눈에

| | ① PREREQUISITE | ② PO-DEV-CHAT | ③ AI-WEB-DEV |
|---|---|---|---|
| **한 줄 정의** | 디자인·규칙·골격 준비 | 화면·요구사항을 계약으로 정의 | 계약을 코드로 구현 |
| **주체** | 개발 리드/운영자 | PO (도메인 전문가) | 개발자 (VSCode + Claude Code) |
| **주기** | 프로젝트당 1회 | 화면마다 반복 | spec 팩마다 반복 |
| **만드는 것** | foundation 자산 + 규칙 + 빈 골격 | screen model + 데이터·여정 계약(PACK-*/ENT-/EXT-/JRN-) | 테스트 green 코드(app_repo) |
| **절대 안 하는 것** | baseline·ops 코드 구현 | 코드 작성 | 새 계약/규칙 정의 |
| **핵심 산출** | design-guide·design-pages·SPEC-000·SPEC-OPS-000 명세 | confirmed screen model + PACK-* 팩(+ENT-/EXT-/JRN-) | `app_repo` + 스파인 ID 커밋 |
| **상세 문서** | [01-PREREQUISITE/README.md](01-PREREQUISITE/README.md) | [02-PO-DEV-CHAT/README.md](02-PO-DEV-CHAT/README.md) | [03-AI-WEB-DEV/README.md](03-AI-WEB-DEV/README.md) |

---

## 3. 전 레이어 공통 하드 룰 (constitution)

세 레이어 모두가 따르는 불변 규칙. ①의 `.claude/rules/constitution.md`에 정의되고 `.claude/`로 번들되어 ②·③의 hook·lint가 기계적으로 강제한다.

1. **단일 진실원** — screen model(YAML)이 원본이다. HTML 렌더·React 코드는 파생 뷰이며 model을 거치지 않고 직접 편집하지 않는다.
2. **스파인 ID** — 모든 아티팩트는 ID를 가진다. 화면→요구사항→팩→task→test→commit이 ID로 끝까지 추적된다.
3. **DS 폐쇄(closure)** — design system 집합 밖의 컴포넌트는 model·design page에 들어올 수 없다. lint L1이 강제한다 (발명 금지).
4. **Optimistic locking** — 저장은 `version` 필드 체크 기반. 동시 편집 충돌을 기계적으로 차단한다.
5. **TDD** — 테스트 없는 구현 금지. red → green → refactor 3겹. `tdd-gate` hook이 commit을 차단한다.
6. **커밋 규칙** — 커밋 메시지에 스파인 ID 포함: `[PACK-ORDER/T001] 요약 (REQ-...)` (baseline은 `[SPEC-000/T###]`).

---

## 4. 스파인 ID 체계

①의 `.claude/rules/spine-ids.md`에 채번 규칙이 고정되고 전 레이어가 공유한다.

| 접두 | 의미 | 생성 레이어 |
|---|---|---|
| `DP-` | design page 템플릿 (DP-MAIN, DP-POPUP …) | ① |
| `SCR-` | screen (화면) | ② |
| `CMP-` | component (화면 내 컴포넌트) | ② |
| `REQ-` | requirement (요구사항) | ② |
| `ENT-` | entity (개념 데이터 엔티티 계약) | ② |
| `EXT-` | external system (외부 연동 계약) | ② |
| `NOTE-` | PO 자유 노트 (verbatim) | ② |
| `NFR-` | 비기능 요구사항 | ② |
| `JRN-` | journey (화면 간 사용자 여정 = E2E 시나리오) | ② |
| `Q-` | HITL 질문 | ② |
| `PRM-` | prompt log 항목 | ② |
| `PACK-` | 도메인 spec 팩 (구현 단위) | ② |
| `SPEC-` | 플랫폼/baseline spec (SPEC-000, SPEC-OPS-000) | ① |
| `T###` | task (구현 단위) | ③ |

**추적 그래프:** `SCR → CMP → REQ → acceptance → PACK → task → test → commit`
- 데이터: `REQ/action → ENT-/EXT- (② 계약) → data-model·ERD (③ 파생) → migration`
- 여정(E2E): `JRN- (② navigate 집계) → SCR/action → Playwright e2e-test (③ Phase γ)`

---

## 5. 레이어별 상세

### ① PREREQUISITE — 준비

PO 작업과 개발이 시작되기 전에 **디자인 자산·규칙·앱 골격을 1회 준비**한다. "빈 흰 캔버스" 문제를 없애는 것이 목적 — PO에게 백지를 주는 대신, 허용집합(design-guide)·페이지 템플릿(design-page)·불변 규칙(constitution)·ID 체계를 상류에서 못 박아 이후 단계가 그 틀 **안에서만** 움직이게 한다.

**워크플로우**: 사용자가 기존 DS를 `input/`에 투입 → `design-guide.md` 작성(허용집합 원본) → `design-page-builder` 스킬로 빈 페이지 템플릿(DP-*) 생성 → rules(ops-stack 포함)·SPEC-000·SPEC-OPS-000 명세 확정 → 빈 `app_repo` 스캐폴드.

**핵심 자산**: `design-page-builder` 스킬(+전용 `design-page-lint.py`), 저장 이벤트 훅 `ds-guide-validate.py`, 공유 규칙 5종(constitution/spine-ids/tech-stack/ds-closure/ops-stack).

**산출물**: `foundation/`(design-system·design-guide·design-pages) + SPEC-000 명세 + **SPEC-OPS-000 명세(배포·CI/CD·관측성)** + `.claude` 하네스 골격(rules 포함) + 빈 `app_repo`.
**baseline·ops 코드는 만들지 않는다** — 무엇이 공통 기능/운영 요건인지 *명세*까지만, 구현은 ③ Phase 0.

### ② PO-DEV-CHAT — 화면·요구사항 정의

PO가 ①의 디자인 자산을 토대로 **화면·요구사항을 계약(screen model YAML)으로 정의·확정**한다. 코드는 절대 쓰지 않고 **계약만** 산출한다. 목표는 "개발자가 화면 하나만 보고 spec을 만들 수 있을 만큼"의 정보 수집이며, 부족하면 HITL로 다시 묻는다.

**워크플로우 — 4 Stage HITL**:

```
Stage 1  layout-recommend   DS 매핑 + design page 선택 + screen model 초안 → patch 루프
            └ 저장 시: on-save-schema-validate(Pre) → on-save-lint-L1~L4(Post) → HTML 렌더
Stage 2  action-interview   interactive 컴포넌트별 순회 인터뷰 → actions[] + Gherkin acceptance
Stage 3  note-intake        PO verbatim 노트 수집 (AI 본문 수정 금지, 태그 제안만)
Stage 4  sufficiency-check  기계 체크 + AI gap 분석 → 누락 시 HITL 재질문
   ▼
Gate A   gate-a-check       lint 0 + 충분성 통과 + 전 action 확정 + PO 승인 → status: confirmed
   ▼
spec-generator              confirmed 화면 → 도메인 단위 PACK-* 팩 발행 → ③ 인계
```

**상태 머신**: `draft → layout_confirmed → actions_in_progress → review → confirmed`

**핵심 자산**: 9개 스킬(layout-recommend·action-interview·note-intake·**entity-intake**·**external-intake**·**journey-map**·sufficiency-check·gate-a-check·spec-generator), 저장 이벤트 훅 2종(schema-validate·lint-L1-L4), 공유 규칙(screen-model-schema-v2·data-contract-schema·journey-schema 외).

**산출물**: `model_repo/`(screens SCR-*.yaml 단일 원본 + **entities ENT-*.yaml + externals EXT-*.yaml + journeys JRN-*.yaml** + renders 파생 HTML + specs PACK-* 팩 + link-manifest).

### ③ AI-WEB-DEV — 개발

상류의 **계약을 실행 가능한 코드로 전환**한다. 새로 정의하지 않고, ①의 규칙·기술스택·자산과 ②의 확정 screen model을 받아 test-first로 `app_repo` 하나에 구현·통합한다.

**워크플로우 — 4 Phase**:

| Phase | 이름 | 하는 일 | 주기 |
|---|---|---|---|
| **0** | SPEC-000·SPEC-OPS-000 Baseline | SPEC-000·SPEC-OPS-000 명세 수신 → 공통 기능·운영(배포/CI·CD/관측성) 전달 모드(A/B) 명세화 → 그에 맞춰 산출 | 1회 |
| **α** | Layout Scaffold | confirmed screen model 전체 → React shell 일괄 생성 (layout만, wiring 없음) | 1회 |
| **β** | Spec Pack Iteration | 팩 단위 backend + frontend wiring, T### TDD 루프. ②의 ENT-/EXT- 계약 → data-model·ERD 파생 | 팩마다 |
| **γ** | Integration & NFR | ②의 JRN-* 여정 → Playwright(+BDD) E2E + 성능·동시성·보안·관측성 검증 | 배포 전 |

**Phase 0의 핵심 — 공통 기능 전달 2모드**: 로그인·SSO·RBAC 등 각 공통 기능에 대해 둘 중 하나를 지정한다.

- **모드 A (가이드 코드블럭)**: 동작하는 *예시 코드 + 패턴*을 `baseline-guides/` 스킬로 제공. 프로젝트마다 변형되는 기능(권한 조건부 렌더, 감사 로그 삽입 등) → Phase β가 로드해 적용.
- **모드 B (직접 코드 주입)**: *완성 코드*를 통째로 app_repo에 구현(테스트 green). 변형 불필요한 기능(로그인/SSO 모듈, JWT 필터, RBAC 엔티티) → Phase β는 호출만.
- 판정 한 줄: **"프로젝트마다 변형되나?"** → 예면 A, 아니면 B. 결과는 `baseline-delivery-manifest.yaml`에 기록.

**핵심 자산**: 5개 speckit 명령(specify·scaffold·plan·tasks·implement), 스킬(design-system-usage·coding-style·complex-bl·baseline-guides), 생애주기 훅(tdd-gate·commit-spine-id·manifest-sync — `hooks.json` 선언 + `install-git-hooks.sh/.ps1`로 `.git/hooks/`에 설치), 서브에이전트(bl-analyst·test-author·code-reviewer), 규칙(gate-b-checklist·tdd-policy·commit-convention·change-order-policy).

**산출물**: `app_repo/` — 테스트 green 코드 + 스파인 ID 커밋 히스토리.

---

## 6. 인계 지점 (Handoff Matrix)

레이어 간 계약은 아래 4개 인계로 정의된다. 모두 양쪽 README에서 항목·위치가 일치하도록 교차 검증되어 있다.

| 인계 | 무엇이 넘어가나 | 출발 → 도착 |
|---|---|---|
| **① → ②** | foundation 전체: design-system(token) + design-guide.md + design-pages(DP-*) | `①/output/foundation/` → `②/input/` |
| **① → ③** | `.claude` 하네스(command·skill·hook·subagent **+ rules**) + foundation 전체 + **SPEC-000·SPEC-OPS-000 명세**(구현 아님) + 빈 app_repo 골격 | `①/output/` → `③/input/harness/` |
| **② → ③** | **PACK-\* spec 팩**: screens(yaml_ref·render_ref·pinned_contract) + scope(REQ-/CMP-) + **데이터 계약(ENT-/EXT- ref)** + actions+acceptance 원문 + notes(verbatim·complexity) + **여정(JRN- ref)** + open_items | `②/model_repo/specs/` → `③/input/spec-pack/` |
| **③ → ②** | **Change Order** 판정 결과: dismiss / amend / regenerate. 별도 ② 스킬 없이 PO가 기존 Gate A 흐름으로 재확정 → spec-generator가 버전 +1로 재발행 | `③` 변경요청 → `②/model_repo` 재확정·re-pin |

**경계 원칙 요약**: *명세*는 ①, *계약(정의)*은 ②, *구현(코드)*은 ③. 어느 레이어도 하류의 책임을 침범하지 않는다. 특히 SPEC-000은 ①이 명세하고 ③ Phase 0가 구현하며, rules는 ①이 작성해 `.claude`로 번들되어 ②·③의 hook이 강제한다.

---

## 7. 자산 배치 규칙 (공통 컨벤션)

세 레이어 모두 동일한 배치 원칙을 따른다:

- **단일 스킬 전용 스크립트·파일** → 그 스킬 폴더 아래 공존 (`skills/<skill>/scripts/`, `skills/<skill>/<rule>.md`). 예: ①의 `design-page-lint.py`, ②의 `sufficiency-check.py`·`gate-a-check.py`·`question-bank.md`.
- **저장 이벤트 훅 / 여러 스킬·레이어 공유 규칙** → `.claude/hooks/`(+`hooks.json`)·`.claude/rules/`. 예: ②의 `on-save-lint`, ①·②의 공유 규칙들.

판별 기준: **"단일 스킬이 직접 호출/소유하는가?"** → 예면 스킬 아래 중첩, 아니면 최상위.

---

## 8. 폴더 구조 (최상위)

```
PO-DEV-Harn/
├── README.md                  # (이 문서) 3-레이어 통합 진입 문서
├── 01-PREREQUISITE/           # ① 준비 — foundation·rules·빈 app_repo 골격
│   ├── input/ .claude/{skills/hooks/rules} output/
│   └── README.md
├── 02-PO-DEV-CHAT/            # ② 화면·요구사항 정의 — screen model 계약
│   ├── .claude/{skills/hooks/rules} output/model_repo/
│   └── README.md
└── 03-AI-WEB-DEV/           # ③ 개발 — app_repo 구현
    ├── input/ .claude/{skills/hooks/subagents/rules} output/app_repo/
    └── README.md
```

---

## 9. 문서 맵

| 보고 싶은 것 | 문서 |
|---|---|
| 전체 파이프라인·인계·하드 룰 (이 문서) | `README.md` |
| 디자인 자산·규칙·골격 준비 방법 | `01-PREREQUISITE/README.md` |
| PO 화면 정의 4-Stage HITL·상태 머신 | `02-PO-DEV-CHAT/README.md` |
| screen model schema v2 전문 | `02-PO-DEV-CHAT/.claude/rules/screen-model-schema-v2.md` |
| 데이터 계약(ENT-/EXT-)·여정(JRN-) 스키마 | `02-PO-DEV-CHAT/.claude/rules/data-contract-schema.md`, `journey-schema.md` |
| 배포·CI/CD·관측성 명세·스택 결정 | `01-PREREQUISITE/output/foundation/platform-baseline/SPEC-OPS-000.md`, `.claude/rules/ops-stack.md` |
| SDD+TDD 개발 4-Phase·baseline 전달 모드 | `03-AI-WEB-DEV/README.md` |
