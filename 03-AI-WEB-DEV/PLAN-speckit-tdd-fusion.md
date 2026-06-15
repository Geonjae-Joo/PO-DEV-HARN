<!-- plan: 03-AI-WEB-DEV — speckit × TDD 융합 하니스 워크플로 설계 -->
<!-- status: draft v1 | author: harness-planning | date: 2026-06-15 -->

# ③ AI-WEB-DEV — speckit × TDD 융합 하니스 워크플로 (설계 계획)

> 목표: ②(PO-DEV-CHAT)가 발행한 **spec-pack(PO 계약 원문)** 을 입력으로,
> **spec-kit의 SDD 4단계(specify→plan→tasks→implement)** 와 **TDD(red→green→refactor)** 를
> 하나의 강제된(enforced) 하니스 워크플로로 융합한다.
> 핵심 산물은 문서가 아니라 **재현 가능한 실행 파이프라인**이다.

---

## 0. 이 계획서의 위치

- **입력 계약**: `02-PO-DEV-CHAT` → `PACK-*/spec.yaml` (screen model 추출물, 코드 없음)
- **상위 규범**: `01-PREREQUISITE`의 constitution(불변 룰) · design-system · platform-baseline(SPEC-000) · tech-stack
- **이 레이어의 책임**: 계약의 *구현*. spec-kit이 ERD·API·task·코드를 생성하고, TDD가 그 코드의 정당성을 기계적으로 보증한다.
- 본 문서는 `03-AI-WEB-DEV`의 **설계 계획(plan)** 이며, 확정 시 아래 §6의 산출물로 분해되어 자체적으로 SDD+TDD로 구축된다.

---

## 1. 레퍼런스 조사 결과 (speckit에서 TDD를 하는 방법)

조사한 1차 자료와, 본 하니스에 채택할 결론을 정리한다.

### 1.1 공식 spec-kit — TDD는 *기본 내장*

- 워크플로는 **Spec → Plan → Tasks → Implement**, 각 단계 사이에 **review gate**(approve/reject)가 있다. 이는 본 저장소의 `.specify/workflows/speckit/workflow.yml`에 그대로 존재한다(`review-spec`, `review-plan` 게이트).
- `/tasks` 단계에서 **테스트 항목이 구현 항목보다 먼저 정렬**된다. 목적은 "약속한 것(requirement) → 전달한 것(code)"의 추적성. 태스크는 user story 단위로 묶이고, 독립 태스크에 `[P]` 병렬 마커, 정확한 파일 경로를 붙인다.
- 테스트는 표준 템플릿에선 *옵션*(요청 시)이지만, **본 하니스는 TDD를 하드 룰로 승격**한다(아래 1.5).
- 채택: 4단계 + 단계 간 게이트 + test-first 정렬 + `[P]` 마커 + 스파인 ID 추적. (이미 `commands/speckit.{specify,plan,tasks}.md`에 반영됨)

### 1.2 Kent Beck TDD 통합 (spec-kit PR #1172)

spec-kit에 Kent Beck TDD를 융합한 대표 레퍼런스. (논의 대기로 미머지지만 패턴이 가장 구체적)

- **`/speckit.go`** — *한 개의 task* 에 대해 엄격한 **RED → GREEN → REFACTOR → COMMIT** 사이클을 돈다. `/speckit.implement`(전체 자동 실행)와 달리 **개발자 통제(태스크 1개씩)** 가 핵심.
- **AI 경고신호 자동 감지** — ① 반복 루프(loops) ② 과도한 일반화(over-engineering) ③ **테스트 약화/조작(test cheating)**. AI가 통과시키려고 테스트를 무력화하는 것을 잡아낸다.
- **Tidy First 커밋 규율** — *구조적 변경(structural)* 과 *행위 변경(behavioral)* 을 **분리 커밋**한다.
- **CLAUDE.md(HOW) ↔ constitution.md(WHAT) 분리** — constitution은 *무엇을 만드는가*(불변 룰), CLAUDE.md는 *어떻게 만드는가*(TDD 방법론·기술스택·컨벤션). CLAUDE.md는 constitution+plan에서 자동 채움.
- 기대치: **80%+ 커버리지**.
- 채택: `/speckit.go`식 **태스크 단위 RED→GREEN→REFACTOR→COMMIT 루프**, **test-cheating 감지**, **Tidy First 분리 커밋**, **HOW/WHAT 문서 분리**.

### 1.3 ashebanow의 운영 노하우 (PR #1172 코멘트)

