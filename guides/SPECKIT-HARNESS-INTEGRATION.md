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
빈 템플릿 → 하니스 하드룰 7원칙 비준. **모든 speckit 명령이 읽는 권위**이며 `/speckit-analyze`가 위반을 CRITICAL로 강제한다. ①의 `01-PREREQUISITE/.claude/rules/constitution.md`와 동기화 사본(둘은 항상 일치 유지).

### B. 템플릿 — `.specify/templates/*` (4종 하니스화)
- `spec-template.md` — Pack Scope(SCR/CMP/REQ·pinned_contract), SCR별 Gherkin acceptance 원문, notes(verbatim·complexity), open_items, Clarifications.
- `plan-template.md` — tech-stack 핀, Constitution Check 게이트, Data Model/ERD/API/wiring, bl-analyst, Gate B.
- `tasks-template.md` — test-first 2계층(API+화면), 스파인 ID, decision row/전이 100%, `[SCAFFOLD]` 예외, Gate B 블록.
- `checklist-template.md` — Gate A/B·Constitution·TDD·커밋 체크리스트.

### C. 스킬 오버레이 — `.claude/skills/speckit-*/SKILL.md` (8종)
specify·clarify·plan·tasks·analyze·implement·checklist·git-commit 상단에 "🔗 Harness Integration" 섹션 추가. **원본 로직 보존**, 하니스 입력·게이트·경계만 명시.

### D. git 확장 — `.specify/extensions/git/git-config.yml`
`auto_commit.default: true` + 단계별 메시지를 `[spec-kit/<stage>]`로. `after_implement`만 off(코드 커밋은 implement 루프 담당). `init_commit_message`도 스파인 호환.

### E. 게이트 훅(기존) 보강 — `03-AI-WEB-DEV/.claude/hooks/`
이미 존재하던 `tdd-gate.py`·`commit-spine-id.py`·`manifest-sync.py`·`git-hooks.manifest.json`은 유지. 두 군데만 최소 보정:
- `commit-spine-id.py` — `[spec-kit/<stage>]` 문서 커밋 예외 추가(코드 커밋 strict 유지).
- `tdd-gate.py` — 테스트 스위트는 **구현 파일이 스테이징된 커밋에만** 실행(문서-only 커밋 오차단 방지).

### F. git hook 설치기 + 스택 중립화 (신규)
- `03-AI-WEB-DEV/.claude/hooks/install-git-hooks.sh` / `.ps1` — `.git/hooks/commit-msg`(tdd-gate+commit-spine-id) + `post-commit`(manifest-sync) 설치. 메시지가 필요한 게이트라 commit-msg 단계에 설치(idempotent·백업).
- **스택 중립화** — constitution·템플릿·스킬 오버레이에서 하드코딩됐던 "React+Vite+TS" 핀을 제거하고, 전부 "프로젝트마다 `/speckit-constitution`으로 정의(① `output/foundation/decisions/tech-stack.md`)"로 교체. `.specify/memory/constitution.md`에 §Technology Stack 슬롯 표 추가, `01-PREREQUISITE/.claude/rules/constitution.md`에 원칙 8 추가, `speckit-constitution` 스킬에 ① 오버레이 추가.

---

## 5. 기술 스택은 constitution-driven (고정 아님)

기술 스택은 하니스에 하드코딩하지 않는다. 프론트·백엔드 모두 **① PREREQUISITE에서 `/speckit-constitution`으로 정의**해 `01-PREREQUISITE/output/foundation/decisions/tech-stack.md`(SSOT)에 박고, `.specify/memory/constitution.md` §Technology Stack과 동기화한다. 문서·스킬의 "React"·"Spring Boot"는 예시일 뿐이다(constitution 원칙 8). `tdd-gate.py`는 그 핀에서 파생한 `HARNESS_TEST_CMD`(또는 자동 탐지)로 2계층 테스트를 실행한다.

## 6. 사용 전 1회 셋업

1. **`/speckit-constitution`(① PREREQUISITE)** — 하드룰 동기화 + tech-stack.md(프론트/백엔드/테스트 러너) 확정.
2. **git hook 설치(app_repo 루트)** — 게이트를 실제 강제하려면:
   - bash: `bash 03-AI-WEB-DEV/.claude/hooks/install-git-hooks.sh` (옵션 `HARNESS_TEST_CMD="…"`)
   - PowerShell: `… install-git-hooks.ps1 -HarnessTestCmd "…"`
   - 설치 위치: `.git/hooks/commit-msg`(tdd-gate+commit-spine-id, blocking) + `post-commit`(manifest-sync).
3. **SPEC-000.md 채움(① PREREQUISITE)** — 아직 비어 있다. Phase 0 baseline 공통 기능 명세 작성.
4. **constitution 동기화 규칙** — ①의 `.claude/rules/constitution.md`를 바꾸면 `.specify/memory/constitution.md`도 함께 갱신(둘 일치).
