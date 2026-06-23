# ② PO-DEV-CHAT — PO 화면·요구사항 정의 레이어

> 화면마다 반복. 주체: PO(도메인 전문가).
> 화면·요구사항을 **screen model(YAML)**로 정의·확정한다. 앱 코드는 절대 쓰지 않는다 — **계약만 산출**.
> 목표: **개발자가 screen model 하나만 보고 spec을 만들 수 있을 만큼** 정보 수집.

> 🤖 **런타임:** ②는 **Claude Agent SDK 챗봇**으로 빌드 예정이다(ADR-001 D2). 이 패키지(`packages/po-dev-chat/`)는 그 챗봇이 코드로 로드할 **소스**(skill·hook·rule)를 보존한다 — ①③처럼 마켓플레이스 플러그인으로 등록하지 않는다. 빌드 방법은 [`docs/CHATBOT-DEV-GUIDE.md`](../../docs/CHATBOT-DEV-GUIDE.md), 신구조 매핑은 [`docs/MIGRATION-PLAN.md`](../../docs/MIGRATION-PLAN.md). 불변 규칙·렌더 엔진·spine_ledger는 `packages/harness-core/`를 단일 출처로 공유한다.

---

## 이 레이어의 역할

①의 디자인 자산(허용집합·템플릿·DS 카탈로그)을 토대로 PO가 **화면·요구사항을 계약(screen model)으로 정의·확정**하는 단계다. 코드는 절대 쓰지 않는다 — ③가 화면 하나만 보고 spec을 만들 수 있을 만큼의 정보를 모아 **계약만 산출**한다. 부족하면 HITL로 다시 묻는다.

| 무엇을 | 어떻게 |
|---|---|
| design page에서 화면 시작 | **Stage 0** — instantiate (DP 선택 → SCR- 채번 → 고정영역 상속·빈 캔버스, `harness-core/render/instantiate_screen.py`) |
| 화면 구성·컴포넌트 배치 확립 | **Stage 1** — layout-recommend (DS 매핑 + 초안·patch 루프, 캔버스 안에서만) |
| 컴포넌트 기능·비즈니스 로직 확립 | **Stage 2~3** — action-interview(순회 인터뷰 → actions[]) + note-intake(verbatim 노트) |
| 데이터·외부 연동 계약 정의 | **Stage 2.5** — entity-intake(ENT-) + external-intake(EXT-). action `outcome.target` 데이터 출처 식별 |
| 화면 간 여정(E2E 시나리오) 정의 | **journey-map** — navigate 집계 → JRN- 여정 + 고립 화면 탐지 |
| 충분성 판정 후 확정 | **Stage 4 → Gate A** — sufficiency-check(기계+AI gap) → gate-a-check(6조건, 전역 ID 유일성 포함) |
| 계약 발행 | spec-generator — confirmed 화면 → 도메인 단위 **PACK-* 팩**(+ENT-/EXT-/JRN- ref + pin 계산) → ③ 인계. 발행 전 `spec-pack-guard.py`가 confirmed·참조 무결·pin 기계 검증 |
| 결정론적 렌더·버저닝·Lint | HTML 파생 렌더(저장 시 `render_screen.py` 자동) / optimistic locking·`version` / L1~L5 lint |

**경계 원칙:** 이 레이어는 **계약만** 만든다. 불변 규칙·DS·템플릿의 *명세*는 ①, 그 계약의 *구현(코드)*은 ③의 책임이다. ②는 새 컴포넌트를 발명하지 않고(①의 DS 폐쇄), design page 고정영역을 침범하지 않으며(캔버스 봉쇄), 코드를 쓰지 않는다.

**진실원 원칙: screen model(YAML)이 단일 원본. HTML은 파생 뷰이며 직접 편집 금지.**

---

## Workflow — Stage 0 인스턴스화 + 4 Stage HITL

