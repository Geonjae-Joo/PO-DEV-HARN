> ⚠️ 이 문서는 구 `02-PO-DEV-CHAT/` 레이어(Claude Code 기준)를 설명합니다. ②는 **Claude Agent SDK 챗봇**으로 빌드 예정 — 개발 방법은 `docs/CHATBOT-DEV-GUIDE.md`, 신구조 매핑은 `docs/MIGRATION-PLAN.md` 참조.

﻿# ② PO-DEV-CHAT — PO 화면·요구사항 정의 레이어

> 화면마다 반복. 주체: PO(도메인 전문가).  
> 화면·요구사항을 **screen model(YAML)**로 정의·확정한다. 앱 코드는 절대 쓰지 않는다 — **계약만 산출**.  
> 목표: **개발자가 screen model 하나만 보고 spec을 만들 수 있을 만큼** 정보 수집.

---

## 이 레이어의 역할

①의 디자인 자산(허용집합·템플릿)을 토대로 PO가 **화면·요구사항을 계약(screen model)으로 정의·확정**하는 단계다. 코드는 절대 쓰지 않는다 — ③가 화면 하나만 보고 spec을 만들 수 있을 만큼의 정보를 모아 **계약만 산출**한다. 부족하면 HITL로 다시 묻는다.

| 무엇을 | 어떻게 |
|---|---|
| 화면 구성·컴포넌트 배치 확립 | **Stage 1** — layout-recommend (DS 매핑 + design page 템플릿 선택 + 초안·patch 루프) |
| 컴포넌트 기능·비즈니스 로직 확립 | **Stage 2~3** — action-interview(순회 인터뷰 → actions[]) + note-intake(verbatim 노트) |
| 데이터·외부 연동 계약 정의 | **Stage 2.5** — entity-intake(ENT-) + external-intake(EXT-). action `outcome.target` 데이터 출처 식별 |
| 화면 간 여정(E2E 시나리오) 정의 | **journey-map** — navigate 집계 → JRN- 여정 + 고립 화면 탐지 |
| 충분성 판정 후 확정 | **Stage 4 → Gate A** — sufficiency-check(기계+AI gap) → gate-a-check(6조건, 전역 ID 유일성 포함) |
| 계약 발행 | spec-generator — confirmed 화면 → 도메인 단위 **PACK-* 팩**(+ENT-/EXT-/JRN- ref) → ③ 인계. 발행 전 `spec-pack-guard.py`가 confirmed·참조 무결 기계 검증 |
| 결정론적 렌더·버저닝·Lint | HTML 파생 렌더(저장 시 자동) / optimistic locking·`version` / L1~L4 lint |

**경계 원칙:** 이 레이어는 **계약만** 만든다. 불변 규칙·DS·템플릿의 *명세*는 ①, 그 계약의 *구현(코드)*은 ③의 책임이다. ②는 새 컴포넌트를 발명하지 않고(①의 DS 폐쇄), 코드를 쓰지 않는다.

**진실원 원칙: screen model(YAML)이 단일 원본. HTML은 파생 뷰이며 직접 편집 금지.**

---

## Workflow — 4 Stage HITL

