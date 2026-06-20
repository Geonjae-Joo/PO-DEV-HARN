# TODO 앱 — 빌드 과정 상세 기록 (Build Process)

> **이 문서는 "어떻게 만들었나"의 단계별 상세 기록이다.** (요약은 [REHEARSAL-REPORT.md](REHEARSAL-REPORT.md), 판단 근거는 [DECISION-LOG.md](DECISION-LOG.md), 발견 결함은 [HARNESS-DEFECTS.md](HARNESS-DEFECTS.md).)
> PO-Dev Harness 3-레이어(① PREREQUISITE → ② PO-DEV-CHAT → ③ AI-WEB-DEV)를 TODO 도메인으로 골드패스부터 끝까지 1회 완주한 과정을, 실제 명령·게이트 출력·커밋 해시와 함께 재현 가능하게 적는다.
> 작성: 2026-06-21 · 대상: `projects/todo/`

> **표기**: 커밋 해시는 두 레포로 나뉜다 — `(mono)` = 최상위 모노레포, `(app)` = `app_repo/`의 자체 git 레포.

---

## Phase 0 — 준비/정찰 (코드 0줄)

하네스를 **읽고** 시작했다. 손대기 전에 계약 포맷·강제 장치·툴체인을 파악하는 것이 1패스 통과의 핵심이었다.

1. 구조 파악: `README.md`, `guides/PLAN-speckit-tdd-fusion.md`, `packages/`·`projects/example/` 트리.
2. **골드 템플릿 정독** — 기존 `projects/example`(PACK-ORDER)이 정답지였다: `tech-stack.md`, `SPEC-000.md`, `SCR-ORDER-LIST.yaml`, `ENT-ORDER.yaml`, `JRN-ORDER-VIEW.yaml`, `DP-MAIN.yaml`, `ds-allowlist.md`, `link-manifest.yaml`.
3. **강제 장치 정독** — `spine_ledger.py`, `gate-a-check.py`, `spec-pack-guard.py`, `on-save-schema-validate.py`, `on-save-lint-L1-L4.py`, `sufficiency-check.py`, `tdd-gate.py`, `commit-spine-id.py`, `manifest-sync.py`, `install-git-hooks.{sh,ps1}`, 규칙(constitution·tdd-policy·commit-convention·gate-b-checklist), speckit 스킬(specify·scaffold·tasks·implement).
4. **툴체인 확인**: `node v22.20 · npm 11.13 · python 3.14 · java 17 · git 2.42` → 전부 가용.

> 이 단계에서 얻은 결정적 사실: ⓐ sufficiency-check가 입력 컴포넌트엔 validation 노트, 비동기 액션엔 `error_behavior`, 테이블엔 `initial_state`를 **ERROR로 강제**한다. ⓑ tdd-gate는 `commit-msg` 훅으로 `app_repo/.git/hooks`에 설치된다(→ cwd=app_repo). ⓒ root `.gitignore`가 `app_repo/**`·`model_repo/*`를 무시 → app_repo는 자체 레포가 정석.

---

## Phase 1 — ① PREREQUISITE (foundation 준비)

`projects/todo/` 신규 생성(멀티테넌트 패턴, D-001). DS 자산(범용)은 example에서 복사 재사용.

작성한 산출물:
- `foundation/decisions/tech-stack.md` — **경량 TS 풀스택 핀**(Node+Express / React+Vite / Vitest·Supertest·Testing Library·Playwright). 근거: "간단한 TODO를 실제 실행·green까지"(D-002). constitution 원칙 8(스택은 프로젝트별 결정).
- `foundation/platform-baseline/SPEC-000.md` — 인증/RBAC **N/A**(단일 사용자, D-004), 셸·에러상태만 mode A.
- `foundation/platform-baseline/SPEC-OPS-000.md`, `decisions/ops-stack.md` — 로컬 범위.
- `foundation/design-system/ds-allowlist.md`, `design-pages/DP-MAIN·DP-POPUP.yaml`, `link-manifest.yaml`, `VERSION` — example 복사/재사용.

---

## Phase 2 — ② PO-DEV-CHAT (계약 정의)

도메인 최소화(D-003): 단일 화면·단일 엔티티·4 액션. Phase 0에서 파악한 sufficiency 제약을 **선반영**해 1패스 통과를 노렸다.

### 2.1 계약 작성
- `model_repo/entities/ENT-TODO.yaml` — `{ todoId, title, status: ACTIVE|COMPLETED, createdAt }`.
- `model_repo/screens/SCR-TODO-LIST.yaml` — 컴포넌트 4종(titleInput·addBtn·filterbar·table), 액션 4종(001 추가/002 토글/003 삭제/004 필터), 그리고 게이트 통과용 노트(검증·데이터출처·빈목록·로딩·진입·NFR) + `initial_state` + 비동기 액션 `error_behavior`.
- `model_repo/journeys/JRN-TODO-MANAGE.yaml` — 단일 화면 다단계 여정(추가→토글→필터).

