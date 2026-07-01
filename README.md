# PO-Dev Harness — 3-Layer 통합 README

> 디자인 자산·계약·코드를 **하나의 웹앱(`app_repo`)으로 수렴**시키는 3-레이어 개발 하네스.
> 세 레이어는 독립 단계가 아니라 **계약 기반 파이프라인**이다: ①이 토대를 깔고 → ②가 계약(screen model)을 만들고 → ③이 계약을 코드로 구현한다.
>
> 이 문서는 세 레이어의 역할·워크플로우·산출물·인계 지점을 한눈에 보는 진입 문서다. 각 레이어의 상세는 하위 README, **실제 개발 절차는 [`USER-GUIDE.md`](USER-GUIDE.md)** 를 참조한다.

> 🏗️ **구조 (2026-06-22 기준):** 시스템 코드는 `packages/`(Tier 1, 전 프로젝트 공용), 프로젝트 데이터는 `projects/<id>/`(Tier 2+3)로 분리되어 있다. 아키텍처 결정은 [`docs/ADR-001`](docs/ADR-001-3runtime-architecture.md)(3-runtime)·[`docs/ADR-002`](docs/ADR-002-deterministic-screen-render.md)(결정론적 렌더), 이행 기록은 [`docs/MIGRATION-PLAN.md`](docs/MIGRATION-PLAN.md), ② 챗봇화 방법은 [`docs/CHATBOT-DEV-GUIDE.md`](docs/CHATBOT-DEV-GUIDE.md) 참조.

---

## 1. 전체 그림

```
┌──────────────────────┐    foundation 자산     ┌──────────────────────┐
│  ① PREREQUISITE       │ ─────────────────────▶ │  ② PO-DEV-CHAT        │
│  준비 (프로젝트 1회)    │   DS·design-guide·     │  화면·요구사항 정의      │
│  개발 리드/운영자        │   design-pages·catalog │  PO (도메인 전문가)      │
└──────────┬───────────┘                        └──────────┬───────────┘
           │                                               │
           │ 플러그인 하네스(+rules)                          │ PACK-* spec 팩
           │ + SPEC-000 명세 + 빈 app_repo 골격                │ (확정 계약)
           │                                               │
           ▼                                               ▼
        ┌──────────────────────────────────────────────────────┐
        │  ③ AI-WEB-DEV — 개발 (spec 팩마다 반복) · 개발자        │
        │  SDD(speckit) + TDD로 단 하나의 웹앱을 완성               │
        │  ┌────────────────────────────────────────────────┐   │
        │  │  app_repo/  ★ 최종 수렴점                          │   │
        │  │   .specify/ (speckit 메커니즘 vendoring)            │   │
        │  │   backend + frontend (스택은 ①의 tech-stack.md)   │   │
        │  │   specs (동기화된 PACK-*)                          │   │
        │  └────────────────────────────────────────────────┘   │
        └──────────────────────────────┬───────────────────────┘
                                       │ Change Order (③ 판정)
                                       │ dismiss/amend/regenerate
                                       ▼
                          ② 기존 Gate A로 재확정 → 재발행(re-pin)
```

세 레이어가 만드는 산출물은 모두 **스파인 ID로 연결**되어 design page→화면→요구사항→팩→task→test→commit까지 끝까지 추적된다. 화면 model(②)이 단일 진실원이고, 코드(③)와 렌더 HTML은 그로부터 파생된다.

**공유 코어 — `packages/harness-core`**: 세 레이어가 단일 출처로 공유하는 Tier 1 시스템 코드.
- `rules/` — 불변 규칙 3종(constitution·spine-ids·ds-closure).
- `lib/` — `ds_closure.py`(DS 폐쇄 검증)·`spine_ledger.py`(스파인 ID 전역 유일성·채번).
- `render/` — **결정론적 렌더 엔진**(ADR-002): YAML screen/design page → 바이트 동일 HTML, DS 카탈로그, DP→SCR 인스턴스화, `layout_hash`/`render_hash` 핀 계산. ①②③이 동일 엔진을 공유한다. **실제 DS 모양**은 ① 준비단계가 1회 컴파일·커밋한 정적 자산(`ds-compiled.css`·`ds-fixtures.json`)에서 읽는다(D8 시각 충실도 레이어). 엔진은 순수 Python으로 Vue/React/Tailwind를 런타임에 쓰지 않으며, 자산이 없으면 와이어프레임으로 폴백한다.

---

## 2. 세 레이어 한눈에