```
Stage 0  instantiate                                       (ADR-002 §6)
  PO가 카탈로그/DP 미리보기에서 design page 선택
  → spine_ledger.mint_scr_id 로 SCR- 채번 (전역 유일)
  → instantiate_screen.py: DP locked region 참조 상속 + editable 캔버스 빈 상태로 새 SCR-*.yaml(draft)
  → from_template: {page: DP-MAIN, version: N} 핀 (불변 — DP 원본 절대 미수정)
  │
  ▼
Stage 1  layout-recommend
  ① DS 매핑 — ds-allowlist.md 허용 목록에서 컴포넌트 매핑 (DS 밖 발명 금지)
  ② screen model YAML 초안 → PO patch 수정 루프 (캔버스 안에서만, 초안 이후에도 이 스킬 담당)
  ③ 저장 시마다 자동:
     hook(Pre):  on-save-schema-validate.py — schema v2(반응형 position·px/auto 금지) 검증, 실패 시 저장 차단
     hook(Post): on-save-lint-L1-L4.py — L1 DS폐쇄·L2 완전성·L3 일관성·L4 커버리지·L5 canvas-bounds
     render:     harness-core/render/render_screen.py → renders/SCR-*.render.html (lint 통과 후만)
  └ L1·L5 error 0 → status: layout_confirmed
  │
  ▼
Stage 2  action-interview
  interactive 컴포넌트 하나씩 순회 질문 (question-bank.md 기반)
  → 자연어 → actions[] 구조화 (trigger / outcome.type / permission)
  → Gherkin acceptance 초안 → PO user_confirmed
  → 원문: prompt_log[] append-only / 요약: provenance.intent  (prompt-log-policy.md)
  │
  ▼
Stage 2.5  entity-intake / external-intake   (action의 데이터 출처 식별 시)
  outcome.type ∈ {query, mutate, export} → outcome.target 이 ENT-/EXT- 여야 함
  → entity-intake: 개념 엔티티(ENT-) 의미·속성·관계 계약 (물리 타입 없음 — ③ 파생)
  → external-intake: 외부 연동(EXT-) 엔드포인트·인증·장애처리 규약
  (포맷: rules/data-contract-schema.md / 미정의 참조는 sufficiency-check gap)
  │
  ▼
Stage 3  note-intake
  PO 자유 발화 수집 (verbatim: true — AI 본문 수정 금지)
  AI: kind(business_rule/nfr 등) + complexity(low/med/high) 태그 제안만
  complexity: high → ③ speckit-plan 중 bl-analyst subagent 자동 호출
  │
  ▼
Stage 4  sufficiency-check
  ① sufficiency-check.py — spec-readiness 체크리스트 기계 검사
  ② sufficiency-check skill — AI gap 분석 (의미적 누락 탐지)
  → 누락 → intake.open_questions[] → HITL 재질문
  → 전 질문 answered 또는 deferred(사유 필수) → Gate A 가능
  │
  ▼
Gate A  gate-a-check  [PO 명시 요청 시만 실행]
  lint error 0 + sufficiency pass/pass_with_deferred
  + 전 action user_confirmed + PO 승인
  + 전역 스파인 ID 유일성(harness-core/lib/spine_ledger.py — link-manifest 원장)
  → status: confirmed + confirmed_at 기록   (6조건)
  │
  ▼
spec-generator  [PO 명시 요청 시만 실행]
  발행 전 가드(필수): scripts/spec-pack-guard.py — confirmed 아님/ENT·EXT dangling ref 차단 + pin 계산·기록
  confirmed screen model → 도메인 단위 PACK-* 팩 발행 (+ENT-/EXT-/JRN- ref) → ③ 인계
  절단 기준: Entity 응집 > Workflow 연결성 > Actor 경계  (spec-pack-schema.md)

journey-map  (복수 화면 confirmed 후, 횡단)
  전체 SCR의 navigate action 집계 → 화면 간 여정 JRN-*.yaml + 고립 화면 탐지
  → ③ Phase γ Playwright(+BDD) E2E 시나리오 출처  (rules/journey-schema.md)
```

상태 머신: `draft → layout_confirmed → actions_in_progress → review → confirmed`
상세 전환 조건: [state-machine.md](rules/state-machine.md)

---

## Harness 자산

### Skills

