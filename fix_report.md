# PO-DEV-HARN 하네스 고도화 — Fix Report

> 작성: 2026-06-30 · 검토 대상: `packages/{plugin-prerequisite, plugin-po-define, plugin-ai-web-dev, po-def-chat, harness-core}` + 루트 문서
> 목적: 3개 플러그인의 README·스킬·훅·공유 자산을 *전체 워크플로* 관점에서 검토하고, 오류·모순·개선점을 기록. 간단한 항목은 바로 수정, 영향도가 큰 항목은 본 문서에 남겨 사용자 판단을 돕는다.

---

## 0. 종합 평가

전반적으로 **설계 의도가 매우 일관되고 문서화 수준이 높다.** 3-레이어(① 준비 → ② 정의 → ③ 구현) 경계 원칙("①은 명세, ②는 계약, ③은 구현")이 README·constitution·스킬 전반에 반복적으로 강제되고 있고, 교차 계약(spine-ids · ds-closure · screen-model-schema-v2)을 `harness-core/` 단일 출처로 모은 구조도 견고하다. 기계 검증기(lint L1~L5, gate-a-check, spec-pack-guard, layout-hash-guard)도 대부분 스키마 v2와 정확히 정합한다.

다만 **마이그레이션(구 `.claude/` 구조 → `packages/` 모노레포, ② 챗봇 분리) 과정에서 남은 잔여 불일치**가 여러 곳에 있고, 그중 하나(②→③ 브리지 `pack-to-spec.py`)는 기능적으로 깨져 있다. 아래에 심각도별로 정리한다.

### 요약 표

| ID | 심각도 | 항목 | 상태 |
|---|---|---|---|
| H1 | 🔴 High | `pack-to-spec.py`가 screen-model-schema-v2와 다른 필드명을 읽음 (②→③ 브리지 무력화) | **판단 필요** |
| M1 | 🟠 Medium | `gate-a-check.py`가 `[L5 ERROR]`를 게이트 차단 태그에서 누락 | ✅ 수정함 |
| M2 | 🟠 Medium | ① `dp-render.py` 훅 3중 등록 불일치 (settings.json↔plugin.json↔README) | **판단 필요** |
| M3 | 🟠 Medium | `.claude/rules/` 구 구조 경로가 스킬·스키마 다수에 잔존 | **판단 필요** (1건만 수정) |
| L1 | 🟡 Low | "② PO-DEV-CHAT" 스테일 명칭 13곳 (현 정식명 "② PO-DEFINE") | 부분 수정 / 권고 |
| L2 | 🟡 Low | `marketplace.json` 2개 중복 (`name` 불일치: po-dev-harness vs po-dev-harn) | **판단 필요** |
| L3 | 🟡 Low | 플러그인당 `plugin.json` 2개 (루트 메타 vs `.claude-plugin/` 매니페스트) — 버전 드리프트 위험 | 권고 |
| L4 | ⚪ Info | `ds-closure.md`의 `on-save-lint-L1.py` 오타 → `on-save-lint-L1-L4.py` | ✅ 수정함 |
| L5 | ⚪ Info | `screen-model-schema-v2.md`의 `.claude/rules/state-machine.md` 경로 | ✅ 수정함 |
| L6 | ⚪ Info | `gate-a-check.py` 주석 "5가지 조건" → 실제 6가지 | ✅ 수정함 |

---

## 1. 워크플로 의도 분석 (전체 관점)

핵심 데이터 흐름은 **스파인 ID로 꿰어지는 단방향 파이프라인**이다.

```
①  DP-* (design page) ─ instantiate ─▶ ②  SCR-* (screen model, 단일 진실원)
   ds-allowlist.md ───── DS 폐쇄 ─────▶    actions[](REQ-) · ENT-/EXT- · JRN-
   SPEC-000/OPS-000 ──── 명세 ─────────▶ ③  Gate A(confirmed) → PACK-* 발행
   tech-stack/ops-stack ─ 결정 핀 ─────▶    pack-to-spec → spec.md → plan → tasks → TDD
                                            layout_hash 가드로 ②확정 좌표 freeze
   ③ ──── Change Order(dismiss/amend/regenerate) ────▶ ② 재확정·re-pin (환류)
```

