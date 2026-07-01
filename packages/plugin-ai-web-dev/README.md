# ③ AI-WEB-DEV — 개발 레이어 (SDD + TDD 하네스)

> Claude Code 플러그인 (`ai-web-dev`). Spec 팩마다 반복. 주체: 개발자 (VSCode + Claude Code).
> ①의 하네스 자산과 ②의 spec 팩을 받아 **SDD(speckit) + TDD로 단 하나의 웹앱(`app_repo`)을 완성**한다.
> 파일럿은 개발자가 로컬에서 직접 구동 — 사람을 루프 안에 두고 측정한다.

> 패키지 경로: `packages/plugin-ai-web-dev/`. `marketplace.json`에 `ai-web-dev`로 등록(`/plugin marketplace add .` 후 활성화). 작업 대상은 IDE로 연 `projects/<id>/`의 `app_repo/`. 불변 규칙·렌더 엔진·spine_ledger는 `packages/harness-core/`를 단일 출처로 공유한다. SDD는 **speckit 스킬군**으로 제공한다(구 `commands/`에서 `skills/`로 이동).

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

> **선행 — 부트스트랩:** speckit 명령이 동작하려면 `app_repo`에 `.specify/` 메커니즘이 있어야 한다. `hooks/install-speckit.sh/.ps1`이 플러그인 `.specify/`를 vendoring하고 git 훅을 설치한다. 플러그인 업그레이드 시 `speckit-sync.sh/.ps1`이 메커니즘만 재복사한다.

---

## Phase 0 — SPEC-000·SPEC-OPS-000 Baseline

프로젝트 1회. spec 팩 iteration 시작 전에 완료한다.
①이 작성한 **SPEC-000(공통 기능 명세)과 SPEC-OPS-000(운영 명세: 배포·CI/CD·형상관리·관측성)**, 그리고 `ops-stack.md`(도구 결정)를 받아, **각 요건을 어떤 방식으로 전달할지 먼저 명세화**하고 그 결정에 따라 산출한다. Phase 0의 핵심 산출은 "코드"가 아니라 **전달 방식 결정(delivery manifest) + 그에 맞는 자산**이다.

> **운영 요건(SPEC-OPS-000):** CI 파이프라인·Dockerfile/Helm·관측성 SDK(Phoenix/Langfuse) 주입은 대개 표준이라 **모드 B**(완성 코드 주입), 배포 타깃별 차이(k8s vs 온프렘 등)는 **모드 A** 가이드로 보강한다. 도구 선택은 `ops-stack.md`를 따른다.

### 공통 기능 전달 방식 — 2가지 모드

각 공통 기능(로그인, SSO, RBAC, admin, 공통 레이아웃 …)에 대해 **둘 중 하나**를 지정한다.

| 모드 | 무엇 | 언제 | 산출 위치 | 이후 사용 |
|---|---|---|---|---|
| **A. 가이드 코드블럭** | 동작하는 *예시 코드 블럭 + 패턴 설명* (전체 구현이 아님) | 프로젝트마다 변형이 필요한 기능 (권한 조건부 렌더, 감사 로그 삽입 등) | `app_repo/.claude/skills/baseline-guides/` 에 reference 스킬로 적재 | Phase β에서 모델이 스킬로 로드 → 도메인 코드에 맞게 적용 |
| **B. 직접 코드 주입** | *완성된 동작 코드*를 통째로 구현·주입 (테스트 green) | 변형 불필요한 기능 (로그인/SSO 모듈, JWT 필터, RBAC 엔티티/미들웨어) | `app_repo/backend/`·`frontend/` 에 실제 코드 + 테스트 | 그대로 동작. Phase β는 호출만 |

> **판정 기준 한 줄:** "프로젝트마다 변형되나?" → 예면 **A(가이드)**, 아니면 **B(직접 주입)**. 애매하면 B로 골격을 주입하고 변형 지점만 A 가이드로 보강한다.

### 흐름

