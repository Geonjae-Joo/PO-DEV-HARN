# USER GUIDE 실전 예제 — 계산기 웹앱 만들기

> 이 문서는 [`USER-GUIDE.md`](USER-GUIDE.md)의 워크플로우를 **하나의 실제 앱**에 그대로 적용한 워크스루다. 개념·규칙은 USER-GUIDE를, 각 레이어 상세는 패키지 README를 참조한다.
>
> **만들 앱:** 사내 사용자가 로그인해서 계산을 하고, 계산 이력이 사용자별로 쌓이며, 프로필을 설정할 수 있는 계산기 웹앱.
>
> **화면 4개:**
> 1. **로그인 페이지** — 사내 SSO 로그인
> 2. **계산기** — 숫자·연산 입력, 계산, 이력 자동 기록 (메인 화면)
> 3. **프로필 설정 팝업** — 표시 이름·테마 설정
> 4. **사용 로그 페이지** — 사용자별 계산 이력 조회·기간 필터·엑셀 내보내기

---

## 이 예제에서 미리 보는 스파인 ID 지도

워크플로우를 따라가며 아래 ID들이 차례로 채번된다. 끝에서 한 줄도 빠짐없이 역추적된다.

```
①  DP-MAIN, DP-POPUP                              (design page 템플릿)
②  SCR-AUTH-LOGIN     ← DP-MAIN 인스턴스화          (로그인)
    SCR-CALC-MAIN      ← DP-MAIN 인스턴스화          (계산기)
    SCR-PROFILE-SETTINGS ← DP-POPUP 인스턴스화       (프로필 팝업)
    SCR-USAGE-LOG      ← DP-MAIN 인스턴스화          (사용 로그)
    ENT-USER, ENT-CALC-LOG                          (데이터 계약)
    EXT-SSO                                          (외부 연동 계약)
    JRN-LOGIN-CALC, JRN-VIEW-HISTORY, JRN-EDIT-PROFILE (여정)
②  PACK-CALC (계산기+로그), PACK-PROFILE (프로필)     (도메인 팩)
①  SPEC-000 (로그인/SSO/RBAC 공통기능 명세)          → ③ Phase 0가 구현
③  T001…, e2e/JRN-*, commit                         (구현·테스트·커밋)
```

> **먼저 알아둘 경계 한 가지:** 로그인은 **공통 기능**이다. 따라서 인증·세션·RBAC 로직은 PO가 계약으로 정의하는 게 아니라 ①의 **SPEC-000 명세** → ③ **Phase 0(모드 B)** 가 구현한다. PO는 로그인 *화면의 레이아웃*만 ②에서 정의한다. 이 구분이 이 예제의 핵심 학습 포인트다.

---

## 0. 등장 인물 (이 프로젝트)

| 역할 | 누가 | 무엇을 |
|---|---|---|
| 개발 리드 | 운영자 | ① DS·DP·SPEC-000·tech-stack 준비 |
| PO | 계산기 서비스 기획자 | ② 화면 4개를 screen model로 확정 |
| 개발자 | 프론트/백엔드 1명 | ③ `app_repo`에 구현 |

스택 결정(예): 백엔드 Spring Boot / 프론트 React+Vite+TS+Tailwind+shadcn/ui (`foundation/decisions/tech-stack.md`).

---

## 1. 프로젝트 시작 (1회)

```
/plugin marketplace add .
/plugin install prerequisite
/plugin install ai-web-dev

# 새 워크스페이스
projects/calculator/.claude/settings.json   ← PROJECT_ROOT + 활성 플러그인
```

이후 ①·③ 작업자는 `projects/calculator/`를 IDE로 연다.

---

## 2. ① 준비 — 개발 리드 (프로젝트당 1회)

> USER-GUIDE §2에 해당. 목표: PO가 백지에서 시작하지 않도록 틀을 못 박는다.