이 의도는 문서상 매우 잘 표현되어 있고, 각 경계에서 "발명 금지(no new contract)"가 반복 강조된다. **연결의 무결성을 보장하는 장치**도 잘 갖춰져 있다:

- **DS 폐쇄**: `harness-core/lib/ds_closure.py` 단일 출처를 ①(design-page-lint)·②(on-save-lint L1)가 동시 import (실패 시 동치 폴백). ✔
- **전역 ID 유일성**: `harness-core/lib/spine_ledger.py`를 Gate A 조건6이 강제. ✔
- **결정론적 좌표 계약**: `layout_hash`(좌표 전용, D8 시각자산과 무관) → ③ `layout-hash-guard.py`가 진입 시 재검증. ✔
- **constitution 단일 출처**: 권위는 ① `harness-core/rules/constitution.md`, ③ `.specify/memory/constitution.md`는 `speckit-constitution`이 동기화하는 파생. (단, `/speckit-constitution` 정의는 ③에 있고 ①이 그 결과 tech-stack 핀을 소유 — 의도된 교차 의존, 문서화됨.) ✔

**결론:** 3개 플러그인은 구조적으로 잘 연결되어 있다. 단 한 곳, **②→③ 핸드오프의 *기계 브리지*(`pack-to-spec.py`)가 실제 스키마와 어긋나** 자동 초안 생성이 무력화된다(H1). 이 부분이 워크플로 관점에서 가장 큰 단절점이다.

---

## 2. 발견 항목 상세

### 🔴 H1 — `pack-to-spec.py` ↔ screen-model-schema-v2 필드 불일치 (②→③ 브리지)

**위치:** `packages/plugin-ai-web-dev/.specify/scripts/bash/pack-to-spec.py`

**증상:** 이 스크립트는 `/speckit-specify`의 "산문 직접작성 금지, 팩에서 파생하라"를 기계화하는 **G2 브리지**다. 그런데 `model_repo/screens/SCR-*.yaml`(스키마 v2)을 읽으면서 **존재하지 않는 필드명**을 참조한다:

| pack-to-spec.py가 읽는 필드 | 실제 schema v2 필드 | 결과 |
|---|---|---|
| `sdoc.get("title")` | `screen.name` (중첩) | 화면명 `[화면명]`으로 공란 |
| `sdoc.get("description")` | (없음) | 공란 |
| `sdoc.get("components")` | `layout[]` (각 `id: CMP-*`) | CMP 목록 `[화면 모델 components 참조]`로 공란 |
| `sdoc.get("requirements")` | `actions[]` (각 `id: REQ-*`) | "**화면 모델에 requirements 없음**" 출력 |
| 각 req의 `action`/`user_story`/`api`/`validation` | `behavior`/`acceptance`/`outcome`/`permission` | Given/When/Then 본문 공란 |
| `sdoc.get("open_questions")` | `intake.open_questions[]` (중첩) | deferred 항목 누락 |

**근거(교차 검증):** 같은 레포의 `on-save-lint-L1-L4.py`와 `gate-a-check.py`는 **정확히 스키마 v2 필드**(`doc["screen"]["id"]`, `doc["actions"]`, `doc["intake"]["open_questions"]`, `source.ref`, `meta.interactive`)를 읽는다. 즉 스키마 v2가 정본이고 **`pack-to-spec.py`만 옛 스키마(평면 `requirements`/`components`)를 가정**하고 있다. 결과적으로 생성되는 `spec.md` 초안은 거의 전 항목이 `[검토 필요]`/`[없음]`으로 비어, "산문 날조 금지 + 자동 파생"이라는 G2 설계 목적이 사실상 작동하지 않는다.

**왜 High인가:** ②가 발행한 PACK을 ③ speckit으로 끌어오는 **유일한 자동 브리지**가 빈 껍데기를 만들면, 개발자가 결국 손으로 spec.md를 채우게 되어 하네스의 핵심 가치(계약→코드 무손실 전달)가 훼손된다.

