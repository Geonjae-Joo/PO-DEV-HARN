# 작업 지시서 — ② 플러그인 추출(`po-define`) + 챗봇 패키지 리네임(`po-def-chat`)

> 대상 실행 환경: **Claude Code**(Linux 셸/`git` 사용 가능). 이 지시서는 Cowork 세션에서 샌드박스가 비활성이라 디렉터리 이동을 못 해서, 본 작업을 Claude Code에서 그대로 수행하도록 작성했다.
> 작성: 2026-06-29. 관련: `docs/ADR-001-3runtime-architecture.md`(R1).

---

## 0. 배경 — 무엇이 잘못됐고 무엇으로 바꾸나

직전 작업(ADR-001 R1)에서 ②의 **능력(skills·hooks·rules)** 과 **챗봇 제품**을 한 패키지(`packages/po-dev-chat/`)에 합쳐, 그 패키지 자체를 플러그인으로 등록했다. 그러나:

- `po-dev-chat`은 **챗봇(런타임 제품)의 이름**이다.
- 화면·요구사항 정의 **능력**은 ①(`plugin-prerequisite`)·③(`plugin-ai-web-dev`)처럼 **독립 플러그인**이어야 한다.

따라서 능력을 별도 플러그인 **`po-define`**(디렉터리 `packages/plugin-po-define/`)으로 추출하고, 챗봇 패키지는 **`po-def-chat`**(`packages/po-def-chat/`)으로 리네임한다. 챗봇은 나중에 이 플러그인의 소스를 **가져다 로드**한다.

### 결정(확정)

| 항목 | 값 |
|---|---|
| 플러그인 디렉터리 | `packages/plugin-po-define/` |
| 플러그인 마켓플레이스 ID | `po-define` |
| 챗봇 패키지 디렉터리 | `packages/po-def-chat/` (구 `po-dev-chat`) |
| 마켓플레이스 등록 대상 | **`po-define`** (챗봇 `po-def-chat`은 등록 안 함) |

---

## 1. 목표 구조 (before → after)

**Before (현재):**
```
packages/
├── plugin-prerequisite/        ①
├── plugin-ai-web-dev/          ③
├── harness-core/               공용 코어(rules·lib·render)
└── po-dev-chat/                ② 능력 + 챗봇이 한 패키지에 혼재 (← 분리 대상)
    ├── .claude-plugin/plugin.json   (name: po-dev-chat)
    ├── plugin.json                  (name: po-dev-chat)
    ├── settings.json.legacy
    ├── README.md
    ├── skills/  hooks/  rules/
```

**After (목표):**
```
packages/
├── plugin-prerequisite/        ①
├── plugin-po-define/           ② 능력 플러그인 (추출)  ← 마켓플레이스 등록
│   ├── .claude-plugin/plugin.json   (name: po-define)
│   ├── plugin.json                  (name: po-define)
│   ├── settings.json.legacy
│   ├── README.md                    (플러그인/자산 설명)
│   ├── skills/  hooks/  rules/
├── plugin-ai-web-dev/          ③
├── harness-core/               공용 코어
└── po-def-chat/                ② 챗봇 앱 (리네임). 빌드 예정. plugin-po-define 소스를 로드
    └── README.md                    (챗봇 앱 stub — plugin-po-define + CHATBOT-DEV-GUIDE 가리킴)
```

> **핵심:** `harness-core`는 그대로. `screen-model-schema-v2.md`는 이미 R1에서 `harness-core/rules/`로 이동 완료(단일 출처). `po-dev-chat/rules/screen-model-schema-v2.md`는 redirect stub 상태로 plugin-po-define으로 함께 이동된다.

---

## 2. 디렉터리 이동 (셸 — 순서 엄수)

리포 루트에서 실행한다. `git` 사용 시 history 보존을 위해 `git mv` 권장(비-git이면 `mv`).