| 파일 | 단계 | 설명 |
|---|---|---|
| `skills/layout-recommend/SKILL.md` | Stage 0~1 | 인스턴스화 0단계 + DS 매핑 + screen model 초안. 저장 시마다 엔진 위임 HTML 렌더. **초안·수정 모두 담당.** |
| `skills/action-interview/SKILL.md` | Stage 2 | interactive 컴포넌트별 순회 인터뷰. actions[] 구조화 + Gherkin acceptance. |
| `skills/note-intake/SKILL.md` | Stage 3 | verbatim 노트 수집. kind·complexity 태그 제안만. |
| `skills/entity-intake/SKILL.md` | Stage 2.5 | action이 참조하는 개념 데이터 엔티티(ENT-) 계약 정의. 의미·속성·관계까지만(물리 설계는 ③). |
| `skills/external-intake/SKILL.md` | Stage 2.5 | 외부 연동(EXT-) 계약 정의. 엔드포인트 목적·인증·장애처리 규약까지만(어댑터 코드는 ③). |
| `skills/journey-map/SKILL.md` | confirmed 후 | navigate 집계 → 화면 간 여정(JRN-) 정의. 고립 화면 탐지. ③ Phase γ E2E 시나리오 출처. |
| `skills/sufficiency-check/SKILL.md` | Stage 4 | sufficiency-check.py 실행 후 AI gap 분석. open_questions 생성. action 데이터 출처의 ENT-/EXT- 형식 검증(실존 검증은 spec-pack-guard가 발행 전 강제). |
| `skills/gate-a-check/SKILL.md` | Gate A | 6가지 조건 종합 판정(전역 ID 유일성 포함). PO 명시 요청 시만 실행. |
| `skills/spec-generator/SKILL.md` | Gate A 후 | confirmed 화면 → PACK-* 팩 발행. 발행 전 `scripts/spec-pack-guard.py` 필수(+pin 계산). |

### Hooks

> **챗봇 전환 메모:** 현 소스의 hook은 Claude Code 저장 이벤트(PreToolUse/PostToolUse) 형식이다(`settings.json.legacy` 참조). Agent SDK 챗봇 빌드 시 이 로직은 **patch 적용 전 호출 validator**로 래핑된다(ADR-001 D2). 로직은 그대로 재활용된다.

| 스크립트 | 이벤트(현 소스) | 트리거 | 설명 |
|---|---|---|---|
| `hooks/on-save-schema-validate.py` | `PreToolUse(Write\|Edit)` | SCR-*.yaml 저장 전 | schema v2 필수 필드·enum + 반응형 position(px/auto 금지)·from_template 검증. 실패 시 저장 차단. |
| `hooks/on-save-lint-L1-L4.py` | `PostToolUse(Write\|Edit)` | SCR-*.yaml 저장 후 | L1 DS폐쇄·L2 완전성·L3 일관성·L4 커버리지·**L5 canvas-bounds**(가로 봉쇄·locked 슬롯 보호). L1·L5 error → 저장 차단. `harness-core/lib/ds_closure.py` import. |
| `skills/sufficiency-check/scripts/sufficiency-check.py` | (skill 직접 호출) | Stage 4 진입 | spec-readiness 기계 검사. JSON 결과 → AI gap 분석 입력. |
| `skills/gate-a-check/scripts/gate-a-check.py` | (skill 직접 호출) | Gate A 요청 | 6조건 판정(조건6=전역 ID 유일성, `harness-core/lib/spine_ledger.py`). 통과 시 status: confirmed 전환. |
| `skills/spec-generator/scripts/spec-pack-guard.py` | (skill 직접 호출) | PACK 발행 전 | confirmed 아님·ENT/EXT dangling ref 차단. `harness-core/render/pins.py`로 `layout_hash`/`render_hash` 계산·기록·재검증(stale→error). JRN 미커버 화면 경고. |

### Rules (공유)

여러 스킬이 참조하는 규칙은 `rules/`에 둔다. 단일 스킬 전용 파일은 해당 스킬 폴더에 공존. 불변 하드룰(constitution·spine-ids·ds-closure)은 `harness-core/rules/`가 단일 원본.