1. **DS 투입** — shadcn/ui 컴포넌트 + 토큰을 `foundation/design-system/ds-source/`에 저장.
2. **허용집합** — `ds-allowlist.md`에 이 앱이 쓸 컴포넌트를 등록:
   `Button, Input, Card, Table, Dialog(모달), Select, DatePicker, Avatar, Label, Separator` (+ 각 props·states).
   → 저장 시 `ds-guide-validate` 훅이 형식 검증. **이제 PO는 이 목록 밖 컴포넌트를 쓸 수 없다.**
3. **design page 생성** — `design-page-builder` 스킬로 2개 템플릿:
   - **DP-MAIN** — Header(로고·Avatar)·Breadcrumb(locked) + content(editable, 12-col grid) + Footer(locked). 로그인·계산기·로그 화면의 바탕.
   - **DP-POPUP** — 모달 컨테이너(locked: 타이틀바·닫기버튼) + body(editable). 프로필 팝업의 바탕.
4. **DS 카탈로그 렌더** — `foundation/design-system/catalog/index.html` 생성. PO가 "여기에 `Table`을, 강조색은 `color-primary-600`" 이라고 **이름으로 지시**할 근거.
5. **결정·명세 확정**
   - `decisions/tech-stack.md` (위 스택) · `ops-stack.md` (GitHub + GitHub Actions + Docker + Phoenix)
   - **`platform-baseline/SPEC-000.md`** — 공통 기능 명세: **사내 SSO 로그인 / 세션 / RBAC(일반 사용자·관리자) / 공통 레이아웃(Header의 Avatar·로그아웃)**. ← 로그인이 여기 들어간다(명세까지만, 코드는 ③).
   - `SPEC-OPS-000.md` — 배포·CI/CD·관측성 명세.
6. **빈 `app_repo` 스캐폴드** + `foundation/VERSION` 핀.

✅ DoD: ds-allowlist + DP-MAIN/DP-POPUP + 카탈로그 + SPEC-000(로그인 포함)·OPS 명세 + tech/ops-stack + VERSION.

---

## 3. ② 화면 정의 — PO (화면마다 반복)

> USER-GUIDE §3에 해당. 코드 한 줄 없이 화면 4개를 계약으로 확정한다. 각 화면은 **Stage 0 → 1 → 2 → (2.5) → 3 → 4 → Gate A** 를 거친다.

### 3-1. 로그인 페이지 — `SCR-AUTH-LOGIN`

**Stage 0 인스턴스화**: DP-MAIN 선택 → 이름 "로그인", 도메인 `AUTH`, 타입 `LOGIN` → `SCR-AUTH-LOGIN` 채번. Header/Footer 고정영역 상속, content 캔버스는 빈 상태.

**Stage 1 레이아웃**: PO가 *"가운데에 Card, 그 안에 사내 SSO 로그인 버튼 하나"* 라고 지시.
```yaml
# SCR-AUTH-LOGIN.yaml (발췌)
screen: { id: SCR-AUTH-LOGIN, name: "로그인", from_template: { page: DP-MAIN, version: 1 } }
layout:
  - { ref: Card, slot: content, position: { base: { col_start: 5, col_span: 4, row: 1 } },
      children: [ { ref: Button, id: CMP-SSO-BTN, props: { label: "사내 계정으로 로그인" } } ] }
```
저장 → schema 검증 → L1(DS폐쇄)·L5(canvas-bounds) 통과 → `render_screen` HTML 렌더 → `layout_confirmed`.

**Stage 2 액션 인터뷰**: `CMP-SSO-BTN` 클릭하면?
```yaml
actions:
  - id: REQ-AUTH-001
    trigger: { on: click, component: CMP-SSO-BTN }
    outcome: { type: navigate, target: EXT-SSO }     # 외부 SSO로 리다이렉트
    acceptance: |
      Given 비로그인 사용자가 로그인 화면에 있고
      When 사내 계정으로 로그인 버튼을 누르면
      Then 사내 SSO 인증 페이지로 이동하고, 성공 시 계산기(SCR-CALC-MAIN)로 돌아온다
```

**Stage 2.5 외부 연동 계약**: `outcome.target: EXT-SSO` 가 정의를 요구 →
```yaml
# EXT-SSO.yaml — external-intake
external: { id: EXT-SSO, name: "사내 SSO", protocol: OIDC }
auth: { flow: authorization_code, scopes: [openid, profile] }
failure: { on_timeout: "에러 토스트 + 재시도", on_denied: "로그인 화면 유지" }
```