```
PO: "주문 테이블, 기간 필터, 엑셀 버튼..."
  │
  ▼
Stage 1  layout-recommend
  ① DS 매핑 — ds-allowlist.md 허용 목록에서 컴포넌트 매핑 (DS 밖 발명 금지)
  ② design page 선택 — archetype에 맞는 템플릿 (DP-MAIN, DP-POPUP …)
  ③ screen model YAML 초안 생성 → PO patch 수정 루프 (초안 이후에도 이 스킬 담당)
  ④ 저장 시마다 자동:
     hook(Pre):  on-save-schema-validate.py — schema v2 검증, 실패 시 저장 차단
     hook(Post): on-save-lint-L1-L4.py — L1~L4 lint
     skill:      layout-recommend 렌더링 → renders/SCR-*.render.html (lint 통과 후만)
  └ L1 error 0 → status: layout_confirmed
  │
  ▼
Stage 2  action-interview
  interactive 컴포넌트 하나씩 순회 질문 (question-bank.md 기반)
  → 자연어 → actions[] 구조화 (trigger / outcome.type / permission)
  → Gherkin acceptance 초안 → PO user_confirmed
  → 원문: prompt_log[] append-only / 요약: provenance.intent
  (하이브리드 적재 규칙: prompt-log-policy.md)
  │
  ▼
Stage 2.5  entity-intake / external-intake   (action의 데이터 출처 식별 시)
  outcome.type ∈ {query, mutate, export} → outcome.target 이 ENT-/EXT- 여야 함
  → entity-intake: 개념 엔티티(ENT-) 의미·속성·관계 계약 (물리 타입 없음 — ③ 파생)
  → external-intake: 외부 연동(EXT-) 엔드포인트·인증·장애처리 규약
  (포맷: .claude/rules/data-contract-schema.md / 미정의 참조는 sufficiency-check gap)
  │
  ▼
Stage 3  note-intake
  PO 자유 발화 수집 (verbatim: true — AI 본문 수정 금지)
  AI: kind(business_rule/nfr 등) + complexity(low/med/high) 태그 제안만
  complexity: high → ③ speckit.plan 중 bl-analyst subagent 자동 호출
  │
  ▼
Stage 4  sufficiency-check
  ① sufficiency-check.py — spec-readiness 체크리스트 기계 검사
  ② sufficiency-check skill — AI gap 분석 (의미적 누락 탐지)
  → 누락 → intake.open_questions[] → HITL 재질문
  → 전 질문 answered 또는 deferred(사유 필수) → Gate A 가능
  │
  ▼
Gate A  gate-a-check  [disable-model-invocation: true — PO 명시 요청 시만]
  lint error 0 + sufficiency pass/pass_with_deferred
  + 전 action user_confirmed + PO 승인
  + 전역 스파인 ID 유일성(harness-core/lib/spine_ledger.py — link-manifest 원장)
  → status: confirmed + confirmed_at 기록
  │
  ▼
spec-generator  [disable-model-invocation: true]
  발행 전 가드(필수): scripts/spec-pack-guard.py — confirmed 아님/ENT·EXT dangling ref 차단
  confirmed screen model → 도메인 단위 PACK-* 팩 발행 (+ENT-/EXT-/JRN- ref) → ③ 인계
  절단 기준: Entity 응집 > Workflow 연결성 > Actor 경계
  (포맷: skills/spec-generator/spec-pack-schema.md)

journey-map  (복수 화면 confirmed 후, 횡단)
  전체 SCR의 navigate action 집계 → 화면 간 여정 JRN-*.yaml + 고립 화면 탐지
  → ③ Phase γ Playwright(+BDD) E2E 시나리오 출처
  (포맷: .claude/rules/journey-schema.md)
```

상태 머신: `draft → layout_confirmed → actions_in_progress → review → confirmed`  
상세 전환 조건: [state-machine.md](.claude/rules/state-machine.md)

---

## Harness 자산

### Skills

| 파일 | 단계 | `disable-model-invocation` | 설명 |
|---|---|---|---|
| `skills/layout-recommend/SKILL.md` | Stage 1 | — | DS 매핑 + design page 선택 + screen model 초안. 저장 시마다 HTML 렌더링. **초안·수정 모두 담당.** |
| `skills/action-interview/SKILL.md` | Stage 2 | — | interactive 컴포넌트별 순회 인터뷰. actions[] 구조화 + Gherkin acceptance. |
| `skills/note-intake/SKILL.md` | Stage 3 | — | verbatim 노트 수집. kind·complexity 태그 제안만. |
| `skills/entity-intake/SKILL.md` | Stage 2.5 | — | action이 참조하는 개념 데이터 엔티티(ENT-) 계약 정의. 의미·속성·관계까지만(물리 설계는 ③). |
| `skills/external-intake/SKILL.md` | Stage 2.5 | — | 외부 연동(EXT-) 계약 정의. 엔드포인트 목적·인증·장애처리 규약까지만(어댑터 코드는 ③). |
| `skills/journey-map/SKILL.md` | confirmed 후 | — | navigate 집계 → 화면 간 여정(JRN-) 정의. 고립 화면 탐지. ③ Phase γ E2E 시나리오 출처. |
| `skills/sufficiency-check/SKILL.md` | Stage 4 | — | sufficiency-check.py 실행 후 AI gap 분석. open_questions 생성. action 데이터 출처의 ENT-/EXT- 형식 검증(실존 검증은 spec-pack-guard가 발행 전 강제). |
| `skills/gate-a-check/SKILL.md` | Gate A | **true** | 6가지 조건 종합 판정(전역 ID 유일성 포함). PO 명시 요청 시만 실행. |
| `skills/spec-generator/SKILL.md` | Gate A 후 | **true** | confirmed 화면 → PACK-* 팩 발행. 발행 전 `scripts/spec-pack-guard.py` 필수. |