```bash
cd <repo-root>   # PO-DEV-HARN

# 2-1) 챗봇 패키지를 통째로 리네임
git mv packages/po-dev-chat packages/po-def-chat

# 2-2) 그 안의 '플러그인 자산'을 새 플러그인 패키지로 추출
mkdir -p packages/plugin-po-define
git mv packages/po-def-chat/skills              packages/plugin-po-define/skills
git mv packages/po-def-chat/hooks               packages/plugin-po-define/hooks
git mv packages/po-def-chat/rules               packages/plugin-po-define/rules
git mv packages/po-def-chat/.claude-plugin      packages/plugin-po-define/.claude-plugin
git mv packages/po-def-chat/plugin.json         packages/plugin-po-define/plugin.json
git mv packages/po-def-chat/settings.json.legacy packages/plugin-po-define/settings.json.legacy
# 현재 README는 ②의 '자산/워크플로우' 설명이므로 플러그인으로 이동
git mv packages/po-def-chat/README.md           packages/plugin-po-define/README.md
```

이 시점에 `packages/po-def-chat/`는 비어 있다(자산이 모두 plugin-po-define으로 이동). → §6에서 챗봇 앱 README stub을 새로 만든다.

> **상대경로 불변성(안심 포인트):** `plugin-po-define/`, `po-def-chat/`, 구 `po-dev-chat/`는 **모두 `packages/`의 직속 자식**이라 깊이가 동일하다. 따라서 이동된 파일들의 상대 참조는 **수정 불필요**:
> - `skills/layout-recommend/SKILL.md`의 `../../../harness-core/rules/screen-model-schema-v2.md` → 여전히 `packages/harness-core/rules/...` 로 해석됨.
> - `hooks/on-save-lint-L1-L4.py`의 `Path(__file__).resolve().parents[2] / "harness-core" / "lib"` → 여전히 `packages/harness-core/lib`.
> - `skills/spec-generator/scripts/*.py`가 `parents[N]/harness-core/...`를 쓰는 경우도 깊이 동일 → 그대로 동작.
> 이동 직후 §7-3 grep으로 파이썬 내부에 하드코딩된 `po-dev-chat` 리터럴이 없는지만 확인하면 된다(현재는 `harness-core/lib/ds_closure.py` 주석 1건뿐, 코드 영향 없음).

---

## 3. 매니페스트 편집 (이동 후)

### 3-1. `packages/plugin-po-define/.claude-plugin/plugin.json`

`name`만 변경(hooks는 `${CLAUDE_PLUGIN_ROOT}` 기준이라 그대로).

```diff
- "name": "po-dev-chat",
+ "name": "po-define",
```
설명 문구의 "(② PO-DEV-CHAT ...)" 도 "② PO-DEFINE — 화면·요구사항 screen model 정의 플러그인" 으로 다듬는다(선택).

### 3-2. `packages/plugin-po-define/plugin.json` (루트 메타)

```diff
- "name": "po-dev-chat",
+ "name": "po-define",
```
`components`(skills/·hooks/·rules/)와 `shared: "../harness-core"`는 그대로 유효.

### 3-3. `.claude-plugin/marketplace.json`

```diff
  "description": "PO Development Harness — 3-layer plugin marketplace (prerequisite · po-dev-chat · ai-web-dev)",
+ "description": "PO Development Harness — 3-layer plugin marketplace (prerequisite · po-define · ai-web-dev)",
  ...
-     "name": "po-dev-chat",
-     "source": "./packages/po-dev-chat",
-     "description": "② PO-DEV-CHAT — ...",
+     "name": "po-define",
+     "source": "./packages/plugin-po-define",
+     "description": "② PO-DEFINE — 화면·요구사항을 screen model(YAML) 계약으로 정의. Cowork/Claude Code 플러그인. (챗봇 po-def-chat이 이 플러그인을 로드)",
```

### 3-4. `marketplace.json` (루트)