```
foundation/platform-baseline/ 에서 SPEC-000.md + SPEC-OPS-000.md + foundation/decisions/ops-stack.md 수신
  │
  ▼
speckit-specify  SPEC-000·SPEC-OPS-000 scope 확인 + ★ 요건별 전달 모드(A/B) 결정
                → baseline-delivery-manifest.yaml 작성 (기능·운영요건 → mode:A|B + 사유)
  │
  ├─[mode B 기능]──────────────────────────────────────────┐
  │  speckit-plan → speckit-tasks(test-first) →             │
  │  Gate B → speckit-implement → commit → code-reviewer     │  → app_repo 실제 코드(green)
  │                                                          │
  └─[mode A 기능]──────────────────────────────────────────┘
     예시 코드블럭 + 패턴 가이드 작성
     → app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md   → Phase β가 로드해 적용
```

**산출물**: `baseline-delivery-manifest.yaml`(전달 모드 단일 진실원) · (B) 라우팅·인증/SSO/RBAC 실제 구현+테스트·공통 레이아웃·DB 연결·CI 설정 · (A) `baseline-guides/` reference 스킬.

> **①과의 경계:** *무엇이 공통 기능인지(scope·요구사항)*는 ①의 SPEC-000이 정한다. *그것을 A로 줄지 B로 줄지, 그리고 실제 코드/가이드*는 ③ Phase 0가 만든다. ①은 baseline을 구현하지 않는다 — 명세까지만.

---

## Phase α — Layout Scaffold

**모든 확정 screen model → 프론트엔드 페이지 컴포넌트 shell 일괄 생성.**
대상 프레임워크·확장자·디렉터리 구조는 **①의 tech-stack.md `frontend.framework`에서 파생**한다(고정값 아님 — React→`.tsx`/`src/pages`, Vue→`.vue`/`src/views` 등). screen model 자체는 프레임워크 중립이라 scaffold는 그 모델을 선택된 프레임워크로 투영할 뿐이다. 각 화면을 layout만 있는 상태(데이터·이벤트 없음)로 만든다. 이후 Phase β가 shell에 wiring만 추가한다.

```
② model_repo/screens/*.yaml (전체 confirmed) + renders/*.render.html(참조용) 수신
  │
  ▼
speckit-scaffold  전체 화면 shell 일괄 생성
  - screen model position 그대로 DS 컴포넌트 배치 · props stub · 라우팅 연결 · 이벤트/API 없음
  │
  ▼
hook: layout-hash-guard.py (진입 가드 — 각 화면 재렌더 layout_hash 가 ②확정 pinned_contract와 일치해야 진행. 불일치 시 빌드 차단)
hook: tdd-gate.py ([SCAFFOLD] skip)  ·  commit-spine-id.py → [SCAFFOLD] 커밋
```

**산출물**: `app_repo/frontend/` 아래 모든 화면의 페이지 shell (경로·확장자는 ①의 프레임워크 규약).

**왜 선행하는가**: 한 화면이 여러 팩에 걸칠 때 layout 중복·충돌 방지 · 팩별 implement가 wiring에만 집중 · 앱을 띄우면 모든 화면이 layout 상태로 즉시 확인(walking skeleton).

---

## Phase β — Spec Pack Iteration

spec 팩 단위로 반복한다. **팩 = 하나의 도메인 모듈** (단일 feature가 아님).

```
PACK-X 수신 (model_repo/specs/PACK-X/)
  │
  ▼
speckit-specify   팩 scope 확인(묶인 화면·REQ/CMP) · 필요 시 sub-pack 재분할 · open_items deferred 처리
                  (pack-to-spec.py PACK-<ID> 로 spec-pack+screen model → spec.md 초안 생성 후 검토)
  │
  ▼
speckit-plan      Data Model + ERD — ②의 ENT-/EXT- 계약에서 *파생*(물리 타입·인덱스·FK). 새 엔티티 발명 금지(필요 시 Change Order)
                  API 설계(EXT- 계약은 어댑터로) · complexity:high 노트 → bl-analyst subagent · frontend wiring 계획(shell_ref 기준)
  │
  ▼
speckit-tasks     T### 태스크 목록 · test-first 정렬(테스트 태스크 선행) · [P] 병렬 마커 · backend→frontend 순서
  │
  ▼
Gate B  (개발자 소유 — rules/gate-b-checklist.md)
  Data Model·ERD·BL·Task 전체 확정 · bl-analyst 미해결 0 · PO는 비차단 소프트 리뷰만 · approve 전 구현 금지
  │
  ▼
speckit-implement  (T### 순서대로)
  ① subagent: test-author — acceptance(Gherkin)+worked examples → 실패 테스트 먼저 (API·화면 2계층)
  ② 구현: red → green → refactor
  ③ hook: tdd-gate.py — 테스트 없음/실패 시 commit 차단
  ④ hook: commit-spine-id.py → [PACK-ORDER/T001] 자동 커밋
  │
  ▼
subagent: code-reviewer   DS 준수·보안·코딩 스타일·TDD 충족·스파인 ID 검증
  │
  ▼
integration 브랜치 머지 → PR
```