### Hooks

hooks는 `.claude/settings.json`의 `hooks` 키에 Claude Code hook 이벤트로 정의된다(프로젝트 훅은 settings.json에서 로드됨).  
스크립트 경로: `${CLAUDE_PROJECT_DIR}/.claude/hooks/`

| 스크립트 | 이벤트 | 트리거 | 설명 |
|---|---|---|---|
| `on-save-schema-validate.py` | `PreToolUse(Write\|Edit)` | SCR-*.yaml 저장 전 | schema v2 필수 필드·enum 검증. 실패 시 저장 차단(exit 1). |
| `on-save-lint-L1-L4.py` | `PostToolUse(Write\|Edit)` | SCR-*.yaml 저장 후 | L1 DS준수·L2 완전성·L3 일관성·L4 커버리지. L1 error → 저장 차단. |
| `skills/sufficiency-check/scripts/sufficiency-check.py` | (skill 직접 호출) | Stage 4 진입 | sufficiency-check skill이 Bash로 실행. JSON 결과 → AI gap 분석 입력. |
| `skills/gate-a-check/scripts/gate-a-check.py` | (skill 직접 호출) | Gate A 요청 | gate-a-check skill이 Bash로 실행. 6조건 판정(조건6=전역 ID 유일성, `harness-core/lib/spine_ledger.py`). 통과 시 status: confirmed 전환. |
| `skills/spec-generator/scripts/spec-pack-guard.py` | (skill 직접 호출) | PACK 발행 전 | confirmed 아님·ENT/EXT dangling ref 차단(exit 1). JRN 미커버 화면 경고. |
| `harness-core/lib/spine_ledger.py` | (gate-a/CLI 호출) | Gate A·수동 | link-manifest 원장 기준 전역 ID 중복 탐지 + 카운터 드리프트 경고. `--reconcile`로 카운터 갱신. |

### Rules (Supporting Files — 공유)

공유 rules는 여러 스킬이 참조하므로 `.claude/rules/`에 위치.  
단일 스킬 전용 파일은 해당 스킬 폴더에 공존.

| 파일 | 참조하는 스킬 | 설명 |
|---|---|---|
| `.claude/rules/screen-model-schema-v2.md` | 전체 | YAML 6부 구성 스키마. (0)meta (1)layout (2)actions (3)notes (4)prompt_log (5)intake |
| `.claude/rules/state-machine.md` | gate-a-check, layout-recommend | 상태 전환 조건·optimistic locking·Gate A 규칙 |
| `.claude/rules/spec-readiness-checklist.md` | sufficiency-check | 충분성 기준. error/warn 항목별 Gate A 영향 |
| `.claude/rules/prompt-log-policy.md` | action-interview, note-intake | 하이브리드 적재: prompt_log 원문 + provenance.intent 요약 |
| `.claude/rules/data-contract-schema.md` | entity-intake, external-intake, sufficiency-check, spec-generator | ENT-*.yaml·EXT-*.yaml 스키마. 개념 계약(②)과 물리 설계(③) 경계 명시 |
| `.claude/rules/journey-schema.md` | journey-map, spec-generator | JRN-*.yaml 스키마. navigate 집계 → 여정. ③ Phase γ Playwright 매핑 |
| `skills/action-interview/question-bank.md` | action-interview (전용) | archetype·outcome.type별 인터뷰 질문 목록 |
| `skills/spec-generator/spec-pack-schema.md` | spec-generator (전용) | PACK-* 팩 포맷 + 절단 기준 + speckit 명령 매핑 |