```diff
-     { "name": "po-dev-chat",  "source": "./packages/po-dev-chat",         "description": "② ..." },
+     { "name": "po-define",    "source": "./packages/plugin-po-define",    "description": "② 화면·요구사항 screen model 계약 정의 (Cowork/Claude Code 플러그인; 챗봇 po-def-chat이 로드)" },
```

### 3-5. 프로젝트 settings

`projects/devlog/.claude/settings.json`:
```diff
- "enabledPlugins": ["prerequisite", "po-dev-chat", "ai-web-dev"]
+ "enabledPlugins": ["prerequisite", "po-define", "ai-web-dev"]
```

`projects/example/.claude/settings.json`:
```diff
-     "po-dev-chat@po-dev-harness": true,
+     "po-define@po-dev-harness": true,
```

---

## 4. 문서·참조 일괄 치환 규칙

`po-dev-chat`은 두 의미로 쓰였다. **의미별로 다르게** 치환한다.

| 규칙 | 패턴 | 치환 | 의미 |
|---|---|---|---|
| **A** | `packages/po-dev-chat/skills` · `/hooks` · `/rules` | `packages/plugin-po-define/skills` · `/hooks` · `/rules` | 자산(플러그인) 경로 |
| **B** | 마켓플레이스/settings의 플러그인 ID `po-dev-chat` | `po-define` | 플러그인 ID (§3에서 처리) |
| **C** | 챗봇 제품/패키지로서의 `po-dev-chat`, `packages/po-dev-chat/`(앱 디렉터리), "po-dev-chat 챗봇" | `po-def-chat`, `packages/po-def-chat/` | 챗봇 런타임 |
| **D** | 레이어 라벨 "② PO-DEV-CHAT" / "②(po-dev-chat)" 산문 | 유지 가능(또는 "② PO-DEFINE 레이어") | 사람이 읽는 레이어명 — 기능 영향 없음 |

> ⚠️ 무작정 전역 치환 금지. 같은 줄에 자산 경로(A)와 챗봇(C)이 섞일 수 있으니 아래 파일별 표대로 처리한다.

### 4-1. 파일별 치환 체크리스트

| 파일 | 라인(현재) | 처리 |
|---|---|---|
| `README.md` | 61 `packages/po-dev-chat` (패키지 표) | C → `packages/po-def-chat` (챗봇) **또는** 표를 "② 능력=plugin-po-define / 챗봇=po-def-chat" 두 줄로 분리 |
| `README.md` | 62 README 링크 | A → `packages/plugin-po-define/README.md` |
| `README.md` | 243 폴더트리 `po-dev-chat/ # ② → Agent SDK 챗봇 소스` | 트리를 §1 After 구조로 갱신(plugin-po-define + po-def-chat) |
| `docs/ADR-001-...md` | 30, 43, 72~74 | §5 지침대로 D2/D2-a 재서술 |
| `docs/ADR-002-...md` | 4 `packages/po-dev-chat/rules/state-machine.md`, `/skills/layout-recommend/SKILL.md`, `/skills/spec-generator/spec-pack-schema.md` | A → `plugin-po-define/...` |
| `docs/CHATBOT-DEV-GUIDE.md` | 116 `po-dev-chat/rules/` | A → `plugin-po-define/rules/` |
| `docs/MIGRATION-PLAN.md` | 48 트리, 117 헤더, 152 단계 | A(자산)·C(챗봇) 구분해 갱신. 트리 48은 §1 After로 |
| `docs/SUPERPOWERS-CHATBOT-BUILD-GUIDE.md` | 13·146 "po-dev-chat 챗봇" → C | 13,146 C / 111,113,155,156,157,187,201,238 A / 162 예시 `po-dev-chat-app` → `po-def-chat` |
| `USER-GUIDE.md` | 14 "po-dev-chat 스킬", 79 README 링크 | 14: 스킬=plugin-po-define(A) / 79: A → `plugin-po-define/README.md` |
| `USER-GUIDE-devlog-runbook.md` | 17, 166 "po-dev-chat 스킬", 297 스크립트 경로 | A → `plugin-po-define/...` (297: `packages/plugin-po-define/skills/spec-generator/scripts/spec-pack-guard.py`) |
| `guides/PROPOSAL-speckit-correct-usage.md` | 51, 106, 157 | A → `plugin-po-define/skills/spec-generator/...` |
| `guides/PLAN-speckit-tdd-fusion.md` | 248 | A → `plugin-po-define/skills/spec-generator/spec-pack-schema.md` |
| `guides/IMPACT-speckit-fix.md` | 46 | A → `plugin-po-define/skills/spec-generator/spec-pack-schema.md` |
| `packages/plugin-po-define/rules/screen-model-schema-v2.md`(이동된 stub) | 12 "②(po-dev-chat)만의 자산" | D — 유지 또는 "②(po-define)" |
| `packages/harness-core/lib/ds_closure.py` | 6 주석 "② po-dev-chat" | D(선택) — "② po-define" |