**Frontend wiring 원칙**: Phase α shell에 API hook·상태 관리·권한 조건부 렌더·에러 처리 추가. layout 구조(위치·배치)는 건드리지 않는다. 신규 컴포넌트(modal·drawer 등)는 이 팩에서 shell+wiring 동시 생성.

---

## Phase γ — Integration & NFR

```
② model_repo/journeys/JRN-*.yaml 수신
  │
  ▼
E2E 구현 — JRN-* 1개 → Playwright(+BDD) E2E 스펙 1개
  - 각 step → 거치는 화면 action의 acceptance(Gherkin) 재사용 (새 시나리오 발명 금지)
  - 커밋: [E2E/JRN-…] (commit-convention.md) · 추적: JRN- → SCR/action → e2e-test → commit
  │
  ▼
code-reviewer 전체 검토 · NFR(성능·동시성·보안·감사) · 관측성 검증(OPS-OBS — Phoenix/Langfuse) · 배포 준비(OPS-CD — ops-stack.md)
```

**E2E 원칙**: 시나리오 출처는 ②의 `JRN-*` 계약. ③는 여정을 새로 정의하지 않고 Playwright로 *구현*만 한다. 도구·CI 연동은 `ops-stack.md`/SPEC-OPS-000을 따른다.

---

## 변경 처리 — Change Order (자동 재생성 안 함)

```
1. Pin      spec은 생성 시점 계약 버전에 고정.
2. Freeze   구현 중 화면은 소프트 프리즈. PO 편집은 change-order 큐에 누적.
3. Change Order  PO 재확정 시 스파인 ID 단위 diff + blast radius 계산 → 변경 지시서.
4. 개발자 판정  dismiss(외관 → re-pin) · amend(경미 → 제자리 수정 후 re-pin) · regenerate(중대 → 해당 팩만 재생성 + 새 Gate B)
5. TDD 백스톱  acceptance 변경 시 기존 테스트가 깨짐(breaking). REQ 추가만이면 새 task(additive).
```

---

## Harness 자산

### Skills — speckit (SDD) + 구현 가이드

speckit은 **스킬**으로 제공된다(모델이 필요 시 로드, 슬래시 호출 `/speckit-*`). 코어 5종 + 보조 5종 + git 확장 5종.

| 스킬 | 단계 | 설명 |
|---|---|---|
| `speckit-specify` | 모든 Phase | 자연어/팩 → `spec.md` 생성·갱신. **선행: `install-speckit` 부트스트랩.** `pack-to-spec.py`로 spec-pack+screen model → 초안 생성 후 검토(산문 직접작성 금지). |
| `speckit-scaffold` | **Phase α 전용** | 전체 확정 screen model → 프론트엔드 shell 일괄 생성 (①의 framework에서 확장자·구조 파생). |
| `speckit-plan` | Phase 0·β | Data Model·ERD·API 설계. **②의 ENT-/EXT- 계약에서 물리 설계 파생**(발명 금지). complexity:high → bl-analyst. |
| `speckit-tasks` | Phase 0·β | `tasks.md` 생성. test-first 정렬. [P] 병렬 마커. |
| `speckit-implement` | Phase 0·β | T### 단위 TDD 구현 루프. test-author → red → green → refactor → commit. |
| `speckit-analyze` | 검토 | tasks 생성 후 spec·plan·tasks 교차 일관성/품질 비파괴 분석. |
| `speckit-clarify` | 보강 | spec의 미충족 영역을 최대 5개 표적 질문으로 식별·반영. |
| `speckit-constitution` | 1회/변경 | 프로젝트 constitution 생성·갱신 + 의존 템플릿 동기화. 권위는 `harness-core/rules/constitution.md`(파생 동기화). |
| `speckit-checklist` | 검토 | feature 요구사항 기반 맞춤 체크리스트 생성. |
| `speckit-taskstoissues` | 선택 | tasks를 의존 순서 GitHub 이슈로 변환. |
| `speckit-git-initialize` / `-feature` / `-commit` / `-remote` / `-validate` | git 확장 | `.specify/extensions/git/`의 git 워크플로우(저장소 초기화·feature 브랜치·자동 커밋·원격·검증)를 감싼 확장 스킬. |

