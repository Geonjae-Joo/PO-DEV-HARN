# ① PREREQUISITE — 준비 레이어

> 고객사/프로젝트당 **1회** 수행. 주체: 개발 리드/운영자.
> PO 작업(②)과 개발(③)이 시작되기 전에 **디자인 자산·규칙·앱 골격을 준비**한다.
> 산출물은 ②와 ③ 양쪽에 흘러들어가고, **빈 `app_repo` 골격**을 스캐폴드한다 (baseline 실제 구현은 ③ Phase 0의 몫).

---

## Workflow

```
1. 사용자가 기존 design component를 input/design-system/ 에 직접 저장
   (새로 만들지 않음 — 기존 DS 그대로 투입, design token 포함)
     └ hook: ds-guide-validate.py 자동 실행 (목록·필수 필드 검증)

2. design-guide.md 작성 — DS 컴포넌트 목록(이름·props·용도) + 사용 가이드
   (②의 layout-recommend skill과 lint가 이 목록을 허용 집합 원본으로 참조)

3. skill: design-page-builder 실행
   DS를 조합해 빈 페이지 템플릿 생성 (DP-MAIN, DP-POPUP 등)
     └ 스킬이 생성 직후 scripts/design-page-lint.py 직접 호출 (DS 폐쇄 검증 — DS 밖 컴포넌트 사용 시 error)

4. rules 확정
   constitution.md / spine-ids.md / tech-stack.md / ds-closure.md / SPEC-000.md

5. 빈 app_repo 스캐폴드
   기술스택 골격 + .claude/ 하네스 자산(commands/skills/hooks/subagents + rules) + design-system 투입 + SPEC-000 명세 배치
   (★ baseline 코드를 여기서 구현하지 않는다 — ③ Phase 0가 전달 모드 A/B를 정해 구현/가이드 산출)
```

**DoD**: design-guide.md 존재(lint 참조 가능) / design page 최소 1세트(DP-MAIN + DP-POPUP) / constitution에 하드 룰 명시 / SPEC-000 **명세**가 스파인 편입 / rules가 .claude 골격에 번들 / 스파인 ID 규칙 고정.

---

## Harness 자산

> **배치 원칙 (②와 동일):** 단일 스킬이 직접 호출하거나 그 스킬 전용인 스크립트·파일은 **해당 스킬 폴더 아래에 공존**시킨다. 저장 이벤트로 자동 실행되는 훅(hooks.json)과 여러 스킬·레이어가 공유하는 규칙은 **최상위 `hooks/`·`rules/`** 에 둔다.

### Skills — 모델이 필요 시 로드하는 상세 가이드

| 파일 | 설명 |
|---|---|
| `skills/design-page-builder/SKILL.md` | DS 컴포넌트를 조합해 빈 페이지 템플릿(DP-MAIN, DP-POPUP 등)을 생성하는 방법. 허용 집합(design-guide.md) 참조, DS 밖 컴포넌트 발명 금지. 각 템플릿에 스파인 ID(DP-*) 부여. |
| `skills/design-page-builder/scripts/design-page-lint.py` | **design-page-builder 전용.** 스킬이 템플릿 생성 직후 Bash로 직접 호출하는 출력 검증기. 템플릿이 DS 허용 집합 안의 컴포넌트만 쓰는지 + 스파인 ID(DP-*) 존재 검증. (②의 `sufficiency-check.py`·`gate-a-check.py`가 스킬 폴더에 중첩된 것과 동일 패턴.) |

### Hooks — 저장 이벤트 자동 실행 (AI 없는 결정론)

hooks는 `hooks/hooks.json`에 Claude Code hook 이벤트로 정의된다. 스크립트 경로: `${CLAUDE_PROJECT_DIR}/.claude/hooks/`

| 스크립트 | 이벤트 | 트리거 | 설명 |
|---|---|---|---|
| `hooks/ds-guide-validate.py` | `PreToolUse(Write\|Edit)` | design-guide.md 저장 시 | 컴포넌트 목록 형식, 필수 필드(이름·props·용도) 존재 여부 검증. design-guide.md는 사람이 직접 작성·편집하는 공유 foundation 아티팩트(②의 허용 집합 원본)이므로 저장 이벤트 훅으로 최상위에 둔다. (②의 `on-save-schema-validate.py`와 동일 위상.) |