> ⚠️ **여기서 멈춤.** 인증 성공 후의 세션·토큰·RBAC는 PO가 정의하지 **않는다** — SPEC-000 공통 기능이다. PO는 "버튼 → SSO 이동 → 성공 시 계산기로" 라는 *화면 계약*까지만. 나머지는 ③ Phase 0.

**Stage 3~4 → Gate A**: 노트 없음, 충분성 통과 → "확정해줘" → 6조건 통과 → `confirmed`.

### 3-2. 계산기 — `SCR-CALC-MAIN` (메인 화면)

**Stage 0**: DP-MAIN 인스턴스화 → `SCR-CALC-MAIN`.

**Stage 1**: *"상단에 결과 디스플레이(Input read-only), 그 아래 숫자·연산 버튼 그리드, 우측 상단에 프로필 버튼"*.
```yaml
layout:
  - { ref: Input,  id: CMP-DISPLAY, props: { readOnly: true }, position: { base: { col_start: 1, col_span: 12, row: 1 } } }
  - { ref: Button, id: CMP-KEY-7,  position: { base: { col_start: 1, col_span: 3, row: 2 } } }   # … 0-9, +,-,*,/,=,C
  - { ref: Avatar, id: CMP-PROFILE-BTN, slot: header-actions }   # 프로필 팝업 진입점
```

**Stage 2 액션 인터뷰**:
```yaml
actions:
  - id: REQ-CALC-001              # 계산 실행
    trigger: { on: click, component: CMP-KEY-EQUALS }
    outcome: { type: mutate, target: ENT-CALC-LOG }   # 계산 결과를 로그로 기록
    acceptance: |
      Given 사용자가 "12 + 3" 을 입력했고
      When = 버튼을 누르면
      Then 디스플레이에 15 가 표시되고, 그 계산(식·결과·시각)이 내 사용 로그(ENT-CALC-LOG)에 1건 추가된다
  - id: REQ-CALC-002              # 프로필 팝업 열기
    trigger: { on: click, component: CMP-PROFILE-BTN }
    outcome: { type: open_modal, target: SCR-PROFILE-SETTINGS }
```

**Stage 2.5 데이터 계약**: `mutate ENT-CALC-LOG` →
```yaml
# ENT-CALC-LOG.yaml — entity-intake (개념 계약, 물리 타입 없음)
entity: { id: ENT-CALC-LOG, name: "계산 로그" }
attributes:
  - { name: expression, meaning: "입력한 수식 원문" }
  - { name: result,     meaning: "계산 결과값" }
  - { name: created_at, meaning: "계산 시각" }
relations:
  - { to: ENT-USER, kind: belongs_to, meaning: "이 로그는 한 사용자에 귀속" }
```

**Stage 3 노트** (verbatim, AI 수정 금지):
> "사칙연산 우선순위와 괄호를 지원해야 함. `2 + 3 * 4` 는 14. 0으로 나누면 에러 표시."

→ AI가 `complexity: high` 태그 제안(수식 파싱·연산 우선순위). **이 노트가 ③ speckit-plan에서 `bl-analyst` 서브에이전트를 부른다.**

**Stage 4 → Gate A**: 충분성 통과 → `confirmed`.

### 3-3. 프로필 설정 팝업 — `SCR-PROFILE-SETTINGS`

**Stage 0**: **DP-POPUP** 인스턴스화 → `SCR-PROFILE-SETTINGS` (모달 컨테이너 고정, body 캔버스).

**Stage 1**: body에 `Input`(표시 이름) + `Select`(테마: light/dark) + `Button`(저장).