| 구현 스킬 | 설명 |
|---|---|
| `design-system-usage/SKILL.md` | DS 컴포넌트를 ①의 프레임워크(예: React)로 구현. design token 참조·shell 생성 패턴. |
| `coding-style/SKILL.md` | ①의 tech-stack.md 스택의 코딩 컨벤션(패키지 구조·네이밍·예외 처리). 예시: Spring Boot + React. |
| `complex-bl/SKILL.md` | decision table·state machine 코드화. bl-analyst 산출물 해석·적용. |
| `baseline-guides/SKILL.md` | **[Phase 0 모드 A 템플릿]** 공통 기능 가이드의 *산출 형식* 정의. Phase 0가 mode:A 기능마다 `app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md`를 생성, Phase β가 로드해 변형 적용. |

### Hooks — git 생애주기 자동 실행 (AI 없는 결정론)

git 훅은 `hooks/git-hooks.manifest.json` 선언 + `install-git-hooks.sh/.ps1`이 `app_repo/.git/hooks/`에 설치한다.

| 파일 | 트리거 | 설명 |
|---|---|---|
| `tdd-gate.py` | commit-msg | 테스트 없음/실패 시 commit 차단. 러너 미탐지+`HARNESS_TEST_CMD` 미설정 시도 **차단**(우회: `HARNESS_TDD_ALLOW_NO_RUNNER=1`). 테스트 파일은 네이밍 컨벤션으로 판별(spec-pack `specs/` 오인 안 함). `[SCAFFOLD]` skip. |
| `commit-spine-id.py` | commit-msg | 스파인 ID 포함 검증. `[<PACK\|SPEC\|MOD>/<task>] 요약 (REQ-...)`. PACK/MOD은 REQ- 필수, SPEC-은 REQ- 또는 `(baseline)`/`(ops baseline)` 사유 필수. `[SCAFFOLD]`·`[CO/...]`·`[E2E/JRN-...]`·`[spec-kit/...]` 예외. |
| `speckit-artifact-guard.py` | commit-msg | `[spec-kit/specify\|plan\|tasks]` 커밋이 마커만 있고 산출물(spec/plan/tasks.md)이 없으면 차단. `.specify/feature.json`으로 feature_dir 해석, 불가 시 graceful PASS. |
| `layout-hash-guard.py` | Phase α 진입 | 각 pack `screens[].yaml_ref`를 ②와 동일 엔진(`harness-core/render/pins`)으로 재렌더해 `pinned_contract.layout_hash`와 비교(불일치→빌드 차단). `render_hash`는 warn. `layout_hash`는 좌표·구조 전용이라 **시각 충실도 자산(D8)과 무관**(불변) — DS 자산이 바뀌어도 이 가드는 통과한다. (ADR-002 D5·D8) |
| `manifest-sync.py` | post-commit | `model_repo/specs/PACK-*` → `app_repo/specs/` 동기화 + shell_ref 갱신. 비차단. |
| `git-hooks.manifest.json` | — | 위 git 훅의 생애주기 선언(pre-commit 차단 체인 + post-commit 동기화). 설치기가 파싱하지 않는 문서용 매니페스트(플러그인 훅 규약 `hooks/hooks.json`과 구분). |
| `install-git-hooks.sh` / `.ps1` | — | 매니페스트가 선언한 git 훅 설치(bash / PowerShell). `PYTHON`·`HARNESS_TEST_CMD` 지원. |
| `install-speckit.sh` / `.ps1` | — | **app_repo 부트스트랩**: 플러그인 `.specify/` 메커니즘 vendoring + `.source` 버전 핀 + git hook 설치 호출. |
| `speckit-sync.sh` / `.ps1` | — | 플러그인 업그레이드 시 **메커니즘만** 재복사. 상태(memory·feature.json·overrides·git-config)는 **보존**. |

### .specify — speckit 메커니즘/상태 경계

speckit 스크립트는 cwd에서 위로 `.specify/`를 찾아 루트를 정한다. 따라서 `.specify/`는 **app_repo에 물리적으로** 있어야 하지만 소유권이 둘로 갈린다.