**권장 조치 (직접 수정하지 않고 남김 — 영향도 큼):**
스키마 v2 기준으로 필드 접근을 재작성. 핵심 매핑:
- 화면 제목: `sdoc["screen"]["name"]`
- CMP 목록: `[it["id"] for it in sdoc.get("layout", []) if str(it.get("id","")).startswith("CMP-")]`
- REQ/acceptance: `sdoc.get("actions", [])`를 순회하며 `a["id"]`, `a["behavior"]`, `a.get("acceptance", [])`(Gherkin 원문 우선), `a["outcome"]["target"]`, `a.get("permission")` 사용. Gherkin 부재 시에만 "파생 초안" 표기.
- open items: `sdoc.get("intake", {}).get("open_questions", [])`에서 `status in (deferred)` 추출.
- notes: 현행대로 `notes[]` + `body`(이미 정합).

> 검토 포인트: 혹시 `model_repo/screens/`에 *옛 스키마* 화면 파일이 실제로 존재해 양쪽을 모두 지원해야 하는지 확인 필요. 아니라면 v2 단일 지원으로 단순화 권장. 원하시면 이 스크립트 v2 재작성안을 만들어 드리겠습니다.

---

### 🟠 M1 — `gate-a-check.py`가 `[L5 ERROR]`를 차단 태그에서 누락 ✅ 수정 완료

**위치:** `packages/plugin-po-define/skills/gate-a-check/scripts/gate-a-check.py` (`check_lint`)

**증상:** lint 훅(`on-save-lint-L1-L4.py`)은 L5(canvas-bounds: 가로 봉쇄·locked 슬롯 보호) 위반을 `[L5 ERROR]`로 내보내며 *"L5 error → Gate A 차단"* 으로 문서화돼 있다. 그런데 gate-a-check는 차단 대상 태그를 `("[L2 ERROR]", "[L3 ERROR]", "[L4 ERROR]")`로만 검사해 **L5 위반이 Gate A를 그대로 통과**했다. (lint는 L5만 있을 때 exit 0이므로 returncode 경로로도 안 걸림.)

**수정:** 태그 튜플에 `"[L5 ERROR]"` 추가, 메시지·통과로그를 `L1~L5`로 정정. 게이트가 의도대로 캔버스 경계 위반을 차단하도록 강화됨. (동작이 *더 엄격해지는* 변경이므로 인지 차원에서 기록.)

---

### 🟠 M2 — ① `dp-render.py` 훅 3중 등록 불일치 (+ ①↔② 훅 컨벤션 불일치)

**위치:** `packages/plugin-prerequisite/` 의 `settings.json` · `.claude-plugin/plugin.json` · `README.md`

**증상:** `dp-render.py`(DP-*.yaml 저장 시 미리보기 HTML 자동 렌더 — ②의 `render_screen` 자동렌더에 대응)가 등록처마다 다르게 잡혀 있다:

| 출처 | 등록된 PostToolUse 훅 |
|---|---|
| `settings.json` | `ds-guide-validate.py` + **`dp-render.py`** (2개) |
| `.claude-plugin/plugin.json` | `ds-guide-validate.py` (1개, dp-render 누락) |
| `README.md` 훅 표 · 폴더 트리 | `ds-guide-validate.py`만 기재 (dp-render 미문서화) |

게다가 **②는 이미 컨벤션을 정리**했다 — `settings.json`을 `settings.json.legacy`로 강등하고 활성 훅을 `.claude-plugin/plugin.json`에 두었다. 반면 **①은 활성 `settings.json`을 유지**한다. 두 플러그인의 훅 정의 위치 자체가 어긋난다.

**핵심 질문(사용자 판단 필요):**
1. Claude Code 플러그인의 훅 권위 파일을 `.claude-plugin/plugin.json`으로 통일할 것인가? (그렇다면 현재 `dp-render.py`는 실제로 로드되지 않아 **DP 저장 시 자동 렌더가 동작하지 않는 상태**일 가능성이 높다.)
2. ①도 ②처럼 `settings.json` → `.legacy`로 강등하고 `.claude-plugin/plugin.json`에 `dp-render.py`를 추가할 것인가?

**권장:** `.claude-plugin/plugin.json`을 단일 권위로 통일 → 거기에 `dp-render.py` 추가 → README 훅 표·폴더 트리에 `dp-render.py` 1줄 추가 → `settings.json`은 `.legacy`로 강등. (런타임 훅 동작이 바뀌므로 직접 수정하지 않고 남김. 승인 시 일괄 반영 가능.)

