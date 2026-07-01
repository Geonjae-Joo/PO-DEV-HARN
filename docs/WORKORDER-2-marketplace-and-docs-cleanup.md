# 작업 지시서 2 — 마켓플레이스 이름 통일 + README/ADR 문구 보정

> 대상 실행 환경: **Claude Code**(셸/`git`). 선행 작업: `WORKORDER-extract-po-define-plugin.md`(플러그인 추출·리네임) 완료 상태 전제.
> 작성: 2026-06-29. 관련: `docs/ADR-001-3runtime-architecture.md`.

---

## 0. 목적

② 플러그인 추출(R2) 검수에서 발견된 2가지를 정리한다.

1. **(높음) 마켓플레이스 이름 불일치** — 플러그인 로딩이 깨질 수 있는 실제 버그.
2. **(낮음) README/ADR 문구가 R2와 부분적으로 어긋남** — 정확성·가독성 보정.

> 이건 기능 추가가 아니라 **정합성 정리**다. 코드/스키마 로직은 건드리지 않는다.

---

## Part A — 마켓플레이스 이름 통일 (우선)

### A-1. 현재 상태 (불일치)

| 위치 | 현재 `name` / 한정자 | 비고 |
|---|---|---|
| `.claude-plugin/marketplace.json` | **`po-dev-harn`** ← 틀림 | **Claude Code 정본**(아래 근거) |
| `marketplace.json` (루트) | `po-dev-harness` | 중복 파일(내용도 정본과 다름). **Claude Code는 안 읽음** |
| `package.json` | `po-dev-harness` | npm 워크스페이스명 — 마켓플레이스명과 **별개 네임스페이스**(우연히 일치, 의존 아님) |
| `projects/example/.claude/settings.json` | `@po-dev-harness` ×3 | 플러그인 활성화 한정자 |
| `projects/devlog/.claude/settings.json` | 리스트형(한정자 없음) | 마켓플레이스명 의존 없음 |

문제: settings가 `po-define@po-dev-harness`로 참조하는데, 정본(`.claude-plugin/marketplace.json`) 이름이 `po-dev-harn`이라 **매칭 실패** → 플러그인이 로드 안 될 수 있다.

> **정본 근거(검증 완료, Claude Code 공식 문서):** "Create `.claude-plugin/marketplace.json` in your repository root." / 트러블슈팅 "Check that `.claude-plugin/marketplace.json` exists" / 에러 "File not found: `.claude-plugin/marketplace.json` — Missing manifest". 즉 Claude Code는 **`.claude-plugin/marketplace.json`만** 읽고 루트 `marketplace.json`은 기능상 무시한다. 출처: https://docs.claude.com/en/docs/claude-code/plugin-marketplaces

### A-2. 결정

- **정본 = `.claude-plugin/marketplace.json`** (Claude Code 규약 위치).
- **통일 이름 = `po-dev-harness`** (이미 3곳이 사용 — 다수·일관).
- 루트 `marketplace.json`은 **중복**이므로 제거(아래 A-4). 단일 출처 유지.

### A-3. 정본 이름 수정

`.claude-plugin/marketplace.json`:
```diff
- "name": "po-dev-harn",
+ "name": "po-dev-harness",
```
(이 파일의 `plugins` 배열은 이미 prerequisite·po-define·ai-web-dev로 정확함 — 변경 불필요.)

### A-4. 중복 루트 `marketplace.json` 제거 + 문서 참조 갱신

루트 `marketplace.json`은 `.claude-plugin/marketplace.json`과 역할이 겹치고 내용이 더 빈약하다(owner·category 없음). Claude Code는 루트 파일을 쓰지 않는다(A-1 근거).

> ⚠️ **영향 확인 결과(중요): "참조 0건"이 아니다.** 문서 2곳이 루트 `marketplace.json`을 폴더트리/단계 항목으로 참조한다. 삭제하려면 **같이 갱신**해야 한다(둘 다 `①③` 표기라 R2 기준으로도 부정확):
> - `README.md:211` — `├── marketplace.json   # ①③ Claude Code 플러그인 마켓플레이스`
> - `docs/MIGRATION-PLAN.md:42` — `├── marketplace.json   # ①③ 플러그인 마켓플레이스`
> - `docs/MIGRATION-PLAN.md:149` — 단계 문장의 `+ marketplace.json`

```bash
# 잔여 참조 재확인(삭제 전)
rg -n "(^|[^.])marketplace\.json" --glob '!**/node_modules/**' --glob '!**/.claude-plugin/**' --glob '!**/docs/WORKORDER*'
# 위 3건(README:211, MIGRATION-PLAN:42,149)을 .claude-plugin/marketplace.json + ①②③ 로 먼저 수정한 뒤
git rm marketplace.json
```

수정 예시:
- `README.md:211` → `├── .claude-plugin/marketplace.json   # ①②③ Claude Code/Cowork 플러그인 마켓플레이스 (정본)`
- `docs/MIGRATION-PLAN.md:42` → `├── .claude-plugin/marketplace.json  # ①②③ 플러그인 마켓플레이스`
- `docs/MIGRATION-PLAN.md:149` → `+ .claude-plugin/marketplace.json`

> 만약 어떤 외부 도구가 루트 파일을 요구한다면(드뭄), 제거 대신 **정본을 복사해 동기화**하고 두 파일 `name`을 모두 `po-dev-harness`로 맞춘다. 단, "두 벌 유지"는 향후 drift 위험이 있으니 비권장.

> **확인했고 영향 없는 항목:** `.claude/settings.local.json`(설치 상태 없음, 권한만) · USER-GUIDE 4곳의 `/plugin marketplace add .`(`.`은 `.claude-plugin/`로 해석 → 무관) · `package.json`의 `po-dev-harness`(npm 워크스페이스명, 독립).