- TDD 규칙을 **constitution에 명시**하면 코딩 에이전트가 *행위(behavior)* 에 집중한다.
- plan이 각 phase를 "**먼저 통과해야 할 테스트 집합 → 그 다음 그것을 통과시키는 코드 태스크**" 순으로 명세하게 한다.
- spec-kit의 **contracts 메커니즘** 을 phase별 계약 정의로 쓰고 implement에서 그 계약을 강제하면 별도 TDD 장치를 상당 부분 대체할 수 있다.
- 채택: constitution에 TDD 하드 룰 박제 + plan의 phase별 "tests-first then code" + **acceptance(Gherkin)를 phase contract로 사용**.

### 1.4 Red/Green TDD 에이전트 패턴 (Simon Willison)

- "red/green TDD" = 테스트 먼저 작성 → **반드시 실패(red) 확인** → 통과하도록 구현(green).
- 실패 확인을 건너뛰면, 이미 통과하는 무의미한 테스트를 만들 위험. → 다음 장 "**First run the tests**"(구현 전 테스트 실행으로 red 확인)가 핵심 규율.
- 채택: test-author가 작성 직후 **red를 기계적으로 증명**(테스트 러너 실행 → 실패 로그 첨부)하지 않으면 green 단계로 진입 불가.

### 1.5 본 하니스의 결론 (레퍼런스 → 우리 규칙)

| 레퍼런스 패턴 | 본 하니스 적용 |
|---|---|
| specify→plan→tasks→implement + 게이트 | 유지. plan/tasks 앞 Gate B, implement 뒤 code-reviewer/Gate γ |
| tests-first 정렬, `[P]`, 스파인 추적 | `speckit.tasks`에 이미 반영. acceptance/REQ-/T### 연결 |
| `/speckit.go` 태스크 단위 RGRC 루프 | **`speckit.implement`의 내부 루프로 채택**(아직 미작성 — §4 G1) |
| test-cheating·loop·over-eng 감지 | `tdd-gate.py` + code-reviewer 검토 항목으로 강제(미작성 — §4 G2) |
| Tidy First 분리 커밋 | 커밋 prefix 규약으로 강제(§5.4) |
| CLAUDE.md(HOW) ↔ constitution(WHAT) | constitution 비준 + 루트/레이어 CLAUDE.md 작성(§4 G3·G4) |
| red 확인("first run the tests") | test-author 산출에 **실패 로그 증빙 필수**(§5.2) |
| 80%+ 커버리지 + 결정표·전이 100% | 커버리지 게이트 정의(§4 G7) |

> 본 하니스는 spec-kit *기본 TDD*(옵션) 대비 한 단계 강하다: **테스트 없는 구현을 커밋 레벨에서 물리적으로 차단**하고, **decision table의 모든 row와 state machine의 모든 전이를 최소 1 테스트로 커버**한다(`rules/tdd-policy.md`).

---

## 2. 지금 가진 자산 (이미 융합된 부분)

`03-AI-WEB-DEV`는 이미 융합 골격을 갖고 있다.

- **PACK ↔ speckit 매핑** (`spec-generator/spec-pack-schema.md`)
  - `specify` ← meta+scope+open_items / `plan` ← screens(yaml_ref)+actions+notes(complexity) / `tasks` ← actions+acceptance+bl-analyst / `implement` ← acceptance+screens(shell_ref+render_ref)
- **TDD 정책** (`rules/tdd-policy.md`) — 3겹 루프, 테스트 없는 구현 금지, **API+화면 2계층**, decision row·state 전이 전수 커버, `[SCAFFOLD]` 예외, Change Order 백스톱
- **subagents** — `bl-analyst`(complexity:high → decision table/state machine/worked examples), `test-author`(RED, 2계층 실패 테스트), `code-reviewer`(DS·보안·TDD충족·스파인ID 독립검토), `spec-generator`(regenerate 시 팩 재생성)
- **게이트** — `Gate B`(implement 전, 개발자 소유, BL open decision 0 + test-first task 확정), Change Order(pin→freeze→발행→판정→TDD 백스톱)

이 골격은 §1 레퍼런스와 정합한다. 빠진 것은 "**실행부와 강제 장치**"다.

---

## 3. 목표 파이프라인 (Phase 0 → α → β → γ)