| | ① PREREQUISITE | ② PO-DEV-CHAT | ③ AI-WEB-DEV |
|---|---|---|---|
| **한 줄 정의** | 디자인·규칙·골격 준비 | 화면·요구사항을 계약으로 정의 | 계약을 코드로 구현 |
| **주체** | 개발 리드/운영자 | PO (도메인 전문가) | 개발자 (VSCode + Claude Code) |
| **런타임** | Claude Code 플러그인 | Claude Agent SDK 챗봇(빌드 예정) | Claude Code 플러그인 |
| **주기** | 프로젝트당 1회 | 화면마다 반복 | spec 팩마다 반복 |
| **만드는 것** | foundation 자산 + 규칙 + 빈 골격 | screen model + 데이터·여정 계약(PACK-*/ENT-/EXT-/JRN-) | 테스트 green 코드(app_repo) |
| **절대 안 하는 것** | baseline·ops 코드 구현 | 코드 작성 | 새 계약/규칙 정의 |
| **핵심 산출** | design-guide·design-pages·DS 카탈로그·SPEC-000·SPEC-OPS-000 명세 | confirmed screen model + PACK-* 팩(+ENT-/EXT-/JRN-) | `app_repo` + 스파인 ID 커밋 |
| **패키지** | `packages/plugin-prerequisite` | 능력=`packages/plugin-po-define` · 챗봇=`packages/po-def-chat` | `packages/plugin-ai-web-dev` |
| **상세 문서** | [README](packages/plugin-prerequisite/README.md) | [README](packages/plugin-po-define/README.md) | [README](packages/plugin-ai-web-dev/README.md) |

> ①②③ 모두 `marketplace.json`에 등록된 Claude Code/Cowork 플러그인이다(`/plugin marketplace add .`). ②는 **듀얼 런타임**(ADR-001 R1) — 플러그인으로 IDE·Cowork에서 직접 쓰면서, 같은 소스(skill·hook·rule)를 Agent SDK 챗봇으로도 빌드 예정이다(빌드 방법은 [`docs/CHATBOT-DEV-GUIDE.md`](docs/CHATBOT-DEV-GUIDE.md)). 교차 계약 `screen-model-schema-v2`는 `harness-core/rules/` 단일 출처.

---

## 3. 전 레이어 공통 하드 룰 (constitution)

세 레이어 모두가 따르는 불변 규칙. `packages/harness-core/rules/constitution.md`에 단일 원본으로 정의되고, ①③ 플러그인과 ② 챗봇이 공유해 hook·lint가 기계적으로 강제한다.

1. **단일 진실원** — screen model(YAML)이 원본이다. HTML 렌더·React 코드는 파생 뷰이며 model을 거치지 않고 직접 편집하지 않는다.
2. **스파인 ID** — 모든 아티팩트는 ID를 가진다. design page→화면→요구사항→팩→task→test→commit이 ID로 끝까지 추적된다.
3. **DS 폐쇄(closure)** — design system 집합 밖의 컴포넌트는 model·design page에 들어올 수 없다. lint L1이 강제한다 (발명 금지).
4. **캔버스 봉쇄(canvas-bounds)** — design page의 고정 영역(locked)은 침범 불가, editable 캔버스의 가로 그리드를 초과할 수 없다. lint L5가 강제한다 (ADR-002).
5. **Optimistic locking** — 저장은 `version` 필드 체크 기반. 동시 편집 충돌을 기계적으로 차단한다.
6. **TDD** — 테스트 없는 구현 금지. red → green → refactor 3겹. `tdd-gate` hook이 commit을 차단한다.
7. **커밋 규칙** — 커밋 메시지에 스파인 ID 포함: `[PACK-ORDER/T001] 요약 (REQ-...)` (baseline은 `[SPEC-000/T###]`).

---

## 4. 스파인 ID 체계

`packages/harness-core/rules/spine-ids.md`에 채번 규칙이 고정되고 전 레이어가 공유한다.

| 접두 | 의미 | 생성 레이어 |
|---|---|---|
| `DP-` | design page 템플릿 (DP-MAIN, DP-POPUP …) | ① |
| `SCR-` | screen (화면) — DP에서 인스턴스화 | ② |
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

**추적 그래프:** `DP → SCR → CMP → REQ → acceptance → PACK → task → test → commit`
- 인스턴스화: `DP- (① 템플릿) → SCR- (② 화면)` — DP의 고정 영역을 참조 상속, editable 캔버스만 신규 (ADR-002 §6)
- 데이터: `REQ/action → ENT-/EXT- (② 계약) → data-model·ERD (③ 파생) → migration`
- 여정(E2E): `JRN- (② navigate 집계) → SCR/action → Playwright e2e-test (③ Phase γ)`