---

## Input / Output

| 구분 | 무엇 | 비고 |
|---|---|---|
| **Input ← ①** | design-system (design token 포함) + ds-allowlist.md + design-pages 템플릿 + link-manifest.yaml(등록 인덱스) | layout 추천의 허용 집합 + lint 기준 |
| **Output → ③** | **PACK-* spec 팩** — screens(yaml_ref·render_ref·pinned_contract) + scope(REQ-/CMP-) + **데이터 계약(ENT-/EXT- ref)** + actions+acceptance 원문 + notes 원문(verbatim·complexity) + **여정(JRN- ref)** + open_items | spec-pack-schema.md 참조 |
| **Input ← ③** | Change Order 판정 결과 (dismiss/amend/regenerate). **별도 change-order 스킬 없이** PO가 기존 Gate A 흐름으로 재확정 → spec-generator가 버전 +1 재발행(re-pin) | model_repo에 반영 |

---

## 폴더 트리

```
02-PO-DEV-CHAT/
├── README.md
├── skills/
│   ├── layout-recommend/
│   │   └── SKILL.md                   # Stage 1: DS 매핑 + 템플릿 + 초안 + HTML 렌더링
│   ├── action-interview/
│   │   ├── SKILL.md                   # Stage 2: 컴포넌트별 인터뷰 → actions[] 구조화
│   │   └── question-bank.md           # Stage 2 전용: archetype별 질문 뱅크
│   ├── note-intake/
│   │   └── SKILL.md                   # Stage 3: verbatim 노트 수집, 태그 제안
│   ├── entity-intake/
│   │   └── SKILL.md                   # Stage 2.5: 개념 데이터 엔티티(ENT-) 계약
│   ├── external-intake/
│   │   └── SKILL.md                   # Stage 2.5: 외부 연동(EXT-) 계약
│   ├── journey-map/
│   │   └── SKILL.md                   # confirmed 후: navigate 집계 → 여정(JRN-)
│   ├── sufficiency-check/
│   │   ├── SKILL.md                   # Stage 4: 기계 체크 후 AI gap 분석
│   │   └── scripts/
│   │       └── sufficiency-check.py   # Stage 4 전용: spec-readiness 기계 검사
│   ├── gate-a-check/
│   │   ├── SKILL.md                   # Gate A: 5조건 종합 판정 (수동 실행 전용)
│   │   └── scripts/
│   │       └── gate-a-check.py        # Gate A 전용: 종합 판정 + status 전환
│   └── spec-generator/
│       ├── SKILL.md                   # 핸드오프: PACK-* 구성·발행 (수동 실행 전용)
│       └── spec-pack-schema.md        # spec-generator 전용: PACK-* 팩 포맷
├── .claude/
│   ├── settings.json                 # Claude Code hook 이벤트 연결 정의 (프로젝트 훅 로드)
│   ├── hooks/
│   │   ├── on-save-schema-validate.py # PreToolUse: schema v2 검증
│   │   └── on-save-lint-L1-L4.py      # PostToolUse: L1~L4 lint
│   ├── rules/                         # 복수 스킬이 공유하는 supporting files
│   │   ├── screen-model-schema-v2.md  # 화면 YAML 스키마 (6부 구성) — 전체 스킬 참조
│   │   ├── data-contract-schema.md    # ENT-*.yaml·EXT-*.yaml 스키마 (개념 계약/물리 설계 경계)
│   │   ├── journey-schema.md          # JRN-*.yaml 스키마 (navigate 집계 → 여정)
│   │   ├── state-machine.md           # 상태 전환·lint·Gate 연동
│   │   ├── spec-readiness-checklist.md # 충분성 기준 (error/warn)
│   │   └── prompt-log-policy.md       # 원문 append-only + intent 요약 규칙
│   └── skills/                        # (기존 skills/ → .claude/skills/)
└── output/
    └── model_repo/
        ├── screens/                   # SCR-*.yaml — screen model 단일 원본
        ├── entities/                  # ENT-*.yaml — 개념 데이터 엔티티 계약
        ├── externals/                 # EXT-*.yaml — 외부 연동 계약
        ├── journeys/                  # JRN-*.yaml — 화면 간 여정 (E2E 시나리오)
        ├── renders/                   # SCR-*.render.html — 파생 뷰 (편집 금지)
        ├── specs/                     # PACK-*/ — 도메인 모듈 단위 spec 팩
        └── link-manifest.yaml         # 스파인 ID 연결 manifest
```