---

### 🟠 M3 — `.claude/rules/` 구 구조 경로 잔존 (스킬·스키마 다수)

**증상:** 마이그레이션 후 규칙은 `harness-core/rules/`(constitution·spine-ids·ds-closure·screen-model-schema-v2) 또는 `packages/plugin-*/rules/`(state-machine·tdd-policy·commit-convention 등)로 이동했으나, 다수 파일이 옛 `.claude/rules/...` 경로로 참조한다:

| 파일 | 참조 | 정정 대상 |
|---|---|---|
| `harness-core/rules/screen-model-schema-v2.md:238` | `.claude/rules/state-machine.md` | `plugin-po-define/rules/state-machine.md` — ✅ 수정함 |
| `plugin-ai-web-dev/skills/speckit-implement/SKILL.md:26` | `.claude/rules/tdd-policy.md` | `plugin-ai-web-dev/rules/tdd-policy.md` |
| `plugin-ai-web-dev/skills/complex-bl/SKILL.md:46` | `.claude/rules/tdd-policy.md` | 〃 |
| `plugin-ai-web-dev/skills/coding-style/SKILL.md:60` | `.claude/rules/commit-convention.md` | `plugin-ai-web-dev/rules/commit-convention.md` |
| `plugin-ai-web-dev/skills/design-system-usage/SKILL.md:22,61` | `.claude/rules/ds-closure.md` | `harness-core/rules/ds-closure.md` |
| `plugin-prerequisite/docs/project-design-guide.md:16,254` | `.claude/rules/{ds-closure,constitution}.md` | `harness-core/rules/...` |

**주의(판단 필요):** `app_repo/.claude/skills/baseline-guides/...`(③ 런타임)는 **정당한 경로**이므로 건드리면 안 된다. 또한 ③ 일부 스킬은 *런타임에 규칙이 app_repo `.claude/rules/`로 번들된다*는 전제(`design-system-usage:22` 주석)일 수 있어, 단순 일괄치환이 위험하다. → **통일 컨벤션을 먼저 결정**(빌드/번들 경로 vs 소스 경로 표기 규약)한 뒤 일괄 정정 권장. 우선 명확한 1건(harness-core 내부 schema-v2)만 수정함.

---

### 🟡 L1 — "② PO-DEV-CHAT" 스테일 레이어 명칭 (13곳)

**증상:** 레이어 ②의 현 정식명은 README·marketplace 기준 **"② PO-DEFINE" / 플러그인 `po-define`**, 챗봇은 별도 `po-def-chat`이다. 그런데 옛 명칭 "PO-DEV-CHAT"이 다음에 잔존한다:

- ② 스킬 9개 frontmatter `layer: ② PO-DEV-CHAT` — sufficiency-check, external-intake, entity-intake, spec-generator, action-interview, note-intake, layout-recommend, journey-map, gate-a-check
- `plugin-prerequisite/skills/ds-bootstrap/SKILL.md:51` — "PO-DEV-CHAT lint L1" (**소비자 표기가 사실과 다름** → `② po-define lint`로 ✅ 수정함)
- `plugin-prerequisite/docs/{project-design-guide.md:47, first_design_page_guide.md:242}`
- `plugin-ai-web-dev/.specify/memory/constitution.md:15`

**조치:** 의미상 위험이 없는 라벨이므로 전역 치환(`② PO-DEV-CHAT` → `② PO-DEFINE`)을 권장. 이미 읽은 ds-bootstrap 1건만 수정함. 나머지 12곳은 파일을 추가로 열어야 하므로 일괄 반영을 원하시면 한 번에 처리하겠습니다(단순 find-replace, 로직 무영향).

---

### 🟡 L2 — `marketplace.json` 2개 중복 (`name` 불일치)

**위치:** 루트 `marketplace.json` vs `.claude-plugin/marketplace.json`

**증상:** 두 파일이 동일한 3개 플러그인을 등록하지만 `name`이 다르다 — 루트는 `"po-dev-harness"`, `.claude-plugin/`은 `"po-dev-harn"`(레포 폴더명과 일치). 설명·owner·category도 상이. `/plugin marketplace add .`는 통상 `.claude-plugin/marketplace.json`을 읽으므로 루트 파일은 사용되지 않을 가능성이 크다(드리프트 위험).