### 2.2 저장 검증 체인 (cwd=projects/todo, 훅과 동일 스크립트 직접 실행)
```
schema-validate   → ✅ pass (0 warning)
lint L1–L4        → ✅ pass (0 warning)        # DS 폐쇄·완전성·일관성·커버리지
sufficiency-check → ✅ pass (error 0 / warn 0) # 노트 선반영 덕에 경고도 0
spine_ledger      → ✅ 전역 유일성 OK (15 IDs)
```

### 2.3 Gate A (6조건)
```
python gate-a-check.py model_repo/screens/SCR-TODO-LIST.yaml --pi-approved
→ ✅ lint / ✅ sufficiency / ✅ 전 action user_confirmed / ✅ open_question 0 / ✅ PO 승인 / ✅ 전역 ID 유일
→ 🎉 SCR-TODO-LIST → status: confirmed (v2)   # 스크립트가 파일을 confirmed로 재작성
```

### 2.4 발행
- 파생 렌더 `model_repo/renders/SCR-TODO-LIST.render.html` 생성(`GENERATED VIEW` 주석, constitution 원칙 1).
- `spec-pack-guard.py` → ✅ (confirmed + 참조 무결 + 여정 커버).
- **PACK-TODO 발행**: `model_repo/specs/PACK-TODO/spec.yaml`(+renders-ref.txt) — acceptance·notes 원문 보존.
- `model_repo/link-manifest.yaml` 갱신(screen confirmed v2, pack ready).

→ **(mono) `26bf910`** `[PACK-TODO] 리허설 ①②: foundation 핀 + 확정 screen model + PACK-TODO 발행`

---

## Phase 3 — ③ AI-WEB-DEV

### 3.0 Phase 0 (baseline)
`app_repo/baseline-delivery-manifest.yaml` — 전달모드 결정: **mode B 0건, mode A 2건**(FEAT-SHELL-1 셸, FEAT-ERR-1 에러상태), **N/A 11건**(인증·RBAC·감사 등).

### 3.α Phase α — scaffold (화면 shell)
- DS 허용집합 이름의 경량 컴포넌트 작성: `Button·Input·FilterBar·DataTable`.
- `pages/TodoList/index.tsx` shell(레이아웃만, 빈 핸들러, `// SCAFFOLD` 헤더) + `App.tsx`·`main.tsx`·`index.html`.
- 백엔드/프론트 `package.json`·tsconfig·vite·vitest 셋업, `npm install`(백 157pkg / 프론트 186pkg).
- **app_repo를 자체 git 레포로 init + 실제 훅 설치**(`install-git-hooks.sh`). (D-005)
- 셸만 스테이징해 커밋 → 훅 발화 확인:
  ```
  [tdd-gate] scaffold 커밋 — TDD 게이트 skip.   ← [SCAFFOLD] 마커 인식
  [commit-spine-id] PASS (scaffold)
  ```
  → **(app) `3eaabde`** `[SCAFFOLD] Phase α …`

### 3.β Phase β — TDD (RED → GREEN → REFACTOR → COMMIT)

**백엔드(API 레벨)**
1. RED: `backend/test/{todoRepo,api}.test.ts` 먼저 작성 → `npm test` 실행 → **모듈 부재로 실패**(first run the tests).
2. GREEN: `src/{todoRepo,app,server}.ts` 최소 구현 → `npm test` → **18 passed**(저장소 9 + API 9, 상태전이 ACTIVE↔COMPLETED 양방향·경계 404/400 포함).
3. COMMIT: `commit-msg` 훅이 **전체 스위트(18+6)를 실제 실행** → `tdd-gate PASS` + `commit-spine-id PASS`.
   → **(app) `c3942ee`** `[PACK-TODO/T001] 백엔드 API+저장소 (REQ-TODO-LIST.001~004)`

**프론트(화면 레벨)**
1. RED: `pages/TodoList/TodoList.test.tsx`(api 모듈 vi.mock) → 실행 → **`../../api` 부재로 실패**.
2. GREEN: `src/api.ts`(fetch 래퍼) + `TodoList` wiring(상태/이벤트, **layout 구조는 SCAFFOLD 그대로**) → **6 passed**.
3. COMMIT → **(app) `18f91b6`** `[PACK-TODO/T002] 화면 wiring + API 클라이언트`

### 게이트 강제력 음성 테스트 (나쁜 커밋을 막는가)
```
테스트 없는 구현만 스테이징 → 커밋 →  [tdd-gate] BLOCK ✅
스파인 ID 없는 메시지       → 커밋 →  [commit-spine-id] BLOCK ✅
(둘 다 원복하여 working tree 클린 유지)
```