| 파일 | 참조하는 스킬 | 설명 |
|---|---|---|
| `rules/screen-model-schema-v2.md` | 전체 | YAML 6부 구성 스키마 + 반응형 position·`from_template`. (0)meta (1)layout (2)actions (3)notes (4)prompt_log (5)intake |
| `rules/state-machine.md` | gate-a-check, layout-recommend | 인스턴스화 진입·상태 전환·optimistic locking·Gate A 규칙·L1~L5·엔진 렌더 |
| `rules/spec-readiness-checklist.md` | sufficiency-check | 충분성 기준. error/warn 항목별 Gate A 영향 |
| `rules/prompt-log-policy.md` | action-interview, note-intake | 하이브리드 적재: prompt_log 원문 + provenance.intent 요약 |
| `rules/data-contract-schema.md` | entity-intake, external-intake, sufficiency-check, spec-generator | ENT-*.yaml·EXT-*.yaml 스키마. 개념 계약(②)과 물리 설계(③) 경계 |
| `rules/journey-schema.md` | journey-map, spec-generator | JRN-*.yaml 스키마. navigate 집계 → 여정. ③ Phase γ Playwright 매핑 |
| `skills/action-interview/question-bank.md` | action-interview (전용) | archetype·outcome.type별 인터뷰 질문 목록 |
| `skills/spec-generator/spec-pack-schema.md` | spec-generator (전용) | PACK-* 팩 포맷(layout/render_hash·from_template) + 절단 기준 + speckit 매핑 |

---

## Input / Output

| 구분 | 무엇 | 비고 |
|---|---|---|
| **Input ← ①** | design-system+catalog (design token 포함) + ds-allowlist.md + design-pages 템플릿(DP-*) + link-manifest.yaml(등록 인덱스) | 인스턴스화 출처 + layout 추천 허용 집합 + lint 기준 |
| **Output → ③** | **PACK-* spec 팩** — screens(yaml_ref·render_ref·pinned_contract) + scope(REQ-/CMP-) + **데이터 계약(ENT-/EXT- ref)** + actions+acceptance 원문 + notes 원문(verbatim·complexity) + **여정(JRN- ref)** + open_items | spec-pack-schema.md 참조 |
| **Input ← ③** | Change Order 판정 결과 (dismiss/amend/regenerate). **별도 change-order 스킬 없이** PO가 기존 Gate A 흐름으로 재확정 → spec-generator가 버전 +1 재발행(re-pin) | model_repo에 반영 |

---

## 폴더 트리

```
packages/po-dev-chat/                # ② Agent SDK 챗봇 소스
├── README.md
├── settings.json.legacy             # 구 Claude Code 훅 정의 (챗봇 빌드 시 validator 코드로 대체)
├── skills/
│   ├── layout-recommend/SKILL.md            # Stage 0~1: 인스턴스화 + DS 매핑 + 초안 + 렌더
│   ├── action-interview/
│   │   ├── SKILL.md                          # Stage 2: 컴포넌트별 인터뷰 → actions[]
│   │   └── question-bank.md                  # Stage 2 전용: archetype별 질문 뱅크
│   ├── note-intake/SKILL.md                  # Stage 3: verbatim 노트 수집, 태그 제안
│   ├── entity-intake/SKILL.md                # Stage 2.5: 개념 데이터 엔티티(ENT-) 계약
│   ├── external-intake/SKILL.md              # Stage 2.5: 외부 연동(EXT-) 계약
│   ├── journey-map/SKILL.md                  # confirmed 후: navigate 집계 → 여정(JRN-)
│   ├── sufficiency-check/
│   │   ├── SKILL.md                          # Stage 4: 기계 체크 후 AI gap 분석
│   │   └── scripts/sufficiency-check.py      # Stage 4 전용: spec-readiness 기계 검사
│   ├── gate-a-check/
│   │   ├── SKILL.md                          # Gate A: 6조건 종합 판정 (수동 실행 전용)
│   │   └── scripts/gate-a-check.py           # Gate A 전용: 종합 판정 + status 전환
│   └── spec-generator/
│       ├── SKILL.md                          # 핸드오프: PACK-* 구성·발행 (수동 실행 전용)
│       ├── scripts/spec-pack-guard.py        # 발행 전 가드: confirmed·참조 무결·pin 계산
│       └── spec-pack-schema.md               # spec-generator 전용: PACK-* 팩 포맷
├── hooks/
│   ├── on-save-schema-validate.py            # PreToolUse: schema v2 + 반응형 검증
│   └── on-save-lint-L1-L4.py                 # PostToolUse: L1~L5 lint
└── rules/                                    # 복수 스킬이 공유하는 supporting files
    ├── screen-model-schema-v2.md             # 화면 YAML 스키마 (6부 + 반응형 position)
    ├── data-contract-schema.md               # ENT-*.yaml·EXT-*.yaml 스키마
    ├── journey-schema.md                     # JRN-*.yaml 스키마
    ├── state-machine.md                      # 인스턴스화·상태 전환·lint·Gate 연동
    ├── spec-readiness-checklist.md           # 충분성 기준 (error/warn)
    └── prompt-log-policy.md                  # 원문 append-only + intent 요약 규칙

projects/<id>/model_repo/            # ② 산출물 (Tier 3 데이터)
├── screens/                         # SCR-*.yaml — screen model 단일 원본
├── entities/                        # ENT-*.yaml — 개념 데이터 엔티티 계약
├── externals/                       # EXT-*.yaml — 외부 연동 계약
├── journeys/                        # JRN-*.yaml — 화면 간 여정 (E2E 시나리오)
├── renders/                         # SCR-*.render.html — 파생 뷰 (편집 금지)
├── specs/                           # PACK-*/ — 도메인 모듈 단위 spec 팩
└── link-manifest.yaml               # 스파인 ID 연결 manifest (DP→SCR 엣지 포함)
```