```
[① PREREQUISITE]  constitution(불변 룰·TDD 하드룰5) · design-system · SPEC-000 · tech-stack
        │  (Phase 0) speckit.specify: SPEC-000 공통기능 A/B 전달모드 결정 → baseline-delivery-manifest
        ▼
[Phase α] scaffold  app_repo 골격 + 화면 shell(shell_ref) 생성   ← 테스트 면제 [SCAFFOLD]
        │
        ▼
[② PO-DEV-CHAT] ──PACK-*/spec.yaml──►  (계약 원문, 코드 없음, pinned_contract)
        │
        ▼
[Phase β] 팩 단위 반복:
   speckit.specify   범위 확정 / sub-pack 분할 / deferred 처리
        ▼
   speckit.plan      Data Model·ERD·API·frontend wiring  + (complexity:high→bl-analyst)
        ▼   ── review-plan gate
   speckit.tasks     T### test-first 정렬 + [P] + 스파인 연결
        ▼
   ▣ Gate B (개발자 소유)  Data Model/ERD/API 확정 · BL open=0 · test-first task · approve
        ▼
   speckit.implement  ◄── 본 계획의 핵심. 태스크 1개씩 TDD 루프 (▶ §5)
        │   for each T###:  RED → GREEN → REFACTOR → COMMIT   (tdd-gate.py 강제)
        ▼
   code-reviewer      DS·보안·TDD충족·스파인ID 독립 검토 → approve / 수정요청
        ▼
   (Change Order 발생 시) pin→freeze→발행→dismiss|amend|regenerate→re-pin
        ▼
[Phase γ] 통합 검토 / 전역 code-reviewer / 커버리지·보안 종합
```

---

## 4. 갭 분석 — 융합을 "강제"로 만들기 위해 채워야 할 것

현 저장소 점검 결과 발견한 **빠진 조각**(우선순위 순).

### G1. `/speckit.implement` 명령이 없다 🔴 (최우선)
`commands/`에는 `specify·plan·tasks`만 있고 **implement가 없다**. 정작 red→green→refactor가 도는 실행부가 미정의. 본 융합의 심장.
→ **산출물 D1**: `commands/speckit.implement.md` — 태스크 단위 RGRC 루프(§5).

### G2. `tdd-gate.py` hook이 없다 🔴
`tdd-policy.md`·`code-reviewer`가 `tdd-gate.py`를 전제하지만 `03-AI-WEB-DEV/hooks/` 폴더 자체가 없다. **테스트 없는 구현을 막는 강제 장치 부재** → 정책이 선언으로만 존재.
→ **산출물 D2**: `hooks/tdd-gate.py` + `hooks/hooks.json`(PreToolUse/commit 시점).

### G3. constitution.md가 기본 템플릿이다 🔴
`.specify/memory/constitution.md`는 플레이스홀더. tdd-policy가 인용하는 "**하드 룰 5번(TDD)**"이 실재하지 않는다. CLAUDE.md(루트)도 spec-kit 스텁.
→ **산출물 D3**: constitution 비준(특히 *Test-First NON-NEGOTIABLE* 원칙 명문화) + 버전/비준일 기록.

### G4. 루트/레이어 CLAUDE.md(=HOW)가 없다 🟡
PR #1172의 핵심: *WHAT(constitution)* 과 *HOW(CLAUDE.md: TDD 방법론·테스트 러너·커밋 규약·AI 경고신호)* 분리.
→ **산출물 D4**: `03-AI-WEB-DEV/CLAUDE.md`(또는 루트 CLAUDE.md 확장) — 구현 에이전트가 따르는 TDD HOW. constitution+plan에서 채움.

### G5. Phase α scaffold 명령이 없다 🟡
`shell_ref`(Phase α 산출)와 `[SCAFFOLD]` 예외는 곳곳에서 참조되나, scaffold를 만드는 명령/스킬이 없다.
→ **산출물 D5**: `commands/speckit.scaffold.md`(또는 PREREQUISITE 연계) — app_repo 골격 + 화면 shell 생성, `[SCAFFOLD]` 커밋.

### G6. tech-stack / 테스트 툴링이 미고정 🟡
`spec-pack-schema`가 참조하는 `①의 tech-stack.md`가 없고 `SPEC-000.md`는 비어 있다. **테스트 러너·E2E 도구가 안 정해지면** test-author가 무엇으로 실패 테스트를 쓸지 모른다.
→ 사용자 결정에 따름: **프레임워크는 PREREQUISITE에서 고정**, 나머지(테스트 러너 등)는 **plan에서 결정**. 본 계획은 §7에 *권고안*(예: 2계층 = API: 백엔드 통합테스트 / 화면: 컴포넌트+E2E)을 제시하되, 확정은 `01-PREREQUISITE/.../tech-stack.md`(D6)에 박제.

### G7. 커버리지·AI 경고신호 게이트가 수치/규칙으로 미정의 🟢
"80%+", "decision row 100%", "test-cheating 차단"이 정책 문장엔 있으나 **측정·차단 지점**이 없다.
→ **산출물 D7**: code-reviewer 검토 항목 + tdd-gate에 **임계치·감지 규칙** 명시(§5.5).

