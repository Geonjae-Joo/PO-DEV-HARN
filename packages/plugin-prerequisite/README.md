> ⚠️ 이 문서는 구 `01-PREREQUISITE/` 레이어 기준 경로(`.claude/rules/`, `foundation/` 등)를 일부 포함합니다. 신구조(packages/plugin-prerequisite + projects/<id>/foundation) 매핑은 `docs/MIGRATION-PLAN.md` 참조.

﻿# ① PREREQUISITE — 준비 레이어

> 고객사/프로젝트당 **1회** 수행. 주체: 개발 리드/운영자.
> PO 작업(②)과 개발(③)이 시작되기 전에 **디자인 자산·규칙·앱 골격을 준비**한다.
> 산출물은 ②와 ③ 양쪽에 흘러들어가고, **빈 `app_repo` 골격**을 스캐폴드한다 (baseline 실제 구현은 ③ Phase 0의 몫).

---

## Workflow

```
1. 사용자가 기존 design component를 foundation/design-system/ds-source/ 에 직접 저장
   (새로 만들지 않음 — 기존 DS 그대로 투입, design token 포함)
     └ hook: ds-guide-validate.py 자동 실행 (목록·필수 필드 검증)

2. ds-allowlist.md 작성 — DS 컴포넌트 목록(이름·props·용도) + 사용 가이드
   (②의 layout-recommend skill과 lint가 이 목록을 허용 집합 원본으로 참조)

3. skill: design-page-builder 실행
   DS를 조합해 빈 페이지 템플릿 생성 (DP-MAIN, DP-POPUP 등)
     └ 스킬이 생성 직후 scripts/design-page-lint.py 직접 호출 (DS 폐쇄 검증 — DS 밖 컴포넌트 사용 시 error)

4. rules(불변 규칙) 확정 + 프로젝트 결정 핀
   rules: constitution.md / spine-ids.md / ds-closure.md   (.claude/rules/ — 불변)
   decisions: tech-stack.md / ops-stack.md                  (foundation/decisions/ — 프로젝트별 결정)
   + platform-baseline 명세: SPEC-000.md(공통 기능) / SPEC-OPS-000.md(배포·CI/CD·관측성)

5. 빈 app_repo 스캐폴드
   기술스택 골격 + .claude/ 하네스 자산(commands/skills/hooks/subagents + rules) + design-system 투입 + SPEC-000·SPEC-OPS-000 명세 배치
   (★ baseline·ops 코드를 여기서 구현하지 않는다 — ③ Phase 0가 전달 모드 A/B를 정해 구현/가이드 산출)
```

**DoD**: ds-allowlist.md 존재(lint 참조 가능) / design page 최소 1세트(DP-MAIN + DP-POPUP) / constitution에 하드 룰 명시 / SPEC-000·SPEC-OPS-000 **명세**가 스파인 편입 / tech-stack·ops-stack 결정 확정(foundation/decisions/) / 불변 rules(constitution·spine-ids·ds-closure)가 .claude 골격에 번들 / 스파인 ID 규칙 고정.

---

## Harness 자산

> **배치 원칙 (②와 동일):** 단일 스킬이 직접 호출하거나 그 스킬 전용인 스크립트·파일은 **해당 스킬 폴더 아래에 공존**시킨다. 저장 이벤트로 자동 실행되는 훅(스크립트는 `.claude/hooks/`, 선언은 `.claude/settings.json`)과 여러 스킬·레이어가 공유하는 규칙(`.claude/rules/`)은 최상위에 둔다.

### Skills — 모델이 필요 시 로드하는 상세 가이드

| 파일 | 설명 |
|---|---|
| `skills/design-page-builder/SKILL.md` | DS 컴포넌트를 조합해 빈 페이지 템플릿(DP-MAIN, DP-POPUP 등)을 생성하는 방법. 허용 집합(ds-allowlist.md) 참조, DS 밖 컴포넌트 발명 금지. 각 템플릿에 스파인 ID(DP-*) 부여. |
| `skills/design-page-builder/scripts/design-page-lint.py` | **design-page-builder 전용.** 스킬이 템플릿 생성 직후 Bash로 직접 호출하는 출력 검증기. 템플릿이 DS 허용 집합 안의 컴포넌트만 쓰는지 + 스파인 ID(DP-*) 존재 검증. (②의 `sufficiency-check.py`·`gate-a-check.py`가 스킬 폴더에 중첩된 것과 동일 패턴.) |

### Hooks — 저장 이벤트 자동 실행 (AI 없는 결정론)

hooks는 플러그인 `settings.json`의 `hooks` 키에 Claude Code hook 이벤트(PostToolUse matcher + command)로 정의된다. 스크립트 경로: `${CLAUDE_PLUGIN_ROOT}/hooks/`. payload는 stdin JSON, 차단은 exit 2.