**Stage 2 / 2.5**:
```yaml
actions:
  - id: REQ-PROF-001
    trigger: { on: click, component: CMP-SAVE-BTN }
    outcome: { type: mutate, target: ENT-USER }
    acceptance: |
      Given 사용자가 표시 이름을 "민수", 테마를 dark 로 바꾸고
      When 저장을 누르면
      Then 프로필이 갱신되고 팝업이 닫히며, 다음 로그인부터 dark 테마가 적용된다
# ENT-USER.yaml
entity: { id: ENT-USER, name: "사용자" }
attributes:
  - { name: display_name, meaning: "화면에 표시될 이름" }
  - { name: theme,        meaning: "UI 테마 선호(light|dark)" }
  - { name: role,         meaning: "권한(SPEC-000 RBAC 연동 — 읽기전용)" }
```

**Gate A** → `confirmed`.

### 3-4. 사용 로그 페이지 — `SCR-USAGE-LOG`

**Stage 0**: DP-MAIN 인스턴스화 → `SCR-USAGE-LOG`.

**Stage 1**: `DatePicker`(기간 필터) + `Button`(엑셀) + `Table`(이력).

**Stage 2 액션 인터뷰**:
```yaml
actions:
  - id: REQ-USAGE-001              # 이력 조회
    trigger: { on: change, component: CMP-DATE-FILTER }
    outcome: { type: query, target: ENT-CALC-LOG }
    acceptance: |
      Given 사용자가 기간을 "이번 달" 로 선택하면
      When 테이블이 갱신되어
      Then 그 기간에 내가 한 계산만 시각 내림차순으로 보인다 (남의 로그는 안 보임 — RBAC)
  - id: REQ-USAGE-002              # 엑셀 내보내기
    trigger: { on: click, component: CMP-EXPORT-BTN }
    outcome: { type: export, target: ENT-CALC-LOG }
    acceptance: |
      Given 필터된 결과가 있을 때
      When 엑셀 버튼을 누르면
      Then 현재 보이는 행이 .xlsx 로 다운로드된다
```
`query`·`export` 모두 `ENT-CALC-LOG` 참조(이미 정의됨 — 재사용). **Gate A** → `confirmed`.

### 3-5. 여정(JRN) — 4개 화면이 모두 confirmed 된 후 (횡단)

`journey-map` 스킬이 전 화면의 navigate/open_modal action을 집계:
```yaml
JRN-LOGIN-CALC:    SCR-AUTH-LOGIN → (SSO) → SCR-CALC-MAIN → REQ-CALC-001(계산·로그)
JRN-VIEW-HISTORY:  SCR-CALC-MAIN → SCR-USAGE-LOG → REQ-USAGE-001(필터) → REQ-USAGE-002(엑셀)
JRN-EDIT-PROFILE:  SCR-CALC-MAIN → REQ-CALC-002(팝업) → SCR-PROFILE-SETTINGS → REQ-PROF-001(저장)
```
→ 고립 화면 없음. 이 3개 여정이 ③ Phase γ의 Playwright E2E 출처가 된다.

### 3-6. 발행 — PACK 분해

`spec-generator`가 confirmed 화면을 **엔티티 응집** 기준으로 도메인 팩으로 묶는다:

| PACK | 묶이는 화면 | 핵심 엔티티 | 비고 |
|---|---|---|---|
| **PACK-CALC** | SCR-CALC-MAIN + SCR-USAGE-LOG | ENT-CALC-LOG | 둘 다 계산 로그를 쓰고/읽음 → 한 팩 |
| **PACK-PROFILE** | SCR-PROFILE-SETTINGS | ENT-USER | 프로필 도메인 |
| *(로그인)* | SCR-AUTH-LOGIN | — | **팩 아님.** SPEC-000 공통기능 → ③ Phase 0 |

발행 전 `spec-pack-guard.py`가 confirmed 여부·ENT/EXT 참조 무결성·`layout_hash`/`render_hash` 핀을 검증하고 기록 → `model_repo/specs/PACK-CALC/`, `PACK-PROFILE/` 발행 → ③ 인계.

---

## 4. ③ 구현 — 개발자 (4 Phase)

> USER-GUIDE §4에 해당. `projects/calculator/app_repo/`에서 작업.

### 부트스트랩 (1회)
```bash
bash packages/plugin-ai-web-dev/hooks/install-speckit.sh   # .specify vendoring + git 훅 설치
```