### A-5. (선택) devlog settings 형식 정렬

`projects/devlog/.claude/settings.json`은 리스트 형식이라 마켓플레이스명 의존이 없다(현재도 동작). example과 형식을 맞추고 싶으면 객체+한정자 형식으로:
```diff
- "enabledPlugins": ["prerequisite", "po-define", "ai-web-dev"]
+ "enabledPlugins": {
+   "prerequisite@po-dev-harness": true,
+   "po-define@po-dev-harness": true,
+   "ai-web-dev@po-dev-harness": true
+ }
```
(필수 아님. 리스트 형식 유지해도 무방.)

### A-6. 검증
```bash
rg -n "po-dev-harn\b" --glob '!**/node_modules/**'   # 'po-dev-harn'(짧은 형) → 0건이어야
rg -n "po-dev-harness" --glob '!**/node_modules/**'  # 정본·package·settings 일치 확인
python -c "import json;[json.load(open(f,encoding='utf-8')) for f in ['.claude-plugin/marketplace.json','package.json','projects/example/.claude/settings.json']];print('JSON OK')"
/plugin marketplace add .    # po-dev-harness 로 등록되는지
/plugin                      # prerequisite·po-define·ai-web-dev 3개 노출 확인
```

> **운영 영향(마켓플레이스 캐시):** 이전에 `/plugin marketplace add .`을 **옛 이름 `po-dev-harn`으로 이미 등록**했다면, 리네임 후 Claude Code 사용자 설정에 옛 이름이 캐시돼 있을 수 있다. 그 경우 한 번 정리한다:
> ```
> /plugin marketplace remove po-dev-harn     # 옛 등록 제거(있을 때만)
> /plugin marketplace add .                  # po-dev-harness 로 재등록
> ```
> (처음 등록하는 환경이면 불필요.)

---

## Part B — README/ADR 문구 보정

### B-1. `README.md` line 64 — R2 정확성

현재:
> ①②③ 모두 `marketplace.json`에 등록된 Claude Code/Cowork 플러그인이다(`/plugin marketplace add .`). ②는 **듀얼 런타임**(ADR-001 R1) — 플러그인으로 IDE·Cowork에서 직접 쓰면서, 같은 소스(skill·hook·rule)를 Agent SDK 챗봇으로도 빌드 예정이다 ...

문제: R2 기준으로 **등록되는 건 플러그인 `po-define`**이고, 챗봇 `po-def-chat`은 미등록이다. "①②③ 모두 플러그인"은 부정확.

권장(예시):
> 마켓플레이스(`.claude-plugin/marketplace.json`)에 등록되는 Claude Code/Cowork 플러그인은 **① prerequisite · ② po-define · ③ ai-web-dev** 세 개다(`/plugin marketplace add .`). ②는 **능력/제품 분리**(ADR-001 R2) — 능력은 플러그인 `po-define`(IDE·Cowork에서 직접 사용), 챗봇 `po-def-chat`은 별도 패키지로 빌드 예정이며 같은 플러그인 소스를 로드한다(미등록). 교차 계약 `screen-model-schema-v2`는 `harness-core/rules/` 단일 출처.

### B-2. `docs/ADR-001-...md` D2 헤더 — 개정 표기

현재: `### D2. 같은 harness-core → 런타임 (R1 개정)`
→ 본문이 R2 내용을 담으므로:
```diff
- ### D2. 같은 harness-core → 런타임 (R1 개정)
+ ### D2. 같은 harness-core → 런타임 (R1·R2 개정)
```

### B-3. (선택) `README.md` 폴더트리 순서 — ①②③ 정렬

폴더트리에서 `plugin-po-define`가 `plugin-ai-web-dev` **뒤**에 와서 시각적으로 ①③② 순이다. 레이어 순서대로 보이게 `plugin-po-define`(②) 블록을 `plugin-ai-web-dev`(③) **앞**으로 이동. (미관상, 기능 영향 없음.)

---

## Part C — (선택) 패키지 매니페스트 중복 정리

각 플러그인 패키지에 매니페스트가 두 벌 있다:
- `.claude-plugin/plugin.json` — **Claude Code 정본**(name·skills·hooks).
- `plugin.json`(루트) — 커스텀 메타(components·shared·_note). Claude Code는 안 읽음.

①③에도 같은 구조라 이번 작업의 범위는 아니다. 다만 마켓플레이스 단일화와 같은 맥락에서, 루트 `plugin.json`을 **메타 전용으로 유지할지 / 제거할지** 3개 플러그인 일괄로 정책을 정하면 일관성이 좋아진다. (지금 당장 필수 아님 — 별도 결정 권장.)

---

## 실행 순서 & 커밋 분리

1. **Part A** (마켓플레이스) — 가장 위험한 항목 먼저. 커밋: `fix(marketplace): unify name to po-dev-harness, drop duplicate root manifest`
2. **Part B** (문서 문구) — 커밋: `docs: align README/ADR wording with R2 split`
3. **Part C** — 별도 결정 후 진행(이번 미포함 가능).

각 Part 후 §A-6 검증을 재실행. 끝나면 `WORKORDER-extract-po-define-plugin.md` §7 전체 검증(design-page-lint·hook·/plugin)도 한 번 통과시켜 마무리.

---

## 범위 밖 (이번 미포함, 기록만)

- **훅 차단 코드 검증**: PreToolUse `on-save-schema-validate.py`가 에러 시 `exit 1`. Claude Code에서 저장을 실제 차단하려면 `exit 2`가 맞는지 현행 훅 스키마로 확인 필요(ADR-001 후속 목록에 이미 있음).
- **챗봇 빌드**: `po-def-chat` 실제 구현은 별도.