| 구역 | 내용 | 소유 | 업그레이드 |
|---|---|---|---|
| **메커니즘** | `scripts/`·`templates/`(core)·`workflows/`·`extensions/*/scripts·commands` | **플러그인 단일 원본** | `speckit-sync`가 재복사 |
| **상태** | `memory/constitution.md`·`feature.json`·`templates/overrides/`·`extensions/git/git-config.yml` | **app_repo** | sync가 **보존** |

- **부트스트랩**: `install-speckit`이 메커니즘 vendoring + `.specify/.source`에 `plugin@version`·speckit 버전 기록(상태 미덮음, 멱등).
- **커스터마이즈**: core 템플릿 직접 수정 금지 — `templates/overrides/`에 얹는다(`common.sh: resolve_template`가 overrides→presets→extensions→core 순 해석).
- **constitution 단일 원본**: 권위는 ①(`harness-core/rules/constitution.md`). `.specify/memory/constitution.md`는 `speckit-constitution`이 동기화하는 파생 상태.
- **산출물 위치**: `spec.md`·`plan.md`·`tasks.md`는 `app_repo/specs/<NNN>-<slug>/`(구현, 재생성 가능). PO 계약(`SCR-`·`ENT-`·`JRN-`·`spec-pack.yaml`)은 `model_repo/`(권위). `manifest-sync`가 `model_repo/specs/PACK-*` → `app_repo/specs/`로 동기화.
- **`.specify/scripts/bash/pack-to-spec.py`**: `spec-pack.yaml`+screen/entity/journey → `spec.md` 초안 생성(G2 브리지). 권위 본문은 screen model에서 끌어오고 Gherkin 부재 시 '파생 초안'으로 표시.

### Subagents — 격리 컨텍스트 전문 에이전트

| 파일 | 설명 |
|---|---|
| `agents/bl-analyst.md` | complexity:high 노트 → decision table·state machine·worked examples. speckit-plan 중 호출. |
| `agents/test-author.md` | acceptance(Gherkin)+worked examples → 실패 테스트 먼저. API·화면 2계층. speckit-implement 시작 시. |
| `agents/code-reviewer.md` | DS 준수·보안·코딩 스타일·TDD 충족·스파인 ID·Change Order blast radius 검증. |

> **팩 (재)생성은 ③에 없다.** confirmed 화면 → PACK-* 분해는 ②의 `spec-generator` 책임이다. Change Order가 `regenerate`로 판정되면 PO 재확정 → ②가 해당 팩만 재발행 → ③가 소비한다. ③는 *판정 + blast radius*까지만 (③는 새 계약을 만들지 않는다).

### Rules — 변경 없는 규칙 (hook·CI가 강제)

| 파일 | 설명 |
|---|---|
| `rules/gate-b-checklist.md` | Gate B 통과 조건. Data Model·ERD·BL·Task 확정 + bl_sections 미해결 0 + 개발자 approve. |
| `rules/tdd-policy.md` | red→green→refactor 3겹 강제. 테스트 없는 구현 금지. |
| `rules/commit-convention.md` | `[<PACK\|SPEC\|MOD>/<task>] 요약 (REQ-...)`. scaffold `[SCAFFOLD]`, Change Order `[CO/<dismiss\|amend\|regenerate>]`, E2E `[E2E/JRN-...]`. |
| `rules/change-order-policy.md` | Pin·Freeze·Change Order·dismiss/amend/regenerate 판정 규칙. |

---

## 폴더 트리