**권장:** `.claude-plugin/marketplace.json`을 단일 출처로 유지하고 루트 `marketplace.json`은 제거하거나 동일 내용으로 동기화. (어느 쪽을 정본으로 둘지 사용자 결정 필요.)

---

### 🟡 L3 — 플러그인당 `plugin.json` 2벌

**증상:** 각 플러그인에 루트 `plugin.json`(커스텀 메타: `components`/`shared`/`speckit`/`_note`)과 `.claude-plugin/plugin.json`(CC 매니페스트: `skills`/`hooks`/`agents`)이 공존한다. 현재 `version`은 양쪽 일치(① 0.2.0 / ② 0.1.0 / ③ 0.2.0)하나, **두 곳에 같은 메타가 흩어져 있어 갱신 시 드리프트 위험**이 있다. (의도된 분리일 수 있으나, 단일 출처 원칙과는 어긋남.)

**권장:** 루트 `plugin.json`은 "하네스 전용 메타(shared/speckit 경로 등)"만 남기고 `name/version/description`은 `.claude-plugin/plugin.json`을 정본으로 참조하도록 정리. 최소한 README에 "버전 정본은 `.claude-plugin/plugin.json`" 명시 권장.

---

### ⚪ 기타 (참고)

- **`po-def-chat`은 README 스텁만 존재**(빌드 예정) — 오류 아님. marketplace/② README와 정합.
- **`on-save-lint-L1-L4.py` 파일명 vs 실제 L1~L5 수행**: 파일명은 L1-L4지만 L5(canvas-bounds)까지 수행한다. README에 "L5 추가"가 명시돼 있어 혼선은 적으나, 차후 파일명/문구를 `L1-L5`로 통일하면 더 명확.
- **speckit git 스킬 `source: commands/...`**: `.specify/extensions/git/commands/`의 원본을 가리키는 provenance 표기로 보이며 해당 파일들은 실존. `speckit-scaffold`의 `source: commands/speckit.scaffold.md`만 대응 파일이 안 보여 차후 확인 권장(메타 필드라 기능 영향 없음).

---

## 3. 이번에 바로 수정한 항목 (5건)

| 파일 | 변경 |
|---|---|
| `plugin-po-define/skills/gate-a-check/scripts/gate-a-check.py` | `[L5 ERROR]`를 Gate A 차단 태그에 추가 + 메시지/통과로그 `L1~L5`로 정정 (M1) |
| `plugin-po-define/skills/gate-a-check/scripts/gate-a-check.py` | 주석 "5가지 조건 검사" → "6가지 조건 검사" (L6) |
| `harness-core/rules/ds-closure.md` | `on-save-lint-L1.py` → `on-save-lint-L1-L4.py` (L4) |
| `harness-core/rules/screen-model-schema-v2.md` | `.claude/rules/state-machine.md` → `plugin-po-define/rules/state-machine.md` (L5/M3 일부) |
| `plugin-prerequisite/skills/ds-bootstrap/SKILL.md` | ds-allowlist 소비자 표기 "PO-DEV-CHAT lint L1" → "② po-define lint L1 (on-save-lint-L1-L4.py)" (L1 일부) |

## 4. 사용자 판단이 필요한 항목 (요약)

1. **H1** — `pack-to-spec.py`를 스키마 v2로 재작성할지(권장). 옛 스키마 화면 파일 잔존 여부 확인 필요.
2. **M2** — ① 훅 권위 파일 통일(`.claude-plugin/plugin.json`) + `dp-render.py` 등록/문서화 + `settings.json` 강등 여부.
3. **M3** — `.claude/rules/` 경로 표기 규약 확정(소스 경로 vs 런타임 번들 경로) 후 일괄 정정.
4. **L1** — "PO-DEV-CHAT → PO-DEFINE" 전역 치환 일괄 반영 여부(12곳 잔여).
5. **L2/L3** — `marketplace.json` / `plugin.json` 이중화 정리 방향.

> 위 항목 중 승인해 주시는 것은 바로 반영하겠습니다.
