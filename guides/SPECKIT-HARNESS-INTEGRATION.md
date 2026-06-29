<!-- map: spec-kit(.claude/.specify) × PO-DEV-HARN 융합 — 사용법 + 변경 내역 -->
<!-- status: v1 | date: 2026-06-15 -->

# spec-kit × 하니스 융합 — 사용법 & 변경 내역

이 문서는 `.claude`/`.specify`에 설치된 **spec-kit(v0.8.5)** 을 PO-DEV-HARN ③(AI-WEB-DEV) 요구에 맞춰
융합한 결과의 **사용 순서**와 **무엇을 바꿨는지**를 정리한다. 통합은 speckit 원본 로직을 보존하는
**이디오매틱 오버레이** 방식이다(업그레이드 안전): ① constitution 권위 ② 템플릿 ③ 스킬 오버레이
④ git 확장 + 게이트 훅.

---

## 1. 전체 명령 순서 (한 spec-pack 기준)

```
② PACK-*/spec-pack.yaml  (Gate A confirmed 계약)
        │
        ▼  model_repo/specs/ 로 인계
/speckit-specify    팩 scope 확정 → spec.md (Pack Scope·SCR/REQ·acceptance 원문)   ┐
/speckit-clarify    open_items(deferred Q-)·모호점 HITL 해소 (verbatim 노트 불변)   │ 설계
/speckit-checklist  (선택) Gate A 인계 점검 체크리스트                              │
/speckit-plan       도메인 Data Model·ERD·API·wiring  (complexity:high→bl-analyst)  │
/speckit-tasks      T### test-first 분해 (2계층·[P]·스파인 ID)                       ┘
        │
        ▼
/speckit-analyze    ★ Gate B 일관성 검사 — constitution 위반=CRITICAL, 커버리지·추적 점검
/speckit-checklist  Gate B 체크리스트 → 개발자 approve
        │  (CRITICAL=0, bl-analyst open=0, test-first 정렬 OK)
        ▼
/speckit-implement  태스크 1개씩 RED→GREEN→REFACTOR→COMMIT
        │           tdd-gate.py + commit-spine-id.py (git hook) 강제
        ▼
code-reviewer (subagent) → PR → Phase γ(통합·NFR)
        │
        └─ 계약 변경 시: Change Order(dismiss/amend/regenerate) → ② 반영 → re-pin
```

전후 단계에서 spec-kit **git 확장**이 자동 커밋한다(아래 §4).

---

## 2. spec-kit 명령 ↔ 하니스 역할

| spec-kit | 하니스 역할 | 입력 | 게이트/강제 |
|---|---|---|---|
| `/speckit-constitution` | 하드룰 동기화(① ↔ `.specify/memory`) | 01 constitution | git initialize |
| `/speckit-specify` | Phase β scope 확정 | PACK meta+scope+open_items | 새 SCR/REQ 발명 금지 |
| `/speckit-clarify` | open_items·모호점 HITL | spec-pack open_items | notes verbatim 불변, high→bl-analyst |
| `/speckit-plan` | 도메인 설계(Data Model/ERD/API/wiring) | screens+actions+notes | complexity:high→bl-analyst, layout 불변 |
| `/speckit-tasks` | T### test-first 분해 | actions+acceptance+bl | 대응 테스트 태스크 필수, 2계층 |
| `/speckit-analyze` | **Gate B 일관성 검사** | spec+plan+tasks+constitution | 위반=CRITICAL → 미해소 시 구현 금지 |
| `/speckit-checklist` | Gate A/B 체크리스트 | 위 전부 | 게이트 통과 확인 |
| `/speckit-implement` | TDD 루프 구현 | acceptance+shell_ref | tdd-gate + commit-spine-id |
| `/speckit-git-*` | 브랜치·자동 커밋(문서) | — | `[spec-kit/<stage>]` 메시지 |
| `/speckit-taskstoissues` | (선택) task→issue 동기화 | tasks.md | — |

---

## 3. "부기능" 사용법 (clarify · analyze · checklist · git)