---

## 5. `speckit.implement` 내부 — RED→GREEN→REFACTOR→COMMIT (설계 상세)

본 융합의 핵심. `/speckit.go`(PR #1172) + 본 하니스의 2계층 테스트·스파인 추적을 결합한다.
**한 번에 태스크 1개**(`[P]`여도 검증은 개별), 사람이 사이클을 통제한다.

### 5.1 전제 (진입 조건)
- Gate B approve 완료 (BL open decision = 0, test-first task 확정).
- 대상 `T###`에 연결된 `REQ-/CMP-`, acceptance(Gherkin), bl-analyst worked examples 로드.
- 작업은 pinned_contract(version·hash·git_ref) 스냅샷 위에서만(Change Order freeze 존중).

### 5.2 RED — 실패 테스트 먼저 (test-author subagent)
- test-author가 **2계층** 테스트를 작성:
  - **API 레벨** — endpoint 요청/응답·권한·경계·에러 케이스.
  - **화면 레벨** — 컴포넌트 동작·상태 전이·권한 조건부 렌더.
- 커버리지 규칙: **각 Gherkin 시나리오 ≥1 테스트**, **decision table의 모든 row ≥1**, **state machine의 모든 전이 ≥1**.
- **red 증명(필수)** — 작성 직후 테스트 러너를 실행해 **실패 로그를 산출물에 첨부**. 처음부터 통과하면 무효 → 테스트 재작성. (Simon Willison "first run the tests")
- 경계: 테스트만 작성, 구현 코드 금지. acceptance에 없는 동작 임의 테스트 금지.

### 5.3 GREEN — 최소 구현
- 테스트를 통과시키는 **최소 코드만**. 과도한 일반화 금지(AI 경고신호 §5.5).
- 백엔드(Entity→Service→Controller) → 프론트 wiring(`shell_ref` 컴포넌트에 API hook·상태·권한 렌더) 순. layout은 건드리지 않음(②의 계약).
- 러너 green 확인 → 로그 첨부.

### 5.4 REFACTOR + COMMIT — Tidy First 분리 커밋
- green 유지하며 중복·복잡도 제거.
- **구조 변경과 행위 변경을 분리 커밋**:
  - 행위(테스트 통과 코드): `feat(T###): ...  [REQ-...]`
  - 구조(리네이밍·추출, 행위 불변): `refactor(T###): ...`
  - scaffold: `[SCAFFOLD] ...`(테스트 면제) / Change Order: `[CO/<dismiss|amend|regenerate>] ...`
- 모든 커밋 메시지에 **스파인 ID(T###/REQ-)** 포함(code-reviewer 추적 검증).

### 5.5 강제·감지 (tdd-gate.py + code-reviewer)
- **차단(commit hook)**: 구현 변경에 대응하는 테스트가 없거나 red/실패 상태면 commit 거부. `[SCAFFOLD]`만 예외.
- **AI 경고신호 감지** → 차단 또는 리뷰 플래그:
  - *test-cheating* — 테스트의 단언 약화/삭제, `skip`/`xfail` 남용, 구현에 맞춰 기대값을 사후 수정.
  - *loop* — 동일 변경 반복.
  - *over-engineering* — acceptance·worked example 범위를 넘는 추상화/옵션.
- **커버리지 게이트** — 팩 단위 라인 커버리지 ≥ 임계치(권고 80%) + decision row/state 전이 100%. 미달 시 code-reviewer 수정요청.
- 보안·TDD 위반은 code-reviewer가 **merge 차단 사유**로 분류.

### 5.6 Change Order 백스톱
- 구현 중 계약 변경: acceptance 변경이면 **기존 테스트가 깨지는 것이 정상 신호** → `amend`/`regenerate` 판정. REQ 추가만이면 additive(새 테스트·태스크). 자동 재생성 금지, 영향은 해당 팩으로 한정.

---

## 6. 구축 계획 (산출물 · 순서 · 자체 TDD)

이 하니스 자체도 SDD+TDD로 만든다. **테스트(=하니스 동작 검증 스크립트/픽스처) 먼저, 그 다음 산출물.**

| ID | 산출물 | 의존 | 검증(이 산출물의 "acceptance") |
|---|---|---|---|
| **D3** | constitution 비준(TDD 하드룰5 포함) | — | 하드룰 5개 명문화, 버전/비준일 기입, tdd-policy가 인용하는 "5번" 실재 |
| **D6** | `01/.../tech-stack.md` + SPEC-000 채움 (프레임워크·테스트 러너) | D3 | 프론트/백 프레임워크·2계층 테스트 도구 명시, shell 확장자 결정 |
| **D2** | `hooks/tdd-gate.py` + `hooks.json` | D3 | 테스트 없는 더미 커밋 → 거부됨 / `[SCAFFOLD]` → 통과 (픽스처로 검증) |
| **D1** | `commands/speckit.implement.md` (RGRC 루프 §5) | D2,D6 | 샘플 T###에서 RED 실패로그→GREEN→REFACTOR→분리커밋 흐름 재현 |
| **D5** | `commands/speckit.scaffold.md` (Phase α) | D6 | app_repo 골격 + shell_ref 생성, `[SCAFFOLD]` 커밋, tdd-gate 예외 통과 |
| **D4** | `03/CLAUDE.md` (HOW: TDD 방법론·러너·커밋규약·경고신호) | D1,D3 | constitution+plan 참조로 채워짐, 구현 에이전트가 §5 그대로 수행 |
| **D7** | 커버리지·경고신호 임계치 명문화 (tdd-gate + code-reviewer 갱신) | D2 | 80%/row100%/전이100% 측정 지점, test-cheating 감지 규칙 |
| **D8** | 엔드투엔드 리허설: 샘플 `PACK-ORDER`로 specify→implement 1회 완주 | 위 전부 | Gate B→구현→code-reviewer→green, 스파인 추적 끊김 0 |

**권장 순서**: D3 → D6 → D2 → D1 → D5 → D4 → D7 → D8.
(규범·도구 고정 → 강제장치 → 실행부 → scaffold → HOW문서 → 게이트 수치 → 리허설)

---

## 7. tech-stack / 테스트 툴링 권고안 (확정은 PREREQUISITE)

사용자 결정: **프레임워크는 PREREQUISITE에서 고정**, 나머지는 **plan에서 결정**. 아래는 *권고*일 뿐 D6에서 확정.

- **2계층 테스트 도구 분리**가 핵심(tdd-policy의 "API+화면").
  - *API 레벨*: 백엔드 통합/계약 테스트(요청·응답·권한·에러).
  - *화면 레벨*: 컴포넌트 테스트(상태·조건부 렌더) + 핵심 플로우 E2E.
- shell_ref 예시가 `*.tsx`(React)인 점으로 보아 프론트는 React 계열을 전제로 하나, **확정은 SPEC-000/tech-stack.md**에 박제하고 모든 산출물이 그 핀을 참조하게 한다(재현성).
- 커버리지 측정 도구는 라인 커버리지 + 결정표/전이 매핑을 리포트할 수 있어야 함(스파인 ID ↔ 테스트 추적).

---

## 8. 리스크 & 검증

- **R1 강제장치 공백**: tdd-gate 미구현 동안 TDD는 권고에 그친다 → D2를 D1보다 먼저.
- **R2 테스트 도구 미정**: test-author가 산출물을 못 낸다 → D6 선행 필수.
- **R3 over-spec(과설계)**: 하니스 문서만 늘고 실행 안 됨 → D8 리허설을 완료 기준(DoD)으로.
- **R4 ②/③ 경계 침범**: implement가 layout/계약을 바꾸면 안 됨 → Change Order로만, code-reviewer가 blast radius 검증.
- **검증 게이트**: 각 산출물은 위 표의 acceptance를 통과해야 "done". 최종 DoD는 **D8 엔드투엔드 리허설 green + 스파인 추적 무결**.

---

## 참고 자료 (Sources)

- GitHub Spec Kit (공식): https://github.com/github/spec-kit · 문서 https://github.github.com/spec-kit/ · 방법론 https://github.com/github/spec-kit/blob/main/spec-driven.md
- Kent Beck TDD 통합 PR #1172: https://github.com/github/spec-kit/pull/1172 (`/speckit.init-tdd`, `/speckit.go` RED→GREEN→REFACTOR, Tidy First, AI 경고신호, CLAUDE.md↔constitution 분리)
- Spec-with-TDD 포크: https://github.com/UtakataKyosui/spec-kit-with-tdd-
- Red/green TDD 에이전트 패턴 (Simon Willison): https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/ · "First run the tests" https://simonwillison.net/guides/agentic-engineering-patterns/first-run-the-tests/
- 본 저장소 내부: `03-AI-WEB-DEV/rules/tdd-policy.md`, `commands/speckit.{specify,plan,tasks}.md`, `subagents/{test-author,bl-analyst,code-reviewer,spec-generator}.md`, `02-PO-DEV-CHAT/skills/spec-generator/spec-pack-schema.md`, `.specify/workflows/speckit/workflow.yml`