---

## 렌더링 규칙

| 항목 | 내용 |
|---|---|
| 엔진 | `harness-core/render/render_screen.py` (순수 Python, 결정론적 — 같은 입력 → 바이트 동일 HTML) |
| 트리거 | screen model YAML 저장 후 L1·L5 lint 통과 시 자동 실행 |
| 스타일 소스 | design token — DS 컴포넌트 토큰 그대로 참조(인라인 style·외부 CDN/폰트 금지), 재작성 금지 |
| 출력 | `renders/SCR-{ID}.render.html` (브레이크포인트별 반응형 CSS) |
| 직접 편집 | 금지. 다음 렌더링 시 덮어씌워짐. |
| 파일 헤더 | `<!-- GENERATED VIEW — source: SCR-ID.yaml v{ver} — DO NOT EDIT -->` |
| 핀 | `pinned_contract.layout_hash`(전 브레이크포인트 좌표)·`render_hash`(HTML). ③ Phase α가 재현 검증 |
| 역할 | PO 확인용 시각 프로토타입 + 개발자 참조용 레이아웃 스펙 |

---

## 개선 현황

### ✅ 본류로 편입

| 항목 | 해소 방식 |
|---|---|
| **Entity / Data Model 정의** | `entity-intake` 스킬 + `rules/data-contract-schema.md` + `model_repo/entities/ENT-*.yaml`. ②는 개념 계약, ③ Phase β가 물리 ERD 파생 |
| **External System 계약** | `external-intake` 스킬 + `model_repo/externals/EXT-*.yaml`. 엔드포인트·인증·장애처리 규약 |
| **Navigation Flow / E2E 시나리오** | `journey-map` 스킬 + `rules/journey-schema.md` + `model_repo/journeys/JRN-*.yaml`. ③ Phase γ Playwright 출처 |
| **Change Order 스킬** (폐기) | 별도 스킬 없음. ③가 pin/freeze/판정 소유, `regenerate` 시 PO가 기존 Gate A 흐름으로 재확정 → spec-generator가 버전 +1 재발행 |
| **결정론적 렌더·인스턴스화** | `harness-core/render/` 엔진 + Stage 0 인스턴스화 + L5 canvas-bounds + layout_hash 핀 (ADR-002) |

### 📋 Backlog

**Permission Matrix** (🟡 Important) — 권한이 action 단위로 분산되어 역할별 전체 그림이 없음. → `permission-matrix` 스킬: 모든 SCR-*.yaml의 action.permission 집계 → `role × feature` 매트릭스.