---

## 5. 레이어별 상세

### ① PREREQUISITE — 준비

PO 작업과 개발이 시작되기 전에 **디자인 자산·규칙·앱 골격을 1회 준비**한다. "빈 흰 캔버스" 문제를 없애는 것이 목적 — PO에게 백지를 주는 대신, 허용집합(ds-allowlist)·페이지 템플릿(design-page)·시각 카탈로그(DS catalog)·불변 규칙(constitution)·ID 체계를 상류에서 못 박아 이후 단계가 그 틀 **안에서만** 움직이게 한다.

**워크플로우**: DS 투입(두 경로 중 하나 — **[A 수동]** 기존 사내 DS를 `foundation/design-system/ds-source/`에 직접 투입 + `ds-allowlist.md` 수기 작성, 또는 **[B 자동]** `ds-bootstrap` 스킬에 오픈소스 DS 이름만 주면 설치·`tokens.css`·`ds-allowlist.md`까지 자동 생성) → **DS 자산 빌드**(`build_ds_assets.mjs` — `ds-compiled.css`·`ds-fixtures.json`를 1회 컴파일·커밋, ds-bootstrap Phase 9) → `design-page-builder` 스킬로 캔버스 모델(locked/editable·grid·breakpoints) 기반 페이지 템플릿(DP-*) 생성 → 렌더 엔진으로 **실제 DS 모양의 DS 카탈로그·DP 미리보기** 생성 → 불변 rules + 프로젝트 결정(tech-stack·ops-stack)·SPEC-000·SPEC-OPS-000 명세 확정 → 빈 `app_repo` 스캐폴드.

**핵심 자산**: `ds-bootstrap` 스킬(경로 B: DS 부트스트랩 + allowlist 자동 생성), `design-page-builder` 스킬(+전용 `design-page-lint.py`), 저장 이벤트 훅 `ds-guide-validate.py`, 공유 렌더 엔진(`harness-core/render/render_designpage.py`·`render_catalog.py`), 불변 규칙 3종(constitution/spine-ids/ds-closure, `harness-core/rules/`), 프로젝트 결정 2종(tech-stack/ops-stack, `foundation/decisions/`).

**산출물**: `foundation/`(design-system+catalog·design-pages·**decisions: tech-stack·ops-stack**·platform-baseline·link-manifest·VERSION) + SPEC-000 명세 + **SPEC-OPS-000 명세(배포·CI/CD·관측성)** + 빈 `app_repo`.
**baseline·ops 코드는 만들지 않는다** — 무엇이 공통 기능/운영 요건인지 *명세*까지만, 구현은 ③ Phase 0.

### ② PO-DEV-CHAT — 화면·요구사항 정의

PO가 ①의 디자인 자산을 토대로 **화면·요구사항을 계약(screen model YAML)으로 정의·확정**한다. 코드는 절대 쓰지 않고 **계약만** 산출한다. 목표는 "개발자가 화면 하나만 보고 spec을 만들 수 있을 만큼"의 정보 수집이며, 부족하면 HITL로 다시 묻는다.

**워크플로우 — 4 Stage HITL**:

```
Stage 0  instantiate     DP 선택 → instantiate_screen 으로 SCR- 채번·고정영역 상속·빈 캔버스 시작
Stage 1  layout-recommend   DS 매핑 + screen model 초안 → patch 루프
            └ 저장 시: on-save-schema-validate(Pre) → on-save-lint-L1~L5(Post) → render_screen HTML 렌더
Stage 2  action-interview   interactive 컴포넌트별 순회 인터뷰 → actions[] + Gherkin acceptance
Stage 2.5 entity/external-intake   ENT-/EXT- 데이터·외부 연동 계약
Stage 3  note-intake       PO verbatim 노트 수집 (AI 본문 수정 금지, 태그 제안만)
Stage 4  sufficiency-check  기계 체크 + AI gap 분석 → 누락 시 HITL 재질문
   ▼
Gate A   gate-a-check       lint 0 + 충분성 통과 + 전 action 확정 + 전역 ID 유일성 + PO 승인 → status: confirmed
   ▼
spec-generator              confirmed 화면 → 도메인 단위 PACK-* 팩 발행(+pin 계산) → ③ 인계
journey-map                 navigate 집계 → JRN- 여정 (③ Phase γ E2E 출처)
```