### Phase 0 — Baseline (여기서 로그인이 실제로 구현된다)

SPEC-000을 받아 공통 기능별 전달 모드 결정 → `baseline-delivery-manifest.yaml`:

| 공통 기능 | 모드 | 사유 |
|---|---|---|
| SSO 로그인 / 세션 / JWT | **B (직접 주입)** | 변형 불필요 — 완성 코드+테스트로 주입. `EXT-SSO`(OIDC) 어댑터 구현 |
| RBAC (일반/관리자) | **B** | 표준 — 미들웨어·엔티티 주입 |
| 공통 레이아웃(Header Avatar·로그아웃) | **A (가이드)** | 화면마다 약간 다름 → `baseline-guides/`로 |
| 권한 조건부 렌더(로그는 본인 것만) | **A** | 도메인마다 조건이 다름 → Phase β가 로드해 적용 |

→ `SCR-AUTH-LOGIN` 화면은 Phase α에서 shell이 생기고, 그 뒤 **세션/SSO 흐름은 Phase 0(모드 B) 코드가 연결**한다. *PO 계약(REQ-AUTH-001)은 "버튼→SSO→계산기"라는 화면 흐름의 acceptance로만 쓰이고, 토큰 검증·세션은 baseline 테스트가 책임진다.*

### Phase α — Layout Scaffold (전체 화면 1회)
```
/speckit-scaffold      # SCR-AUTH-LOGIN, SCR-CALC-MAIN, SCR-PROFILE-SETTINGS, SCR-USAGE-LOG → React shell 일괄
```
`layout-hash-guard`가 4개 화면을 ②와 동일 엔진으로 재렌더 → `layout_hash` 일치 확인. 불일치 시 빌드 차단(②확정 위치를 ③이 못 바꿈). 앱을 띄우면 4개 화면이 데이터 없이 layout만으로 보인다(walking skeleton).

### Phase β — Spec Pack Iteration (팩마다)

**PACK-CALC 차례:**
```
/speckit-specify   # PACK-CALC scope 확인 (SCR-CALC-MAIN+USAGE-LOG, ENT-CALC-LOG)
/speckit-plan      # ENT-CALC-LOG → 물리 테이블(calc_log: id, user_id FK, expression, result, created_at) + 인덱스(user_id, created_at)
                   #   API: POST /calc-logs(기록), GET /calc-logs?from&to(조회), GET /calc-logs/export(xlsx)
                   #   ★ complexity:high 노트(수식 우선순위·괄호·0 나누기) → bl-analyst 호출
                   #     → decision table / 파싱 규칙 / worked examples 산출
/speckit-tasks     # T001 수식 평가기 테스트 → T002 평가기 구현 → T003 로그 기록 API 테스트 → … (test-first)
   ── Gate B: Data Model·ERD·BL(수식 평가)·Task 확정, bl 미해결 0, 개발자 approve ──
/speckit-implement # test-author가 REQ-CALC-001/USAGE-001/002 acceptance → 실패 테스트 먼저
                   #   red → green → refactor. tdd-gate·commit-spine-id 강제
                   #   commit: [PACK-CALC/T002] 수식 평가기 구현 (REQ-CALC-001)
   → code-reviewer subagent 검토
```

**PACK-PROFILE 차례:** 같은 루프로 `ENT-USER` → 물리 설계, `REQ-PROF-001` 구현. 권한 조건부 렌더는 Phase 0의 **모드 A 가이드**(`baseline-guides/`)를 로드해 "로그는 본인 것만" 필터를 적용.

### Phase γ — Integration & NFR (배포 전)
```
JRN-LOGIN-CALC    → e2e/login-calc.spec.ts      (로그인 → 계산 → 로그 1건 증가 검증)
JRN-VIEW-HISTORY  → e2e/view-history.spec.ts     (필터 → 본인 로그만 → 엑셀 다운로드)
JRN-EDIT-PROFILE  → e2e/edit-profile.spec.ts     (팝업 → dark 저장 → 재로그인 시 적용)
   commit: [E2E/JRN-LOGIN-CALC] ...
```
각 step은 화면 action의 acceptance(Gherkin)를 **재사용**(새 시나리오 발명 금지). + NFR(동시 계산 부하·0 나누기 보안) + 관측성(Phoenix 트레이싱) + 배포(ops-stack).