> 빠른 후보 탐색: `rg -n "po-dev-chat" --glob '!**/node_modules/**'` 로 재확인하며 규칙 A/C를 적용.

---

## 5. ADR-001 D2/D2-a 재서술 지침

R1 본문이 "②=한 패키지 듀얼 런타임"으로 적혀 있다. **분리 모델**로 정정한다.

- **D2 (정정):** ②의 **능력**은 플러그인 **`po-define`**(`packages/plugin-po-define/`)이다 — `plugin-prerequisite`(①)·`plugin-ai-web-dev`(③)와 동일한 Claude Code/Cowork 플러그인. ②의 **챗봇**은 별도 패키지 **`po-def-chat`**(`packages/po-def-chat/`)으로, Agent SDK로 빌드되며 **`plugin-po-define`의 skill·hook·rule 소스를 로드해 사용**한다. 즉 "능력=플러그인 / 제품=챗봇"으로 분리하고, 챗봇은 플러그인을 가져다 쓴다("같은 로직, 다른 포장"의 정확한 형태).
- **D2-a (유지):** `screen-model-schema-v2.md`는 ①·② 교차 계약이라 `harness-core/rules/` 단일 출처. (변경 없음.)
- R1 "변경 파일" 목록의 경로를 `plugin-po-define/...`로 갱신하고, **R2 개정 이력**을 추가:
  > ### R2 (2026-06-29) — ② 능력/제품 분리
  > - 능력을 `plugin-po-define`으로 추출(마켓플레이스 ID `po-define`), 챗봇 패키지를 `po-def-chat`으로 리네임.
  > - 이유: `po-dev-chat`은 챗봇 제품명. 능력은 ①③처럼 독립 플러그인이어야 함. R1이 둘을 한 패키지에 합친 것을 정정.

---

## 6. README 분할 지침

- `packages/plugin-po-define/README.md` (이동된 기존 README): 헤더를 "② PO-DEFINE — 화면·요구사항 정의 **플러그인**"으로. line 7 런타임 메모를 "이 플러그인은 Cowork/Claude Code에서 직접 사용. 챗봇 `po-def-chat`이 이 소스를 로드한다"로 갱신. 폴더트리(159줄~)를 `packages/plugin-po-define/`로 수정.
- `packages/po-def-chat/README.md` (신규 stub):
  ```markdown
  # ② po-def-chat — PO 화면·요구사항 정의 챗봇 (Agent SDK)

  > 빌드 예정. 이 패키지는 ②의 **챗봇 런타임**이다.
  > 능력(skill·hook·rule)은 플러그인 **`po-define`**(`../plugin-po-define/`)에 있고, 챗봇은 그 소스를 코드로 로드한다.
  > 빌드: `docs/CHATBOT-DEV-GUIDE.md` · `docs/SUPERPOWERS-CHATBOT-BUILD-GUIDE.md`.
  ```