### Rules — 변경 없는 규칙 문서 (전 레이어 공유)

네 규칙 모두 **여러 레이어·스킬이 공유**하는 foundation 규칙이므로 최상위 `rules/`에 둔다 (단일 스킬 전용 규칙이 없음).

| 파일 | 설명 |
|---|---|
| `rules/constitution.md` | **전 레이어 공통 하드 룰.** screen model 단일 원본 / HTML 파생 뷰 저장 허용·직접 편집 금지 / DS 폐쇄 / 스파인 ID / optimistic locking / TDD / 커밋 규칙. |
| `rules/spine-ids.md` | SCR-/CMP-/REQ-/NOTE-/NFR-/SPEC-/T###/DP- 채번 규칙. 전 레이어 공통 적용. |
| `rules/tech-stack.md` | **스택의 단일 출처.** 백엔드·프론트엔드 스택을 ①에서 프로젝트별로 확정한다(고정값 아님). 현재 선택 예시: 백엔드 Spring Boot / 프론트엔드 React+Vite+TS+Tailwind+shadcn/ui. ②·③·스킬·훅이 이 파일을 따른다. 변경 시 DECISIONS.md 갱신. |
| `rules/ds-closure.md` | DS 집합 밖 컴포넌트를 screen model·design page에 추가하는 것을 금지하는 규칙 상세. ①의 design-page-lint + ②의 lint L1이 함께 강제 기준으로 참조. |

---

## 폴더 트리

```
01-PREREQUISITE/
├── README.md
├── input/
│   └── design-system/              # [INPUT] 사용자가 직접 저장하는 기존 DS 원본
│                                   # design token 포함
├── skills/
│   └── design-page-builder/
│       ├── SKILL.md                # DS 조합 → 빈 페이지 템플릿 생성
│       └── scripts/
│           └── design-page-lint.py # [스킬 전용] 템플릿 DS 폐쇄·스파인 ID 검증 (스킬이 직접 호출)
├── hooks/
│   ├── hooks.json                  # Claude Code hook 이벤트 연결 정의
│   └── ds-guide-validate.py        # [저장 이벤트 훅] design-guide.md 형식·목록 검증
├── rules/
│   ├── constitution.md             # 전 레이어 하드 룰 (단일 진실원 원칙 포함)
│   ├── spine-ids.md                # 스파인 ID 채번 규칙
│   ├── tech-stack.md               # 기술스택 결정
│   └── ds-closure.md               # DS 폐쇄 규칙 상세
└── output/                         # [OUTPUT] ②·③로 흘러가는 산출물
    ├── foundation/
    │   ├── design-system/
    │   │   └── design-guide.md     # DS 컴포넌트 목록 + 사용 가이드
    │   │                           # (②의 허용 집합 원본, ③의 구현 참조)
    │   ├── design-pages/
    │   │   ├── DP-MAIN.yaml        # main page 템플릿 (헤더·사이드바·콘텐츠 슬롯)
    │   │   └── DP-POPUP.yaml       # 팝업/모달 페이지 템플릿
    │   └── platform-baseline/
    │       └── SPEC-000.md         # 공통 baseline (로그인/SSO/RBAC/admin)
    └── app-repo-scaffold/
        └── .claude/                # ③ app_repo에 투입될 하네스 자산 골격
                                    # (commands/skills/hooks/subagents/rules)
```

---

## Input / Output

| 구분 | 무엇 | 목적지 |
|---|---|---|
| **Input** | 기존 design component + design token (사용자가 직접 저장) | `input/design-system/` |
| **Output → ②** | foundation 전체: design-system(token 포함) + design-guide.md + design-pages 템플릿 | `output/foundation/` → ②의 `input/` |
| **Output → ③** | `.claude/` 하네스 골격(commands/skills/hooks/subagents **+ rules**) + foundation 전체(design-system·design-guide·design-pages) + **SPEC-000 명세**(구현은 ③ Phase 0) + 빈 app_repo 골격 | `output/app-repo-scaffold/`, `output/foundation/` |

design page 템플릿도 screen model과 동일 규칙 적용: **DS 컴포넌트만 사용 / 스파인 ID(DP-*) 부여 / raw HTML 직접 작성 금지.**