---

## 렌더링 규칙

| 항목 | 내용 |
|---|---|
| 트리거 | screen model YAML 저장 후 L1 lint 통과 시 자동 실행 |
| 스타일 소스 | design token — DS 컴포넌트 토큰 그대로 참조, 재작성 금지 |
| 출력 | `renders/SCR-{ID}.render.html` |
| 직접 편집 | 금지. 다음 렌더링 시 덮어씌워짐. |
| 파일 헤더 | `<!-- GENERATED VIEW — source: SCR-ID.yaml v{ver} — DO NOT EDIT -->` |
| 역할 | PO 확인용 시각 프로토타입 + 개발자 참조용 레이아웃 스펙 |

---

## 개선 현황

### ✅ 완료 — PO-DEV-CHAT에 통합됨

| 항목 | 통합된 위치 |
|---|---|
| error_behavior 구조화 | action-interview Step 3, Q-ERROR 확장, screen-model-schema-v2.md, spec-readiness-checklist.md |
| initial_state 구조화 | action-interview Phase 0 (Q-INIT-STATE), screen-model-schema-v2.md, sufficiency-check gap 5 |
| NFR 구조화 | note-intake NFR follow-up 섹션, screen-model-schema-v2.md `nfr_detail`, sufficiency-check gap 7 |
| reactive 필드 | action-interview Step 3 (Q-REACTIVE), screen-model-schema-v2.md, sufficiency-check gap 6 |
| permission 수집 | action-interview Phase 0 (Q-SCREEN-PERM), sufficiency-check cross-permission 체크 |
| change-order 질문 진입점 | question-bank.md Q-SCREEN-CHANGE-ORDER (status: confirmed 이후) |

### ✅ 해소 — 본류로 편입 (2026-06)

| 항목 | 해소 방식 |
|---|---|
| **Entity / Data Model 정의** (구 🔴) | `entity-intake` 스킬 + `.claude/rules/data-contract-schema.md` + `model_repo/entities/ENT-*.yaml`. ②는 개념 계약, ③ Phase β가 물리 ERD 파생 |
| **External System 계약** (구 🔴) | `external-intake` 스킬 + `model_repo/externals/EXT-*.yaml`. 엔드포인트·인증·장애처리 규약 |
| **Navigation Flow / E2E 시나리오** (구 🟢) | `journey-map` 스킬 + `.claude/rules/journey-schema.md` + `model_repo/journeys/JRN-*.yaml`. navigate 집계 → 여정 + 고립 화면 탐지. ③ Phase γ Playwright 출처 |
| **Change Order 스킬** (구 🟡 — **폐기**) | 별도 스킬 만들지 않음. ③가 pin/freeze/판정 소유, `regenerate` 시 PO가 **기존 Gate A 흐름**으로 재확정 → spec-generator가 버전 +1 재발행. 비대칭 제거 |

### 📋 Backlog — 남은 항목

**Permission Matrix** (🟡 Important)  
권한이 action 단위로 분산 → 역할별 가능 기능 전체 그림 없음.  
→ `permission-matrix` 스킬. 모든 SCR-*.yaml에서 action.permission 집계 → `role × feature` 매트릭스.

**PO 온보