---

## 7. 검증 (Claude Code에서)

### 7-1. 플러그인 lint·훅 동작
```bash
# DP lint (① 산출물 — 경로 무관, plugin-prerequisite 그대로)
python packages/plugin-prerequisite/skills/design-page-builder/scripts/design-page-lint.py --root projects/devlog
# ② schema 검증·lint (이동된 위치에서 직접 호출 — argv 모드)
python packages/plugin-po-define/hooks/on-save-schema-validate.py projects/example/model_repo/screens/SCR-*.yaml
python packages/plugin-po-define/hooks/on-save-lint-L1-L4.py       projects/example/model_repo/screens/SCR-*.yaml
```
기대: design-page-lint **error 0**(devlog DP-MAIN·DP-POPUP). 훅은 harness-core/lib import 성공 + 정상 종료.

### 7-2. 플러그인 로딩
```bash
/plugin marketplace add .
/plugin            # po-define 이 prerequisite·ai-web-dev 와 함께 보이는지
```
`projects/devlog` 를 열어 enabledPlugins에 `po-define` 활성 확인.

### 7-3. dangling 참조 grep (0건이어야 함)
```bash
rg -n "packages/po-dev-chat" --glob '!**/node_modules/**'          # 자산 경로 잔여 → 0
rg -n "\"po-dev-chat\"" --glob '!**/node_modules/**'                # 매니페스트 ID 잔여 → 0
rg -n "po-dev-chat" packages/ --glob '*.py'                         # 파이썬 하드코딩 → 주석 외 0
```

### 7-4. JSON 문법
```bash
python -c "import json,glob;[json.load(open(f,encoding='utf-8')) for f in ['marketplace.json','.claude-plugin/marketplace.json','packages/plugin-po-define/plugin.json','packages/plugin-po-define/.claude-plugin/plugin.json','projects/devlog/.claude/settings.json','projects/example/.claude/settings.json']]; print('JSON OK')"
```

---

## 8. 주의·롤백

- 한 커밋으로 묶지 말고 (1)디렉터리 이동 (2)매니페스트 (3)문서 순으로 나눠 커밋하면 리뷰·롤백이 쉽다.
- `git mv`를 썼으면 이동은 history에 rename으로 남는다. 문제 시 `git restore`/`git revert`로 단계 롤백.
- 빈 `packages/po-dev-chat/`가 디스크에 남으면 삭제(`rmdir`). Windows 탐색기로 지워도 됨.
- 챗봇 빌드는 이 작업 범위 밖(별도). 본 지시서는 **능력 플러그인 추출 + 챗봇 패키지 리네임**까지만.

---

## 부록 — 현재 상태(직전 Cowork 세션이 만든 것)

이미 존재하므로 **새로 만들지 말고 이동·리네임**할 것:
- `packages/po-dev-chat/.claude-plugin/plugin.json`, `packages/po-dev-chat/plugin.json` (name: po-dev-chat) → 이동 후 name=po-define
- 두 `marketplace.json`에 `po-dev-chat` 엔트리 등록됨 → po-define으로 갱신
- `projects/{devlog,example}/.claude/settings.json`에 po-dev-chat 활성화됨 → po-define
- `packages/po-dev-chat/hooks/on-save-*.py` 는 stdin payload+SCR 필터 적용됨(plugin Write|Edit 훅 안전) → 그대로 이동
- `harness-core/rules/screen-model-schema-v2.md` 단일 출처 이동 완료, `po-dev-chat/rules/screen-model-schema-v2.md` 는 redirect stub → stub째로 plugin-po-define/rules로 이동
- `design-page-lint.py` §7 검사(source.kind·position.base·col_span 픽셀 금지) 추가됨 → 위치 그대로(① 플러그인)