**상태 머신**: `draft → layout_confirmed → actions_in_progress → review → confirmed`

**핵심 자산**: 9개 스킬(layout-recommend·action-interview·note-intake·**entity-intake**·**external-intake**·**journey-map**·sufficiency-check·gate-a-check·spec-generator), 저장 이벤트 훅 2종(schema-validate·lint-L1-L5), 발행 가드 `spec-pack-guard.py`(confirmed·참조 무결·pin 계산), 공유 규칙(screen-model-schema-v2·data-contract-schema·journey-schema 외). Gate A는 6조건(전역 ID 유일성 = `harness-core/lib/spine_ledger.py`).

**산출물**: `model_repo/`(screens SCR-*.yaml 단일 원본 + **entities ENT-*.yaml + externals EXT-*.yaml + journeys JRN-*.yaml** + renders 파생 HTML + specs PACK-* 팩 + link-manifest).

### ③ AI-WEB-DEV — 개발

상류의 **계약을 실행 가능한 코드로 전환**한다. 새로 정의하지 않고, ①의 규칙·기술스택·자산과 ②의 확정 screen model을 받아 test-first로 `app_repo` 하나에 구현·통합한다. SDD는 **speckit**(Spec-Driven Development) 스킬군으로, 결정론은 git 생애주기 훅으로 강제한다.

**워크플로우 — 4 Phase**:

| Phase | 이름 | 하는 일 | 주기 |
|---|---|---|---|
| **0** | SPEC-000·SPEC-OPS-000 Baseline | SPEC-000·SPEC-OPS-000 명세 수신 → 공통 기능·운영(배포/CI·CD/관측성) 전달 모드(A/B) 명세화 → 그에 맞춰 산출 | 1회 |
| **α** | Layout Scaffold | confirmed screen model 전체 → React shell 일괄 생성 (layout만, wiring 없음). `layout-hash-guard`로 ②확정 위치 일치 강제 | 1회 |
| **β** | Spec Pack Iteration | 팩 단위 backend + frontend wiring, T### TDD 루프. ②의 ENT-/EXT- 계약 → data-model·ERD 파생 | 팩마다 |
| **γ** | Integration & NFR | ②의 JRN-* 여정 → Playwright(+BDD) E2E + 성능·동시성·보안·관측성 검증 | 배포 전 |

**Phase 0의 핵심 — 공통 기능 전달 2모드**: 로그인·SSO·RBAC 등 각 공통 기능에 대해 둘 중 하나를 지정한다.

- **모드 A (가이드 코드블럭)**: 동작하는 *예시 코드 + 패턴*을 `baseline-guides/` 스킬로 제공. 프로젝트마다 변형되는 기능(권한 조건부 렌더, 감사 로그 삽입 등) → Phase β가 로드해 적용.
- **모드 B (직접 코드 주입)**: *완성 코드*를 통째로 app_repo에 구현(테스트 green). 변형 불필요한 기능(로그인/SSO 모듈, JWT 필터, RBAC 엔티티) → Phase β는 호출만.
- 판정 한 줄: **"프로젝트마다 변형되나?"** → 예면 A, 아니면 B. 결과는 `baseline-delivery-manifest.yaml`에 기록.

**핵심 자산**: speckit 스킬군(specify·scaffold·plan·tasks·implement + analyze·clarify·constitution·checklist·taskstoissues + git 확장 git-initialize·git-feature·git-commit·git-remote·git-validate), 구현 스킬(design-system-usage·coding-style·complex-bl·baseline-guides), 생애주기 훅(tdd-gate·commit-spine-id·**speckit-artifact-guard**·**layout-hash-guard**·manifest-sync — `git-hooks.manifest.json` 선언 + `install-git-hooks.sh/.ps1`로 `.git/hooks/`에 설치), **부트스트랩/동기화기(install-speckit·speckit-sync)**, **pack→spec 브리지(pack-to-spec.py)**, 서브에이전트(bl-analyst·test-author·code-reviewer), 규칙(gate-b-checklist·tdd-policy·commit-convention·change-order-policy).