### 3.γ Phase γ — E2E (여정 JRN-TODO-MANAGE)
- `vite.config.ts`에 `/api → :3001` 프록시 + vitest는 `src/**/*.test`만(e2e 분리).
- 백엔드(3001)·프론트(5173) 백그라운드 기동 → probe 200/200/200(프록시 포함).
- **Playwright(실브라우저)로 4스텝 여정 라이브 완주**: 빈목록 → "우유 사기" 추가(ACTIVE) → 완료 체크(COMPLETED) → 완료필터(해당만) → 미완료필터(빈목록). 증거: `docs/jrn-todo-manage-evidence.png`.
- 재현용 스펙 `frontend/e2e/jrn-todo-manage.spec.ts` 커밋 → **(app) `224c13f`** `[E2E/JRN-TODO-MANAGE] …`

### 독립 code-review (Phase β 마무리)
- 서브에이전트 독립 검토 → **APPROVE-WITH-NITS**(블로킹 0). DS 폐쇄·보안·TDD 충족·스파인 추적 전부 PASS.
- LOW 1건(화면 레벨 역토글 COMPLETED→ACTIVE 미검증) **즉시 보강** → **(app) `bf767a8`**.

### SDD 종이 흔적
- `app_repo/specs/PACK-TODO/{plan,tasks}.md`(Data Model·ERD·API 설계·test-first tasks·Gate B 충족) → **(app) `4945e90`** `[spec-kit/plan] …`

---

## Phase 4 — 하네스 결함 수정 (프로젝트 비의존적 일반화)

리허설 중 발견한 결함을 공용 `packages/`에 실제 수정하고, **HARNESS_TEST_CMD 없이 자동탐지만으로** 통과함을 검증.

- **DEF-001**(cwd 모순) + **DEF-002**(Node 백엔드 미탐지): `tdd-gate.py`에 `_app_base()`(cwd가 app_repo든 프로젝트 루트든 backend/frontend 탐지) + Node 백엔드 탐지 추가, bash 경로 forward-slash 고정. `manifest-sync.py`에 `_project_root()` + shell_ref canonical 저장.
- **OBS-004**(한글 mojibake): `install-git-hooks.{sh,ps1}` 생성 훅에 `PYTHONIOENCODING=utf-8`.
- 검증: 훅 재설치(HARNESS_TEST_CMD 없이) → 커밋 시 자동탐지로 **backend 18 + frontend 6 실행·green**, manifest-sync 정상 동기화·한글 정상. 3-cwd(프로젝트루트/app_repo/빈예제) 회귀 통과.
- 발견 당시 우회 검증 커밋(app) `edfeb7b`·`c001e53`·`33aa89d`(임시 주석 정리 포함).
- → **(mono) `02bd02c`** `fix(harness): tdd-gate·manifest-sync cwd 정규화 + Node 백엔드 자동탐지 + 훅 UTF-8`

---

## Phase 5 — 보고/머지/문서

- 리허설 산출 문서: `docs/{REHEARSAL-REPORT,DECISION-LOG,HARNESS-DEFECTS}.md` + 증거 png → **(mono) `50cad7a`**.
- **master 머지**(사용자 결정: 브랜치=truth): 안전 백업 태그(`backup/master-pre-todo-merge`) 후 `harn-todo-test` 트리를 master로 전면 채택. 머지 커밋 **(mono) `ca7290f`**(부모 `912815e`+`02bd02c`). 구 `01/02/03` 구조 → 신 `packages/projects` 구조로 대체.
- 사용자/개발 문서: `README.md`·`QUICK-START.md` → **(mono) `67b3719`**, CI 워크플로 `app_repo/.github/workflows/ci.yml` → **(app) `31bc7e8`**.

---

## 추적 그래프 (끊김 0)

```
SCR-TODO-LIST (확정 화면)
  └ CMP-TODO-LIST.{titleInput,addBtn,filterbar,table}
      └ REQ-TODO-LIST.001~004 (acceptance Gherkin)
          └ PACK-TODO (발행 팩)
              └ T001(백엔드)·T002(프론트) tasks
                  └ test (백 18 + 프론트 6 + E2E 4스텝)
                      └ commit (app: SCAFFOLD→T001→T002→E2E→plan→review-fix→CI)
```

## 재현 요약 (한 줄씩)
```
① foundation 작성(tech-stack·SPEC-000·DS)            →  계약 토대
② ENT/SCR/JRN 작성 → 검증 체인 → Gate A → PACK 발행   →  확정 계약
③ Phase0 baseline → α scaffold(+훅 설치) → β TDD(RED→GREEN→commit) → γ E2E → review
   결함 발견 시: HARNESS-DEFECTS 기록 → 안전하면 즉시 수정 → 재검증
```

## 핵심 교훈
1. **게이트를 먼저 읽으면 1패스로 통과한다** — sufficiency/lint 규칙을 계약 작성 단계에 선반영.
2. **app_repo는 자체 git 레포** — 훅이 거기서 발화한다(cwd=app_repo). 이 가정이 DEF-001을 낳았고 수정의 기준이 됐다.
3. **RED를 실제로 증명**한 뒤 GREEN — "first run the tests"가 무의미한 통과 테스트를 막는다.
4. **계약과 구현의 경계** — layout/요구사항 변경은 코드가 아니라 ②의 screen model에서(Change Order).
