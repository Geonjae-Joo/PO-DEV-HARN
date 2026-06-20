# Superpowers로 ② PO-DEV-CHAT 챗봇 만들기 — 빌드 가이드

> **목적**: [obra/superpowers](https://github.com/obra/superpowers) 플러그인의 *브레인스토밍 → 계획 → TDD 구현* 워크플로우를 써서, 아직 소스 상태인 **② PO-DEV-CHAT 챗봇(Claude Agent SDK 웹앱)** 을 실제로 빌드한다.
> 이 문서는 "superpowers를 어떻게 설치하고, 어떤 흐름·명령어를 갖고, 각 단계의 input/output이 무엇이며, 챗봇을 만들려면 어떤 콘텐츠를 준비해 어느 단계에 먹여야 하는지"를 정리한다.
> 설계 사양(무엇을 만들지)은 [`CHATBOT-DEV-GUIDE.md`](CHATBOT-DEV-GUIDE.md)가 단일 출처다. 이 문서는 **그 사양을 superpowers 위에서 어떻게 굴릴지(how)** 를 다룬다.
> 작성일: 2026-06-19.

---

## 0. 한 장 요약

```
superpowers(개발 방법론)  ───▶  결과물 = po-dev-chat 챗봇 (제품)
   /brainstorm                    Agent SDK 백엔드 + 대화 UI + validator
   → writing-plans                tool 6종 · 훅→validator 파이프라인
   → subagent-driven-development   PROJECT_ROOT 라우팅 · Gate A
   → TDD(RED-GREEN-REFACTOR)
   → code-review → finish-branch
```

핵심 구분 — **두 개의 TDD가 겹친다. 헷갈리지 말 것.**

| | 누가 | 무엇에 적용 |
|---|---|---|
| **superpowers의 TDD** | 챗봇 *코드*를 짜는 너(개발자)+Claude Code | 챗봇 자체(tool·validator·FE/BE)에 테스트 우선 |
| **하네스의 TDD(③)** | 나중에 챗봇이 만든 계약을 받는 ③ | 대상 app_repo에 테스트 우선 |

이 가이드가 다루는 건 **위쪽(superpowers)** — 챗봇이라는 *제품을* 만드는 작업이다.

---

## 1. superpowers란

코딩 에이전트용 **소프트웨어 개발 방법론 + 합성 가능한 skill 라이브러리**. 설치하면 skill이 작업 종류에 따라 **자동 발동**한다 — 기능을 설명하면 브레인스토밍·계획 skill이, 구현을 시작하면 TDD skill이, 마무리하면 리뷰 skill이 켜진다. "코드부터 짜지 않고, 먼저 무엇을 만들 건지 캐묻는다"가 철학이다.

설계 원칙: **TDD(테스트 우선) · 임기응변보다 프로세스 · 복잡도 축소(YAGNI/DRY) · 주장보다 증거(검증)**.

---

## 2. 설치

> Claude Code 기준. 다른 에이전트(Codex/Cursor/Gemini 등)는 [공식 README](https://github.com/obra/superpowers)의 플랫폼별 절차 참조.

**방법 A — Anthropic 공식 마켓플레이스(가장 간단):**

```bash
/plugin install superpowers@claude-plugins-official
```

**방법 B — superpowers 마켓플레이스(관련 플러그인까지):**

```bash
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

**설치 확인:**

- `/plugin` 목록에 `superpowers`가 active 인지 확인.
- 채팅에 `using-superpowers` 또는 skills-search로 skill이 보이는지 확인.
- 이 레포(PO-DEV-Harn)도 함께 열어 두면, superpowers가 우리 `packages/`·`docs/` 파일을 컨텍스트로 읽을 수 있다.

> 우리 자체 플러그인(`prerequisite`/`ai-web-dev`)과 superpowers는 **공존 가능**하다. 챗봇을 *짜는 동안*은 superpowers만 있으면 되고, 우리 플러그인은 나중에 ③ 단계에서 쓴다.

---

## 3. 워크플로우 (7단계)

skill은 자동 발동하지만, 무엇이 켜지는지 알면 흐름을 통제할 수 있다.

| # | skill(자동 발동) | 하는 일 | 산출 |
|---|---|---|---|
| 1 | **brainstorming** | 코드 작성 전. 러프한 아이디어를 질문으로 정제, 대안 탐색, 설계를 *읽을 수 있는 분량으로 쪼개* 검증받음 | **설계 문서**(design doc) 저장 |
| 2 | **using-git-worktrees** | 설계 승인 후. 새 브랜치에 격리 워크스페이스 생성, 프로젝트 셋업, 테스트 baseline이 깨끗한지 확인 | 작업용 worktree/브랜치 |
| 3 | **writing-plans** | 승인된 설계로. 작업을 **2~5분짜리 task**로 분해. 각 task에 정확한 파일경로·완성 코드·검증 단계 명시 | **구현 계획**(plan) |
| 4 | **subagent-driven-development** / **executing-plans** | 계획 실행. task마다 fresh 서브에이전트 디스패치 + 2단계 리뷰(사양 준수 → 코드 품질), 또는 배치 실행 + 사람 체크포인트 | task별 커밋 |
| 5 | **test-driven-development** | 구현 중. RED→GREEN→REFACTOR 강제. 실패 테스트 먼저 → 실패 확인 → 최소 구현 → 통과 확인 → 커밋. *테스트 전에 짠 코드는 삭제* | 테스트+구현 커밋 |
| 6 | **requesting-code-review** | task 사이. 계획 대비 리뷰, 심각도별 이슈 보고. **Critical은 진행 차단** | 리뷰 결과 |
| 7 | **finishing-a-development-branch** | task 완료 시. 테스트 검증 → 머지/PR/유지/폐기 선택 → worktree 정리 | 머지/PR |

보조 skill: `systematic-debugging`(4단계 근본원인), `verification-before-completion`(진짜 고쳐졌는지), `dispatching-parallel-agents`, `receiving-code-review`, `writing-skills`(새 skill 제작).

---

## 4. 명령어 레퍼런스 (input → output)

> superpowers는 skill 자동 발동이 기본이라 명령어를 **꼭 칠 필요는 없다**. 아래는 단계를 *명시적으로* 시작하고 싶을 때 쓰는 진입점이다. 정확한 명령어 노출은 버전에 따라 다를 수 있으니 `skills-search`로 확인한다.

| 명령/skill | Input (네가 주는 것) | Output (돌려받는 것) | 의미 |
|---|---|---|---|
| `/brainstorm` (brainstorming) | 만들 것의 한 줄 의도 + 참고 문서 경로 | 합의된 **설계 문서**(범위·대안·결정) | "무엇을·왜"를 코드 전에 확정 |
| `/write-plan` (writing-plans) | 승인된 설계 문서 | 2~5분 task로 쪼갠 **plan**(파일경로·코드·검증 포함) | "어떻게"를 실행 가능한 조각으로 |
| `/execute-plan` (executing-plans / subagent-driven) | plan 파일 | task별 구현·테스트·커밋, 체크포인트 | 계획을 코드로 |
| `skills-search` (tool) | 키워드("planning", "review") | 매칭되는 skill 목록 | 어떤 skill이 있는지 탐색 |
| (자동) test-driven-development | "이 task 구현해" | RED→GREEN→REFACTOR 강제 사이클 | 테스트 없는 코드 차단 |
| (자동) requesting-code-review | task 완료 | 심각도별 이슈 리포트 | Critical 차단 게이트 |

**input/output을 읽는 법(중요):** superpowers의 각 단계는 *앞 단계의 output을 다음 단계의 input으로* 받는다. brainstorming의 설계 문서가 writing-plans의 입력이고, plan이 execute의 입력이다. 그래서 **앞 단계를 대충 하면 뒤가 무너진다.** 우리 하네스의 "①→②→③ 계약 파이프라인"과 똑같은 원리다.

---

## 5. 이 챗봇 빌드를 superpowers 단계에 얹기

각 superpowers 단계의 input으로 **무엇을 넣고**, output이 **챗봇의 무엇이 되는지** 매핑한다.

### 5-1. brainstorming 단계 — 무엇을 입력하나

브레인스토밍을 시작할 때 아래를 컨텍스트로 준다(이미 이 레포에 다 있다):

- 사양 원본: [`docs/CHATBOT-DEV-GUIDE.md`](CHATBOT-DEV-GUIDE.md) — 시스템 구성·skill 포팅·훅→validator·상태머신·system prompt 조립.
- 재사용 자산: `packages/po-dev-chat/skills/` 9종, `packages/po-dev-chat/hooks/` 2종, `packages/po-dev-chat/rules/` 6종.
- 공유 검증: `packages/harness-core/lib/ds_closure.py`, `packages/harness-core/rules/`(constitution·spine-ids·ds-closure).
- 데이터 계약: `packages/po-dev-chat/rules/screen-model-schema-v2.md`, `.../data-contract-schema.md`, `.../journey-schema.md`, `skills/spec-generator/spec-pack-schema.md`.

브레인스토밍에서 **확정해야 할 결정들**(브레인스토밍이 너에게 캐물을 것들):

1. Agent SDK 언어 — TypeScript vs Python (skill 포팅·validator 호출 편의로 결정).
2. 저장 백엔드 — 초기 파일(`projects/<id>/`) vs DB/object storage.
3. 멀티테넌트 라우팅 — `PROJECT_ROOT` 주입 방식, 세션-프로젝트 매핑.
4. validator 노출 형태 — 순수 함수 라이브러리로 뽑아 tool/파이프라인에서 호출(스킵 불가).
5. 프런트 범위 — 대화 UI + `render.html` 미리보기 + Gate A 승인 버튼.

→ **output**: 위 결정이 박힌 챗봇 설계 문서.

### 5-2. writing-plans 단계 — 어떤 task로 쪼개지나

[`CHATBOT-DEV-GUIDE.md` §8 구현 순서](CHATBOT-DEV-GUIDE.md)가 그대로 plan의 task 묶음이 된다:

1. `harness-core/lib`의 validator(schema·L1~L4·sufficiency·gate-a)를 **순수 함수 라이브러리**로 확정 + 단위테스트.
2. agent tool 6종 정의 — `recommend_layout` · `render_screen` · `add_action` · `add_note` · `upsert_entity`/`upsert_external` · `generate_spec_pack`.
3. 오케스트레이션 — 훅→validator 파이프라인(patch 전 schema, patch 후 L1~L4) + 상태머신(`draft→layout_confirmed→actions_in_progress→review→confirmed`).
4. `PROJECT_ROOT` 라우팅 + `foundation/VERSION` 핀 + optimistic locking(`version`).
5. 프런트 — 대화 + 미리보기 + Gate A.
6. ③ 인계·Change Order 경로(`model_repo/specs/` 발행).

→ **output**: 각 task에 파일경로·코드·검증이 박힌 plan.

### 5-3. execute + TDD 단계 — 챗봇 코드가 나온다

superpowers의 TDD가 각 tool/validator마다 *테스트 먼저* 강제한다. 특히:

- **validator는 테스트가 쉽다**(순수 함수) → 1번 task부터 RED-GREEN으로 빠르게 green.
- **DS 폐쇄(L1) 가드레일**: "허용 밖 컴포넌트 patch → 적용 거부" 케이스를 반드시 테스트로 고정(`CHATBOT-DEV-GUIDE.md` §3·§9).
- tool은 입출력 계약(예: `add_action` → `actions[]` + Gherkin acceptance)을 테스트로 명세.

→ **output**: 테스트 green인 po-dev-chat 챗봇.

---

## 6. 빌드 전에 준비할 콘텐츠(입력 자료 체크리스트)

브레인스토밍을 켜기 전에 아래가 손에 있어야 한다. 대부분 이미 레포에 있으니 **경로만 모아 두면 된다.**

- [ ] 사양: `docs/CHATBOT-DEV-GUIDE.md` (단일 출처)
- [ ] 포팅 대상 skill 9종: `packages/po-dev-chat/skills/*/SKILL.md`
- [ ] 검증 로직: `packages/po-dev-chat/hooks/on-save-schema-validate.py`, `.../on-save-lint-L1-L4.py`, `skills/sufficiency-check/scripts/sufficiency-check.py`, `skills/gate-a-check/scripts/gate-a-check.py`, `packages/harness-core/lib/ds_closure.py`
- [ ] system prompt 재료: `packages/harness-core/rules/*` + `packages/po-dev-chat/rules/*`
- [ ] 스키마/계약: `screen-model-schema-v2.md` · `data-contract-schema.md` · `journey-schema.md` · `spec-pack-schema.md` · `question-bank.md`
- [ ] 데이터 형상 예시: `projects/example/foundation/`(읽기 대상) · `projects/example/model_repo/`(쓰기 대상 트리)
- [ ] 스택 결정 원칙: `projects/example/foundation/decisions/tech-stack.md`

> superpowers는 worktree를 따로 만든다(워크플로우 2단계). 챗봇 소스는 **새 디렉터리/repo**(예: `packages/po-dev-chat-app/` 또는 별도 repo)에 짜고, `packages/po-dev-chat/`의 SKILL·rule·validator는 **읽어서 포팅**한다 — 원본은 단일 출처로 보존.

---

## 7. 챗봇 산출물 정의(output — DoD)

superpowers plan이 끝났을 때 존재해야 하는 것([`CHATBOT-DEV-GUIDE.md` §9](CHATBOT-DEV-GUIDE.md)와 일치):

- [ ] 9개 skill 로직이 tool/validator로 포팅(경로 `PROJECT_ROOT` 기준)
- [ ] save 훅 2종이 patch 전후 validator 호출로 전환(스킵 불가)
- [ ] DS 폐쇄(L1) 실패 시 patch 미적용(가드레일) — **테스트로 고정**
- [ ] system prompt가 harness-core rules + ② schema에서 조립
- [ ] foundation 읽기 / model_repo 쓰기가 `PROJECT_ROOT` 기준, `VERSION` 핀
- [ ] optimistic locking(`version`) 동작
- [ ] PACK-* 발행이 `model_repo/specs/`에 기록, ③가 참조
- [ ] (superpowers 추가) 위 전부에 테스트가 있고 green

---

## 8. 바로 복붙하는 시작 시나리오

Claude Code에서 superpowers 설치 후, PO-DEV-Harn 레포를 열고 첫 메시지로:

```
PO-DEV-CHAT 챗봇을 만들 거야. 사양은 docs/CHATBOT-DEV-GUIDE.md에 있고,
포팅할 자산은 packages/po-dev-chat/(skills·hooks·rules)와
packages/harness-core/lib/ds_closure.py야.
바로 코드부터 짜지 말고 brainstorming으로 설계부터 같이 잡자.
먼저 결정할 것: Agent SDK 언어(TS/Python), 저장 백엔드(파일/DB),
PROJECT_ROOT 라우팅, validator를 순수함수 라이브러리로 뽑는 범위.
```

이렇게 시작하면 brainstorming skill이 자동 발동해 질문을 던진다. 설계 합의 → "go" → worktree → writing-plans → execute(TDD) 순으로 진행된다. 중간에 막히면 `skills-search`로 필요한 skill을 찾고, 버그는 `systematic-debugging`이 받는다.

---

## 9. 주의점

- **두 TDD를 섞지 말 것**(§0). 지금은 *챗봇 코드*에 대한 superpowers TDD다. 챗봇이 나중에 만드는 *계약*은 코드가 아니므로 그 자체엔 TDD가 없다(③가 구현할 때 적용).
- **단일 출처 보존**: `packages/po-dev-chat/`의 SKILL·rule·`harness-core/lib`는 *읽어서 포팅*하되 챗봇 코드에 **복붙 중복하지 말고 import/참조**. ds-closure가 lib 하나로 통합된 것과 같은 원칙.
- **가드레일은 옵션 아님**: DS 폐쇄(L1)·schema 검증은 patch 적용 전 반드시 통과. superpowers TDD로 "거부" 케이스부터 테스트.
- **superpowers는 git worktree를 만든다**: 우리 레포에서 돌리면 새 브랜치/worktree가 생긴다. `projects/example/app_repo/.git`(③ 영역)과 헷갈리지 않게, 챗봇 작업 브랜치는 챗봇 소스 디렉터리에서 관리.
- **명령어 이름은 버전에 따라 다를 수 있다**: 자동 발동이 기본이므로 명령어가 안 보여도 정상. `using-superpowers`/`skills-search`가 현재 버전의 정식 레퍼런스.

---

## 부록 A. superpowers ↔ 우리 하네스 용어 대응

| superpowers | 우리 하네스(③) | 비고 |
|---|---|---|
| brainstorming → design doc | ②의 screen model 확정 / ①의 SPEC 명세 | "코드 전에 합의" 동일 |
| writing-plans → plan | speckit `specify`/`plan`/`tasks` | task 분해 동일 |
| test-driven-development | tdd-policy + tdd-gate hook | RED-GREEN-REFACTOR 동일 |
| requesting-code-review | code-reviewer 서브에이전트 + Gate B | 심각도 게이트 동일 |
| using-git-worktrees | install-git-hooks가 거는 app_repo/.git | 격리 작업 |

→ 철학이 같으므로(테스트 우선·프로세스·증거), superpowers로 챗봇을 만든 경험은 ③ 하네스 사용에도 그대로 전이된다.

---

## 부록 B. 출처

- obra/superpowers (GitHub): https://github.com/obra/superpowers
- superpowers 마켓플레이스: https://github.com/obra/superpowers-marketplace
- 릴리스 발표글(Jesse Vincent): https://blog.fsck.com/2025/10/09/superpowers/
- 본 레포 사양: `docs/CHATBOT-DEV-GUIDE.md`, `docs/ADR-001-3runtime-architecture.md`, `docs/MIGRATION-PLAN.md`

---

## 10. 리뷰: 실현 가능성 검토 및 개선 사항 (2026-06-20)

> 이 가이드와 `CHATBOT-DEV-GUIDE.md`가 참조하는 자산을 레포 실물과 대조해 검토했다.
> **결론: superpowers로 "web app을 설계하고 기능을 확정하는 챗봇"을 만드는 것은 실현 가능하다.** 워크플로우(brainstorm→plan→TDD→review)는 이 빌드에 잘 들어맞고, 참조 자산도 모두 존재한다. 다만 가이드가 **과소평가하거나 누락한 리스크 8건**이 있고, 이를 brainstorming/writing-plans 입력에 반영하지 않으면 plan 단계에서 막힌다.

### 10-0. 검증된 사실 (자산 실재 확인)

- skill 9종(`packages/po-dev-chat/skills/*`), hook 2종, `harness-core/lib/ds_closure.py`, rules·schema(`screen-model-schema-v2.md` 등), example 데이터(`projects/example/foundation/`·`model_repo/`), `ds-allowlist.md`, `spec-pack-schema.md` 모두 **실재**한다. 포팅 대상이 비어 있지 않다 → 빌드 출발점은 견고하다.

### 10-1. 🔴 (Critical) validator는 아직 "순수 함수"가 아니다 — 최우선 작업

가이드 §3·§5-3은 검증 로직을 "100% 순수 함수로 재활용"한다고 반복하지만, 실물은 다르다. `ds_closure.py`만 진짜 import 가능한 라이브러리이고, 나머지(`on-save-schema-validate.py`·`on-save-lint-L1-L4.py`·`sufficiency-check.py`·`gate-a-check.py`)는 **CLI 스크립트**다:

- **입력**이 `sys.argv` 파일경로, **출력**이 `sys.exit()` 코드 + stderr 텍스트다. 함수 반환값(구조화된 결과)이 없다.
- **모듈 전역 가변 상태**(`ERRORS`, `L1_ERRORS`, `RESULTS` 등)에 결과를 누적한다 → 상시 가동되는 멀티세션 웹 서버에서 **요청 간 상태 오염·동시성 버그**를 일으킨다.
- **파일시스템 스캔**에 의존한다(`model_repo/screens/SCR-*.yaml` glob, `preload_label_registry`, `load_all_screen_ids`). 즉 L3 cross-screen 검증은 patch 하나가 아니라 **repo 전체 컨텍스트**를 요구한다 → §3의 `validate(patch)`는 단순화된 표현이고, validator 시그니처는 `(patch, repo_ctx)`여야 한다.
- `gate-a-check.py`는 **subprocess로 lint·sufficiency를 재실행**한다. 웹 백엔드에서 요청마다 subprocess 호출은 느리고 취약하며 "함수로 import" 모델을 깬다.

→ **개선:** writing-plans의 **Task 1을 "validator 라이브러리 추출"로 명시적 최우선 경로(critical path)로 승격**한다. 각 스크립트를 `f(content|repo_ctx) -> StructuredResult`(예: `{ok: bool, level: "L1|L2|L3|L4|schema", errors:[...], warnings:[...]}`)로 리팩터링해 로직과 argv/exit/stderr/전역상태를 분리한다. gate-a는 subprocess 대신 추출된 함수를 직접 호출. `ds_closure.py`가 이미 그 모범이다.

### 10-2. 🟠 언어 결정(TS vs Python)은 동전던지기가 아니다

모든 validator + `ds_closure.py`가 **Python**이다. Agent SDK 백엔드를 TypeScript로 잡으면 ① 검증 로직을 TS로 재포팅(= **단일 출처 원칙 위반**, 이중관리 부활) 하거나 ② Python을 out-of-process로 호출해야 한다. 가이드 §5-1은 이를 "자유 선택"으로 두지만, **Python이 단일 출처를 그대로 보존**한다는 결과를 표면화해야 한다.

→ **개선:** brainstorming 결정 1을 "결과가 있는 결정"으로 격상. **validator 경로는 Python 권장**(FE/agent를 TS로 가려면 Python 검증 사이드카를 명시).

### 10-3. 🟠 세션/상태 지속성이 웹앱 기준으로 미명세

상태머신(`draft→…→confirmed`)을 "세션 상태"라 부르지만, 웹 챗봇은 **내구성 있고 재개 가능한 멀티테넌트 세션 저장소**가 필요하다(새로고침·재접속·동시 편집). optimistic locking은 *model*에만 언급되고 **대화/세션 상태**에는 없다.

→ **개선:** brainstorming 입력에 "세션 스토어(대화 상태 위치 vs model_repo 분리)" 결정 추가. 어떤 상태가 휘발성이고 어떤 게 model_repo에 영속되는지 경계 정의.

### 10-4. 🟠 멀티테넌트 격리/인가 보안 갭

`PROJECT_ROOT` 주입이 테넌트 경계인데, 세션이 특정 `PROJECT_ROOT`에 **인가**되는 방법과 `../` **경로 탈출 방지**(다른 테넌트 침범)가 어디에도 없다. 상시 가동 웹 서비스에선 실제 위험이다.

→ **개선:** "인증 → PROJECT_ROOT 해석 → 경로 샌드박싱" 요구사항을 §6 체크리스트와 DoD에 추가.

### 10-5. 🟡 TDD가 핵심인데 테스트 전략·픽스처가 비어 있음

가이드는 "validator는 테스트가 쉽다"면서 픽스처 계획이 없다. 그런데 **`projects/example/`이 그대로 골든 픽스처**다(`model_repo/screens/*` 정상 케이스 + `foundation/ds-allowlist.md`).

→ **개선:** `projects/example`을 **테스트 코퍼스로 명명**. 필수 RED 테스트로 "허용목록 밖 컴포넌트 → L1 거부" 케이스를 고정하고, 10-1의 StructuredResult 계약을 **스냅샷 테스트**로 잠근다.

### 10-6. 🟡 도구 인벤토리: `render_screen`은 포팅이 아니라 신규 제작

가이드는 일관되게 "tool 6종"이라 하지만 표에는 `recommend_layout`·`render_screen`·`add_action`·`add_note`·`upsert_entity/external`·`build_journey`·`generate_spec_pack`가 흩어져 있어 실제 **7~8종**이다. 특히 `render_screen`(model→`render.html` 파생)은 기존 9 skill 어디에도 대응이 없는 **순수 신규 컴포넌트**다.

→ **개선:** 도구 수를 일치시키고, `render_screen`을 "포팅"이 아닌 **신규 빌드 항목**으로 분리 표기(렌더러 기술 선택을 brainstorming 결정에 추가).

### 10-7. 🟡 FE ↔ validator 피드백 루프 미정의

§3 파이프라인은 rollback/`open_question`을 만들지만, 그게 챗 UI·미리보기에 어떻게 노출되는지(인라인 에러, Gate A 버튼 활성/비활성)가 없다.

→ **개선:** 파이프라인 출력(StructuredResult) ↔ FE 에러표시 계약을 §4/§5에 한 줄 추가.

### 10-8. 🟢 문서 정확성 소소한 수정

- §6의 `question-bank.md`는 최상위가 아니라 `skills/action-interview/question-bank.md`에 있다 → 경로 명시.
- "tool 6종" 표기를 10-6에 맞춰 통일.

### 10-9. 요약 — brainstorming 전에 확정할 추가 결정 (가이드 §5-1 보강)

기존 5개(언어·저장·라우팅·validator범위·프런트범위)에 더해: **(6) validator 라이브러리 추출 방식 + StructuredResult 계약**, **(7) 세션 스토어/영속 경계**, **(8) 테넌트 인가 + 경로 샌드박싱**, **(9) `render_screen` 렌더러 선택**. 이 4개가 plan 단계의 숨은 차단요인이며, 특히 (6)이 critical path다.