| 스크립트 | 이벤트 | 트리거 | 설명 |
|---|---|---|---|
| `hooks/ds-guide-validate.py` | `PostToolUse(Write\|Edit)` | ds-allowlist.md 저장 직후 | 컴포넌트 목록 형식, 필수 필드(이름·props·용도) 존재 여부 검증. 훅 payload(JSON)를 **stdin**으로 받아 파일 경로를 자기필터(ds-allowlist.md만 검증, 그 외 조용히 통과), 실패 시 **exit 2**로 모델에 피드백. 현행 Claude Code 훅 스키마(matcher + command). settings.json 선언은 `${CLAUDE_PLUGIN_ROOT}/hooks/`. |

### Rules — 변경 없는 불변 규칙 (전 레이어 공유)

세 규칙 모두 **여러 레이어·스킬이 공유**하는 불변 규칙이므로 `.claude/rules/`에 둔다 (단일 스킬 전용 규칙이 없음). **스택 결정(tech-stack·ops-stack)은 규칙이 아니라 프로젝트별 *결정*이므로 rules/가 아닌 `foundation/decisions/`에 둔다** (ds-allowlist.md가 foundation에 있는 것과 동일한 원칙 — project-scope 산출물).

| 파일 | 설명 |
|---|---|
| `.claude/rules/constitution.md` | **전 레이어 공통 하드 룰.** screen model 단일 원본 / HTML 파생 뷰 저장 허용·직접 편집 금지 / DS 폐쇄 / 스파인 ID / optimistic locking / TDD / 커밋 규칙. |
| `.claude/rules/spine-ids.md` | SCR-/CMP-/REQ-/ENT-/EXT-/NOTE-/NFR-/JRN-/SPEC-/T###/DP- 채번 규칙. 전 레이어 공통 적용. |
| `.claude/rules/ds-closure.md` | DS 집합 밖 컴포넌트를 screen model·design page에 추가하는 것을 금지하는 규칙 상세. ①의 design-page-lint + ②의 lint L1이 함께 강제 기준으로 참조. |

### Decisions — 프로젝트별 스택 결정 (foundation 산출물)

규칙이 아니라 **프로젝트마다 확정하는 결정**이므로 `foundation/decisions/`에 둔다. foundation의 일부로 ②·③에 핸드오프된다.

| 파일 | 설명 |
|---|---|
| `foundation/decisions/tech-stack.md` | **앱 스택의 단일 출처.** 백엔드·프론트엔드 스택을 ①에서 프로젝트별로 확정한다(고정값 아님). 현재 선택 예시: 백엔드 Spring Boot / 프론트엔드 React+Vite+TS+Tailwind+shadcn/ui. ②·③·스킬·훅이 이 파일을 따른다. 변경 시 DECISIONS.md 갱신. |
| `foundation/decisions/ops-stack.md` | **운영 스택의 단일 출처.** 형상관리(GitHub\|GitLab)·CI/CD·배포 타깃(k8s\|Docker\|온프렘)·관측성(Phoenix\|Langfuse) 결정을 프로젝트별로 확정(고정값 아님). SPEC-OPS-000 명세의 *도구 선택*에 해당. ③ Phase 0·γ가 따른다. |

---

## 폴더 트리

```
01-PREREQUISITE/
├── README.md
├── input/
│   └── design-system/              # [INPUT] 사용자가 직접 저장하는 기존 DS 원본
│                                   # design token 포함
├── .claude/
│   ├── settings.json              # Claude Code hook 이벤트 연결 정의 (프로젝트 훅 로드)
│   ├── skills/
│   │   └── design-page-builder/
│   │       ├── SKILL.md            # DS 조합 → 빈 페이지 템플릿 생성
│   │       └── scripts/
│   │           └── design-page-lint.py  # [스킬 전용] 템플릿 DS 폐쇄·스파인 ID 검증
│   ├── hooks/
│   │   └── ds-guide-validate.py    # [저장 이벤트 훅] ds-allowlist.md 형식·목록 검증
│   └── rules/                      # 불변 규칙만 (스택 결정은 foundation/decisions/)
│       ├── constitution.md         # 전 레이어 하드 룰 (단일 진실원 원칙 포함)
│       ├── spine-ids.md            # 스파인 ID 채번 규칙
│       └── ds-closure.md           # DS 폐쇄 규칙 상세
└── output/                         # [OUTPUT] ②·③로 흘러가는 산출물
    ├── foundation/
    │   ├── design-system/
    │   │   └── ds-allowlist.md     # DS 컴포넌트 목록 + 사용 가이드
    │   │                           # (②의 허용 집합 원본, ③의 구현 참조)
    │   ├── design-pages/
    │   │   ├── DP-MAIN.yaml        # main page 템플릿 (헤더·사이드바·콘텐츠 슬롯)
    │   │   └── DP-POPUP.yaml       # 팝업/모달 페이지 템플릿
    │   ├── platform-baseline/
    │   │   ├── SPEC-000.md         # 공통 기능 baseline (로그인/SSO/RBAC/admin)
    │   │   └── SPEC-OPS-000.md     # 운영 baseline (배포·CI/CD·형상관리·관측성)
    │   ├── decisions/              # 프로젝트별 스택 결정 (규칙 아님)
    │   │   ├── tech-stack.md       # 앱 기술스택 결정
    │   │   └─