- **clarify** — `/speckit-plan` **전에** 실행 권장. spec-pack의 `open_items`(② deferred `Q-`)와 acceptance 모호점을 최대 5문항 HITL로 좁혀 `spec.md`에 반영. ②의 verbatim 노트 본문은 절대 수정하지 않고, complexity:high 규칙은 plan의 bl-analyst로 위임. scope 밖이면 Change Order.
- **analyze** — `/speckit-tasks` **후, 구현 전**에 실행. 본 하니스에선 이게 **Gate B 일관성 검사**다. `constitution`(`.specify/memory`) 위반은 CRITICAL, REQ↔task 커버리지·test-first 정렬·스파인 추적 끊김을 함께 본다. read-only. CRITICAL=0 전 `/speckit-implement` 금지.
- **checklist** — Gate A 인계/Gate B 구현 전/TDD 충족/커밋 추적 항목을 생성(하니스판 템플릿). analyze와 함께 개발자 approve 근거로 사용.
- **git** — `initialize`(constitution 시 repo 초기화), `feature`(specify 시 브랜치), `commit`(각 단계 전후 자동 커밋). 메시지는 `[spec-kit/<stage>]`로 맞춰 `commit-spine-id` 게이트를 통과한다. **코드 구현 커밋은 git 확장이 아니라 implement 루프**가 `[PACK/T###] (REQ-)`로 만든다.

---

## 4. 변경 내역 (이번 작업)

### A. 권위 — `.specify/memory/constitution.md` (비준)
빈 템플릿 → 하니스 하드룰 7원칙 비준. **모든 speckit 명령이 읽는 권위**이며 `/speckit-analyze`가 위반을 CRITICAL로 강제한다. ①이 단일 원본으로 보유하는 `harness-core/rules/constitution.md`와 동기화 사본(둘은 항상 일치 유지).

### B. 템플릿 — `.specify/templates/*` (4종 하니스화)
- `spec-template.md` — Pack Scope(SCR/CMP/REQ·pinned_contract), SCR별 Gherkin acceptance 원문, notes(verbatim·complexity), open_items, Clarifications.
- `plan-template.md` — tech-stack 핀, Constitution Check 게이트, Data Model/ERD/API/wiring, bl-analyst, Gate B.
- `tasks-template.md` — test-first 2계층(API+화면), 스파인 ID, decision row/전이 100%, `[SCAFFOLD]` 예외, Gate B 블록.
- `checklist-template.md` — Gate A/B·Constitution·TDD·커밋 체크리스트.

### C. 스킬 오버레이 — `.claude/skills/speckit-*/SKILL.md` (8종)
specify·clarify·plan·tasks·analyze·implement·checklist·git-commit 상단에 "🔗 Harness Integration" 섹션 추가. **원본 로직 보존**, 하니스 입력·게이트·경계만 명시.

### D. git 확장 — `.specify/extensions/git/git-config.yml`
`auto_commit.default: true` + 단계별 메시지를 `[spec-kit/<stage>]`로. `after_implement`만 off(코드 커밋은 implement 루프 담당). `init_commit_message`도 스파인 호환.

### E. 게이트 훅(기존) 보강 — `packages/plugin-ai-web-dev/hooks/`
이미 존재하던 `tdd-gate.py`·`commit-spine-id.py`·`manifest-sync.py`·`git-hooks.manifest.json`은 유지. 두 군데만 최소 보정:
- `commit-spine-id.py` — `[spec-kit/<stage>]` 문서 커밋 예외 추가(코드 커밋 strict 유지).
- `tdd-gate.py` — 테스트 스위트는 **구현 파일이 스테이징된 커밋에만** 실행(문서-only 커밋 오차단 방지).

### F. git hook 설치기 + 스택 중립화 (신규)
- `packages/plugin-ai-web-dev/hooks/install-git-hooks.sh` / `.ps1` — `.git/hooks/commit-msg`(tdd-gate+commit-spine-id) + `post-commit`(manifest-sync) 설치. 메시지가 필요한 게이트라 commit-msg 단계에 설치(idempotent·백업).
- **스택 중립화** — constitution·템플릿·스킬 오버레이에서 하드코딩됐던 "React+Vite+TS" 핀을 제거하고, 전부 "프로젝트마다 `/speckit-constitution`으로 정의(① `projects/<id>/foundation/decisions/tech-stack.md`)"로 교체. `.specify/memory/constitution.md`에 §Technology Stack 슬롯 표 추가, `harness-core/rules/constitution.md`에 원칙 8 추가, `speckit-constitution` 스킬에 ① 오버레이 추가.

---

## 5. 기술 스택은 constitution-driven (고정 아님)

기술 스택은 하니스에 하드코딩하지 않는다. 프론트·백엔드 모두 **① PREREQUISITE에서 `/speckit-constitution`으로 정의**해 `projects/<id>/foundation/decisions/tech-stack.md`(SSOT)에 박고, `.specify/memory/constitution.md` §Technology Stack과 동기화한다. 문서·스킬의 "React"·"Spring Boot"는 예시일 뿐이다(constitution 원칙 8). `tdd-gate.py`는 그 핀에서 파생한 `HARNESS_TEST_CMD`(또는 자동 탐지)로 2계층 테스트를 실행한다.

## 6. 사용 전 1회 셋업