---

## 5. 계약이 바뀌면 — Change Order 예시

> USER-GUIDE §5에 해당.

**상황:** 개발 도중 PO가 *"계산기에 백분율(%) 버튼을 추가하고 싶다"* 고 함.

```
③ 개발자: SCR-CALC-MAIN 에 CMP-KEY-PCT 추가 요청 → diff + blast radius 계산
   - layout 변경(버튼 1개 추가) + REQ-CALC-001 acceptance 확장(% 동작) → 중대 변경
   → 판정: regenerate
② PO: 기존 Gate A 흐름으로 SCR-CALC-MAIN 재확정 (% 버튼 배치 + acceptance 추가)
   → spec-generator가 PACK-CALC 만 버전 +1 재발행 (re-pin)
③ 개발자: 새 Gate B → % 평가 테스트 추가(기존 테스트 깨짐 = TDD 백스톱) → 재구현
```

반대로 *"버튼 색만 강조색으로"* 같은 외관 변경이면 → `dismiss` 후 re-pin (재구현 없음).

핵심: **재정의는 항상 ②로 돌아간다.** ③는 판정만, 새 계약은 만들지 않는다.

---

## 6. 이 앱의 최종 추적 그래프

```
①  SPEC-000(로그인/SSO/RBAC) ───────────────→ ③ Phase 0 (모드 B 구현 + 모드 A 가이드)
    DP-MAIN, DP-POPUP
②  DP-MAIN  → SCR-AUTH-LOGIN  → REQ-AUTH-001 → EXT-SSO
            → SCR-CALC-MAIN   → REQ-CALC-001 → ENT-CALC-LOG ┐
                              → REQ-CALC-002 → (open SCR-PROFILE-SETTINGS)
            → SCR-USAGE-LOG   → REQ-USAGE-001/002 → ENT-CALC-LOG ┤→ PACK-CALC
    DP-POPUP→ SCR-PROFILE-SETTINGS → REQ-PROF-001 → ENT-USER     ─→ PACK-PROFILE
    JRN-LOGIN-CALC / JRN-VIEW-HISTORY / JRN-EDIT-PROFILE
③  PACK-CALC → spec.md → T001…(수식평가기·로그API·표·엑셀) → test → [PACK-CALC/T…] commit
    PACK-PROFILE → … → [PACK-PROFILE/T…] commit
    JRN-* → Playwright e2e → [E2E/JRN-*] commit
                                          ↓
                                    app_repo (배포)
```

로그인 화면 한 줄까지도 **SPEC-000(①) 또는 SCR-/REQ-/PACK-(②)** 에서 왔는지, 그리고 어느 task·test·commit이 그것을 구현했는지 끝까지 역추적된다. 이것이 이 하네스의 목적이다.

---

## 부록 — 이 예제가 보여주는 5가지 교훈

1. **로그인 = 공통 기능.** PO가 인증 로직을 계약하지 않는다. ①이 SPEC-000으로 명세하고 ③ Phase 0(모드 B)가 구현한다. PO는 로그인 *화면*만 ②에서 정의한다.
2. **DP 인스턴스화.** 모든 화면은 DP-MAIN/DP-POPUP에서 시작해 고정영역을 상속하고 캔버스에만 작업한다 — 백지에서 시작하지 않는다.
3. **엔티티 응집으로 팩을 자른다.** 계산기와 사용 로그는 둘 다 `ENT-CALC-LOG`를 다루므로 한 팩(PACK-CALC)으로 묶인다.
4. **복잡 노트가 bl-analyst를 부른다.** "수식 우선순위·괄호"라는 PO의 노트(complexity:high)가 ③에서 결정 테이블·worked example을 만들어 TDD의 입력이 된다.
5. **여정이 E2E가 된다.** PO가 화면을 잇는 navigate를 정의하면(JRN-*), ③는 그것을 Playwright로 *구현*만 한다 — 시나리오를 새로 짓지 않는다.