```
packages/plugin-ai-web-dev/          # ③ Claude Code 플러그인
├── README.md
├── plugin.json                      # 매니페스트 (components·speckit: .specify/·shared: ../harness-core)
├── skills/
│   ├── speckit-specify/ · speckit-scaffold/ · speckit-plan/ · speckit-tasks/ · speckit-implement/
│   ├── speckit-analyze/ · speckit-clarify/ · speckit-constitution/ · speckit-checklist/ · speckit-taskstoissues/
│   ├── speckit-git-initialize/ · speckit-git-feature/ · speckit-git-commit/ · speckit-git-remote/ · speckit-git-validate/
│   ├── design-system-usage/SKILL.md
│   ├── coding-style/SKILL.md
│   ├── complex-bl/SKILL.md
│   └── baseline-guides/SKILL.md     # [Phase 0 모드 A] feature별 가이드 스킬 생성 템플릿
├── agents/
│   ├── bl-analyst.md · test-author.md · code-reviewer.md
├── hooks/
│   ├── tdd-gate.py · commit-spine-id.py · speckit-artifact-guard.py · layout-hash-guard.py · manifest-sync.py
│   ├── git-hooks.manifest.json      # git 훅 생애주기 선언 (문서용)
│   ├── install-git-hooks.sh / .ps1  # git 훅 설치기
│   ├── install-speckit.sh / .ps1    # app_repo 부트스트랩 (.specify vendoring)
│   └── speckit-sync.sh / .ps1       # 메커니즘 재복사 (상태 보존)
├── rules/
│   ├── gate-b-checklist.md · tdd-policy.md · commit-convention.md · change-order-policy.md
└── .specify/                        # speckit 메커니즘 단일 원본 (app_repo로 vendoring)
    ├── scripts/bash/ (common.sh·check-prerequisites.sh·create-new-feature.sh·setup-plan.sh·setup-tasks.sh·pack-to-spec.py)
    ├── templates/ (spec·plan·tasks·checklist·constitution)
    ├── workflows/ · integrations/ · memory/constitution.md(템플릿)
    └── extensions/git/ (commands·scripts bash+powershell·config)

projects/<id>/app_repo/              # ③ 산출물 (Tier 3) — ★ 단 하나의 웹앱
├── .claude/skills/baseline-guides/  # [Phase 0 모드 A] 공통 기능 예시 코드블럭·패턴 가이드
├── .specify/                        # vendoring된 speckit 메커니즘 + 프로젝트 상태(memory·feature.json·overrides)
├── baseline-delivery-manifest.yaml  # [Phase 0] 공통 기능별 전달 모드(A/B)+사유
├── backend/                         # ①의 tech-stack.md 스택 — 테스트 green ([모드 B] baseline 포함)
├── frontend/src/pages/              # Phase α shell → Phase β wiring 완료
├── e2e/                             # [Phase γ] Playwright(+BDD) — JRN-* 여정
└── specs/<NNN>-<slug>/              # 동기화된 spec 팩 + spec.md·plan.md·tasks.md
```

---

## Input / Output

| 구분 | 무엇 | 출처/목적지 |
|---|---|---|
| **Input ← ①** | 플러그인 하네스(speckit skills·구현 skills·hooks·agents·rules **+ harness-core 불변 rules: constitution·spine-ids·ds-closure**) + foundation(design-system·design-pages·**decisions: tech-stack·ops-stack**·link-manifest) + **SPEC-000·SPEC-OPS-000 명세**(구현 아님) + 빈 app_repo 골격 | `projects/<id>/foundation/` + 플러그인 (③가 참조) |
| **Input ← ②** | **PACK-* spec 팩** — screens(yaml_ref·render_ref·pinned_contract) + scope(REQ-/CMP-) + 데이터 계약(ENT-/EXT- ref) + actions+acceptance 원문 + notes(verbatim·complexity) + 여정(JRN- ref) + open_items | `model_repo/specs/` → `app_repo/specs/`(manifest-sync) |
| **Output** | `app_repo/` — 테스트 green 코드 + 스파인 ID 커밋 히스토리 (배포 시 독립 repo로 추출) | `projects/<id>/app_repo/` |
| **Output → ②** | **Change Order** 판정(dismiss/amend/regenerate) + blast radius. 별도 스킬 없이 PO가 기존 Gate A 흐름으로 재확정 | `model_repo` 재확정·re-pin |

---

## 경계 원칙 요약

이 레이어는 **구현(how)만** 한다. *명세*는 ①, *계약(정의)*은 ②. ③는 새 계약·규칙을 만들지 않고, ②의 확정 위치(layout_hash)를 바꾸지 않으며(가드 강제), 필요한 데이터가 계약에 없으면 Change Order로 ②에 요청한다.

상세 흐름은 루트 [`USER-GUIDE.md`](../../USER-GUIDE.md), 아키텍처는 [`docs/ADR-001`](../../docs/ADR-001-3runtime-architecture.md)·[`docs/ADR-002`](../../docs/ADR-002-deterministic-screen-render.md), speckit 통합 노트는 [`guides/SPECKIT-HARNESS-INTEGRATION.md`](../../guides/SPECKIT-HARNESS-INTEGRATION.md) 참조.