> **speckit 메커니즘/상태 경계 (부트스트랩).** speckit의 `.specify/`(scripts·templates·workflows·extensions = 메커니즘)는 **플러그인이 단일 원본**이고, `app_repo`에는 `install-speckit.sh/.ps1`이 **vendoring**한다(speckit 스크립트가 `.specify/`를 위로 찾기 때문). `app_repo/.specify/`의 `memory/constitution.md`·`feature.json`·`templates/overrides/`는 **프로젝트 상태**로 app_repo가 소유한다. 플러그인 업그레이드 시 `speckit-sync.sh/.ps1`가 메커니즘만 재복사하고 상태는 보존한다. speckit **산출물**(`spec.md`·`plan.md`·`tasks.md`)은 model_repo가 아니라 **app_repo/specs/**에 있다(권위=②/model_repo, 구현·파생=③/app_repo).

**산출물**: `app_repo/` — 테스트 green 코드 + 스파인 ID 커밋 히스토리.

---

## 6. 인계 지점 (Handoff Matrix)

레이어 간 계약은 아래 4개 인계로 정의된다. 모두 양쪽 README에서 항목·위치가 일치하도록 교차 검증되어 있다. 복사가 아니라 **같은 `projects/<id>/`를 참조**하며 `foundation/VERSION`으로 핀한다(ADR-001 D3).

| 인계 | 무엇이 넘어가나 | 출발 → 도착 |
|---|---|---|
| **① → ②** | foundation 전체: design-system(token)+catalog + ds-allowlist.md + design-pages(DP-*) + link-manifest.yaml(등록 인덱스) | `projects/<id>/foundation/` (②가 직접 참조) |
| **① → ③** | 플러그인 하네스(speckit·skill·hook·subagent **+ 불변 rules: constitution·spine-ids·ds-closure**) + foundation 전체(design-system·design-pages·**decisions: tech-stack·ops-stack**·link-manifest) + **SPEC-000·SPEC-OPS-000 명세**(구현 아님) + 빈 app_repo 골격 | `projects/<id>/foundation/` + `packages/plugin-ai-web-dev` (③가 참조) |
| **② → ③** | **PACK-\* spec 팩**: screens(yaml_ref·render_ref·pinned_contract) + scope(REQ-/CMP-) + **데이터 계약(ENT-/EXT- ref)** + actions+acceptance 원문 + notes(verbatim·complexity) + **여정(JRN- ref)** + open_items | `projects/<id>/model_repo/specs/` → `app_repo/specs/`(manifest-sync) |
| **③ → ②** | **Change Order** 판정 결과: dismiss / amend / regenerate. 별도 ② 스킬 없이 PO가 기존 Gate A 흐름으로 재확정 → spec-generator가 버전 +1로 재발행 | `③` 변경요청 → `②/model_repo` 재확정·re-pin |

**경계 원칙 요약**: *명세*는 ①, *계약(정의)*은 ②, *구현(코드)*은 ③. 어느 레이어도 하류의 책임을 침범하지 않는다. 특히 SPEC-000은 ①이 명세하고 ③ Phase 0가 구현하며, rules는 `harness-core`가 단일 원본으로 보유해 ①③ 플러그인·② 챗봇이 공유한다.

---

## 7. 자산 배치 규칙 (공통 컨벤션)

세 레이어 모두 동일한 배치 원칙을 따른다:

- **단일 스킬 전용 스크립트·파일** → 그 스킬 폴더 아래 공존 (`skills/<skill>/scripts/`, `skills/<skill>/<rule>.md`). 예: ①의 `design-page-lint.py`, ②의 `sufficiency-check.py`·`gate-a-check.py`·`spec-pack-guard.py`·`question-bank.md`.
- **여러 스킬·레이어 공유 코드·규칙** → `harness-core/`(lib·rules·render) 또는 플러그인 최상위(`hooks/`·`rules/`). 예: 렌더 엔진·ds_closure·spine_ledger·공유 rules.
- **hook 선언** → ①② 저장 이벤트 훅은 플러그인 `settings.json`의 `hooks` 키(PostToolUse/PreToolUse matcher), ③ git 생애주기 훅은 `hooks/git-hooks.manifest.json` 선언 후 `install-git-hooks`가 `.git/hooks/`에 설치.

판별 기준: **"단일 스킬이 직접 호출/소유하는가?"** → 예면 스킬 아래 중첩, 아니면 공유 위치.

---

## 8. 폴더 구조 (최상위)

```
PO-DEV-Harn/                       # 모노레포 (시스템 코드 + 프로젝트 데이터)
├── README.md                      # (이 문서) 통합 진입 문서
├── USER-GUIDE.md                  # PO·개발자 end-to-end 워크플로우 가이드
├── package.json                   # workspace 루트 (packages/* 워크스페이스)
├── marketplace.json               # ①③ Claude Code 플러그인 마켓플레이스
├── CLAUDE.md                      # Claude Code 진입 컨텍스트 (speckit 관리)
├── docs/                          # 아키텍처·이행 문서
│   ├── ADR-001-3runtime-architecture.md
│   ├── ADR-002-deterministic-screen-render.md
│   ├── MIGRATION-PLAN.md
│   ├── CHATBOT-DEV-GUIDE.md       # ② Agent SDK 챗봇 빌드 가이드
│   └── SUPERPOWERS-CHATBOT-BUILD-GUIDE.md
├── guides/                        # speckit×TDD 설계 노트 (참고/이력)
├── packages/                      # ── Tier 1: 시스템 코드 (전 프로젝트 공용) ──
│   ├── harness-core/              # 불변 rules + 공용 lib + 렌더 엔진
│   │   ├── lib/ds_closure.py      #   DS 폐쇄 검증 단일 출처 (①②③ 공유)
│   │   ├── lib/spine_ledger.py    #   스파인 ID 전역 유일성·채번 (Gate A·CLI·인스턴스화)
│   │   ├── render/                #   결정론적 렌더 엔진 (ADR-002)
│   │   │   ├── engine.py          #     공용 코어: 토큰→CSS·컴포넌트→HTML·position resolve·hash
│   │   │   ├── render_screen.py   #     SCR-*.yaml → render.html (②③)
│   │   │   ├── render_designpage.py #   DP-*.yaml → 미리보기 (①)
│   │   │   ├── render_catalog.py  #     tokens+ds-allowlist → DS 카탈로그 (①)
│   │   │   ├── instantiate_screen.py # DP-* → 새 SCR-*.yaml 골격 (②)
│   │   │   ├── pins.py            #     layout_hash/render_hash 계산·검증 (②③ 공유)
│   │   │   ├── tokens.py          #     DS-불가지론 토큰 추출·분류
│   │   │   ├── ds_assets.py       #     ds-compiled.css·ds-fixtures.json 로더 (D8 시각 충실도)
│   │   │   └── build_ds_assets.mjs #    ds-source → 두 자산 1회 컴파일 (①, Node·Vue SSR)
│   │   └── rules/                 #   constitution·spine-ids·ds-closure
│   ├── plugin-prerequisite/       # ① → Claude Code 플러그인 (plugin.json·settings.json)
│   │   ├── skills/ds-bootstrap/        # 오픈소스 DS 이름 → ds-source 설치 + tokens.css + ds-allowlist.md 자동 생성
│   │   ├── skills/design-page-builder/
│   │   ├── hooks/ds-guide-validate.py
│   │   └── docs/
│   ├── plugin-ai-web-dev/         # ③ → Claude Code 플러그인 (speckit + TDD)
│   │   ├── skills/ (speckit-*·design-system-usage·coding-style·complex-bl·baseline-guides)
│   │   ├── agents/ (bl-analyst·test-author·code-reviewer)
│   │   ├── hooks/ (tdd-gate·commit-spine-id·layout-hash-guard·manifest-sync + install-*·sync)
│   │   ├── rules/ · .specify/ (speckit 메커니즘 단일 원본)
│   ├── plugin-po-define/          # ② 능력 플러그인 (skills·hooks·rules) ← 마켓플레이스 등록
│   │   └── settings.json.legacy   #   구 Claude Code 훅 정의 (챗봇 빌드 시 코드로 대체)
│   └── po-def-chat/               # ② 챗봇 앱 (빌드 예정; plugin-po-define 소스를 로드)
└── projects/                      # ── Tier 2+3: 프로젝트 데이터 (참조, 복사 아님) ──
    └── <customer-id>/             # 프로젝트 1개 (멀티테넌트로 증식)
        ├── .claude/settings.json  #   PROJECT_ROOT + 활성 플러그인
        ├── foundation/            #   Tier 2 (① 산출): design-system+catalog·design-pages·
        │                          #     decisions·platform-baseline·link-manifest·VERSION
        ├── model_repo/            #   Tier 3 (② 산출): screens·entities·externals·
        │                          #     journeys·renders·specs·link-manifest
        └── app_repo/              #   Tier 3 (③ 산출): backend·frontend·specs·.specify
```

> `projects/` 의 실제 데이터(예: `projects/devlog`(Vue/shadcn-vue)·`projects/example`(React))는 이 문서 범위 밖이다. 새 프로젝트는 `projects/<customer-id>/`로 증식하며, 세 레이어는 같은 폴더를 참조한다.