0. **speckit 부트스트랩(app_repo 루트)** — ★ 가장 먼저. speckit 명령은 app_repo 에 `.specify/` 가 있어야 동작한다(스크립트가 위로 `.specify/`를 찾음). 미설치 시 specify/plan/tasks 가 실행 불가라 v2처럼 우회가 발생한다.
   - bash: `bash "$CLAUDE_PLUGIN_ROOT/hooks/install-speckit.sh"`
   - PowerShell: `powershell -File "$env:CLAUDE_PLUGIN_ROOT\hooks\install-speckit.ps1"`
   - 동작: `.specify/` 메커니즘 vendoring + `.specify/.source`(버전 핀) 기록 + git hook 설치(2번 포함). 멱등.
   - 확인: `bash .specify/scripts/bash/check-prerequisites.sh --paths-only`
1. **`/speckit-constitution`(① PREREQUISITE)** — 하드룰 동기화 + tech-stack.md(프론트/백엔드/테스트 러너) 확정. (`.specify/memory/constitution.md` 는 ①에서 파생되는 상태)
2. **git hook 설치** — 0번이 자동 호출한다. 단독 재설치/테스트 명령 고정 시:
   - bash: `bash "$CLAUDE_PLUGIN_ROOT/hooks/install-git-hooks.sh"` (옵션 `HARNESS_TEST_CMD="…"`)
   - PowerShell: `… install-git-hooks.ps1 -HarnessTestCmd "…"`
   - 설치 위치: `.git/hooks/commit-msg`(tdd-gate + commit-spine-id + **speckit-artifact-guard**, blocking) + `post-commit`(manifest-sync).
3. **SPEC-000.md 채움(① PREREQUISITE)** — Phase 0 baseline 공통 기능 명세 작성.
4. **constitution 동기화 규칙** — 권위는 ①(`harness-core/rules/constitution.md`). `.specify/memory/constitution.md` 는 `/speckit-constitution` 이 동기화하는 **파생 상태**(손으로 양쪽 유지 금지).
5. **플러그인 업그레이드 시** — `speckit-sync.sh/.ps1` 로 메커니즘만 재동기화(상태 보존). git hook 본문이 바뀌었으면 `install-git-hooks` 재실행.

---

## 7. 메커니즘/상태 경계 & 레이어 경계 (왜 이렇게 두는가)

**메커니즘 vs 상태 (`.specify/` 내부).** speckit `.specify/` 는 성격이 다른 둘을 한 폴더에 담는다. 충돌을 피하려면 소유권을 분리한다.

| 구역 | 내용 | 소유 | 업그레이드 |
|---|---|---|---|
| 메커니즘 | `scripts/`·`templates/`(core)·`workflows/`·`extensions/*/scripts·commands` | 플러그인 단일 원본 | `speckit-sync` 재복사 |
| 상태 | `memory/constitution.md`·`feature.json`·`templates/overrides/`·`extensions/git/git-config.yml` | app_repo | sync 가 보존 |

스킬/훅(`skills/speckit-*`, `hooks/*`)은 **메커니즘**이라 플러그인에 그대로 두고 실행 시 작업 repo 의 `.specify/`·`.git/hooks` 를 읽는다. 프로젝트로 인스턴스화되는 건 `.specify/` 뿐이다.

**레이어 경계 (model_repo vs app_repo).**

| model_repo (②·권위·동결) | → 파생 → | app_repo (③·구현·재생성 가능) |
|---|---|---|
| `ENT-*.yaml` (개념 데이터 계약) | | `data-model.md`·ERD·DB 스키마 |
| `JRN-*.yaml` (개념 여정) | | Playwright E2E 코드 |
| `SCR-*.yaml`·`spec-pack.yaml` (계약 원문) | | `spec.md`·`plan.md`·`tasks.md` |

- **`ENT-`/`JRN-` 가 data-model/E2E 와 "중복"?** 아니다 — 권위(개념 계약)와 파생(물리 구현)의 양 끝이다. 분리해야 ① 구현이 합의에서 벗어났는지 감지하고 ② ENT- 변경=Change Order(②로 환류), data-model 변경=③ 재량으로 다르게 다룬다. ENT- 에 인덱스·SQL 등 물리 결정이 새면 그때부터 진짜 중복 — 그 선을 지킨다.
- **speckit 산출물은 왜 app_repo?** 생애주기가 코드와 결합(tasks.md ↔ T### 커밋·tdd-gate·PR), 권위 repo 오염 방지, 파생 방향(model→app), `pinned_contract` 로 재생성 가능. `spec-pack.yaml`(model_repo, 권위)과 `spec.md`(app_repo, 파생)는 **다른 물건**이다.
