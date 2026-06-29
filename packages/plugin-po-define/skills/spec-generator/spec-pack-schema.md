<!-- supporting-file: spec-generator (스킬 전용) -->
<!-- loaded-by: spec-generator 스킬이 PACK-* 팩 구성 시 참조 -->

# Spec Pack Schema

spec 팩은 spec-generator가 만드는 **speckit.specify의 INPUT 번들**이다.
PO가 확정한 계약 원문(screen model 추출물)을 도메인 모듈 단위로 묶어 전달한다.
speckit이 해석·생성하는 것(ERD, API 설계, task 목록, 코드)은 팩에 미리 포함하지 않는다.

> **권위 경계 (중요).** 내용의 **단일 권위는 screen model(`SCR-*.yaml`)·`ENT-`·`JRN-` 원본**이다. spec 팩은 그것들을 **묶고 참조(ref)** 하는 번들이다(scope·screens·entities·journeys). 아래 "Schema 전문"의 `actions[]`·`notes[]` 같은 본문 필드는 **선택적 비정규화(denormalized) 사본**이며, 넣을 경우 screen model 원문과 **반드시 일치(verbatim)** 해야 한다. 최소형 팩(아래 예)은 본문을 중복하지 않고 ref 만 담아도 유효하다 — 이때 `pack-to-spec.py` 가 specify 단계에서 screen model 에서 본문을 끌어와 `spec.md` 초안을 채운다. 즉 acceptance/notes 를 팩에 복사하지 않았다고 해서 specify 를 건너뛰어선 안 된다.

### 최소형(ref-only) 팩 예 — 실제 권장 형태

```yaml
id: PACK-TODO
version: 1
status: ready
description: "TODO 할 일 관리 기능 팩"
screens:    [{ id: SCR-TODO-LIST, shell_ref: null }]
requirements: [REQ-TODO-LIST.001, REQ-TODO-LIST.002, REQ-TODO-LIST.003, REQ-TODO-LIST.004]
entities:   [ENT-TODO]
journeys:   [JRN-TODO-MANAGE]
# 본문(actions/notes/acceptance)은 screen model 이 권위 — 여기 복사하지 않는다.
# pinned_contract 는 spec-pack-guard --write-pins 로 기록(구현 freeze 기준).
```

아래 "Schema 전문"은 본문을 함께 실어 보내는 **풍부형(denormalized)** 을 보여준다. 둘 다 유효하되 권위는 항상 screen model 이다.

```
spec 팩 (PO 계약 원문 번들)
    ↓ speckit.specify  — 범위 확정, 필요 시 sub-pack 분할
    ↓ speckit.plan     — Data Model, ERD, API 설계         [speckit 산출]
    ↓ speckit.tasks    — T### 태스크 목록                   [speckit 산출]
    ↓ speckit.implement — TDD 구현 (task 단위 iteration)    [speckit 산출]
```

---

## 팩 절단 기준 — 3가지 차원

### 1차: Domain Entity 응집 (가장 중요)

**같은 primary entity를 다루는 화면·기능은 하나의 팩으로 묶는다.**

speckit.plan이 Entity, Service, Repository를 도메인 전체에 대해 한 번에 설계해야 한다. "엑셀 내보내기"만 따로 팩을 만들면 OrderEntity를 모른 채 export 로직만 설계하게 된다.

```
PACK-ORDER: SCR-ORDER-LIST + SCR-ORDER-DETAIL + SCR-ORDER-CREATE
  → speckit.plan이 Order 도메인 전체(Entity·Service·API)를 한 번에 설계
  → speckit.tasks가 T001~T015 전체 생성
  → speckit.implement가 task 단위로 iteration
```

### 2차: Workflow 연결성

**navigate로 직접 이동하는 화면들은 함께 묶는다.**

```
SCR-ORDER-LIST → (rowClick) → SCR-ORDER-DETAIL → (수정 버튼) → SCR-ORDER-EDIT
→ 세 화면이 하나의 플로우 → 하나의 팩
```

navigate target이 없거나 다른 도메인으로 이동하는 지점이 팩 경계다.

### 3차: Actor 경계

같은 role이 사용하는 화면을 묶는다. Actor가 완전히 다르고 API 권한 구조도 달라지는 경우 분리 검토.

주의: 같은 화면에 admin-only 버튼이 있는 것은 분리하지 않는다. 완전히 분리된 관리 전용 화면(SCR-ADMIN-*)이 있을 때 분리 검토.

---

## 팩 크기 가드레일

| 신호 | 판단 |
|---|---|
| 화면 1개, action 2개 이하 | 너무 작음 → 같은 도메인 팩에 병합 |
| 3개 이상의 무관한 Entity 등장 | 도메인이 다름 → 분리 |
| speckit.tasks 예상 T### 15개 초과 | 너무 큼 → actor 또는 sub-도메인으로 분리 |

최종 크기 결정은 speckit.specify가 한다. 팩은 "묶음 제안"이다.

---

## 분리 예시 (production 앱 기준)

```
PACK-ORDER         SCR-ORDER-LIST, SCR-ORDER-DETAIL, SCR-ORDER-CREATE
                   (OrderEntity 기반 user 플로우 전체)

PACK-ORDER-ADMIN   SCR-ADMIN-ORDER-LIST, SCR-ADMIN-ORDER-CANCEL
                   (같은 entity지만 actor가 다르고 API 권한 구조 다름)

PACK-MEMBER        SCR-MEMBER-LIST, SCR-MEMBER-DETAIL, SCR-MEMBER-EDIT

PACK-AUTH          SCR-LOGIN, SCR-LOGOUT, SCR-PASSWORD-RESET

PACK-DASHBOARD     SCR-DASHBOARD (다른 엔티티 집계, 읽기 전용)
```

---

## 파일 위치

```
model_repo/specs/
  PACK-ORDER/
    spec-pack.yaml
    renders-ref.txt    # 관련 render HTML 경로 목록 (복사본 아님)
  PACK-ORDER-ADMIN/
    spec-pack.yaml
    renders-ref.txt
```

---

## Schema 전문

```yaml
# ─────────────────────────────────────────────
# META
# ─────────────────────────────────────────────
meta:
  id: PACK-ORDER
  title: "주문 도메인 (사용자)"
  slice_type: feature       # feature | crud | navigation | auth | nfr
  status: ready             # ready | in_progress | done
  created_at: 2026-06-12T11:30:00Z

# ─────────────────────────────────────────────
# SCREENS — 이 팩에 묶인 화면들 (복수 가능)
# screen model YAML과 render HTML의 경로를 참조한다 (복사 아님).
# Phase α에서 만들어진 shell 컴포넌트 경로도 참조 (확장자·구조는 ①의 tech-stack.md 프론트엔드 스택을 따름. 예시는 React .tsx).
# ─────────────────────────────────────────────
screens:
  - id: SCR-ORDER-LIST
    yaml_ref: "model_repo/screens/SCR-ORDER-LIST.yaml"
    render_ref: "model_repo/renders/SCR-ORDER-LIST.render.html"
    shell_ref: "app_repo/frontend/src/pages/OrderList/index.tsx"  # Phase α 산출
    pinned_contract:            # 고정 계약 스냅샷 (구현은 이 위에서만 — freeze). 소비자(speckit-specify)가 읽는 단일 키.
      version: 12
      hash: "sha256:..."          # 모델 semantic 해시 (layout·actions·notes body)
      layout_hash: "sha256:..."   # 전 브레이크포인트 resolve 좌표 + 그리드 정의의 정규형 해시 (ADR-002 §4)
      render_hash: "sha256:..."   # 렌더 HTML(rendered-at 주석 줄 제외, LF 정규화) 해시
      from_template: "DP-MAIN@v2" # 인스턴스화 출처 (DP ID@버전)
      git_ref: "abc1234"
  - id: SCR-ORDER-DETAIL
    yaml_ref: "model_repo/screens/SCR-ORDER-DETAIL.yaml"
    render_ref: "model_repo/renders/SCR-ORDER-DETAIL.render.html"
    shell_ref: "app_repo/frontend/src/pages/OrderDetail/index.tsx"
    pinned_contract:
      version: 8
      hash: "sha256:..."          # 모델 semantic 해시 (layout·actions·notes body)
      layout_hash: "sha256:..."   # 전 브레이크포인트 resolve 좌표 + 그리드 정의의 정규형 해시 (ADR-002 §4)
      render_hash: "sha256:..."   # 렌더 HTML(rendered-at 주석 줄 제외, LF 정규화) 해시
      from_template: "DP-MAIN@v2" # 인스턴스화 출처 (DP ID@버전)
      git_ref: "abc1234"

# ─────────────────────────────────────────────
# SCOPE — 이 팩에 포함된 REQ·CMP 범위
# ─────────────────────────────────────────────
scope:
  reqs:
    - REQ-ORDER-LIST.001
    - REQ-ORDER-LIST.002
    - REQ-ORDER-DETAIL.001
  components:
    - CMP-ORDER-LIST.exportBtn
    - CMP-ORDER-LIST.filterbar
    - CMP-ORDER-LIST.table
    - CMP-ORDER-DETAIL.statusBadge

# ─────────────────────────────────────────────
# ENTITIES — 이 팩이 다루는 개념 데이터 계약(ENT-) ref
# 복사 아님. model_repo/entities/ENT-*.yaml 원본 참조. ③ Phase β가 data-model·ERD로 파생.
# 수집 규칙: scope.reqs 의 action outcome.target 중 ENT- + 그 화면 owner_screens 로 역참조.
# ─────────────────────────────────────────────
entities:
  - id: ENT-ORDER
    ref: "model_repo/entities/ENT-ORDER.yaml"
    version: 1
  - id: ENT-MEMBER
    ref: "model_repo/entities/ENT-MEMBER.yaml"
    version: 1

# ─────────────────────────────────────────────
# EXTERNALS — 이 팩이 거치는 외부 연동 계약(EXT-) ref
# model_repo/externals/EXT-*.yaml 원본 참조. ③ Phase β가 어댑터로 구현.
# ─────────────────────────────────────────────
externals:
  - id: EXT-PAYMENT
    ref: "model_repo/externals/EXT-PAYMENT.yaml"
    version: 1

# ─────────────────────────────────────────────
# JOURNEYS — 이 팩의 화면을 거치는 E2E 여정(JRN-) ref
# model_repo/journeys/JRN-*.yaml 원본 참조. ③ Phase γ가 Playwright(+BDD) E2E로 구현.
# 수집 규칙: steps[].screen 이 이 팩 screens 에 1개라도 포함되는 JRN- 을 넣는다.
# ─────────────────────────────────────────────
journeys:
  - id: JRN-ORDER-REFUND
    ref: "model_repo/journeys/JRN-ORDER-REFUND.yaml"
    version: 1
    priority: high

# ─────────────────────────────────────────────
# ACTIONS — screen model actions[] 원문 추출 (scope 범위만)
# ─────────────────────────────────────────────
actions:
  - id: REQ-ORDER-LIST.001
    component: CMP-ORDER-LIST.exportBtn
    trigger: click
    behavior: "현재 필터 조건의 주문 목록을 엑셀 파일로 다운로드"
    outcome: { type: export, target: ENT-ORDER }
    permission: admin
    acceptance:
      - "Given ADMIN 로그인, When 엑셀 버튼 클릭, Then 현재 filterbar 조건의 주문 xlsx 다운로드"
      - "Given 일반 사용자, When 주문 목록 화면 진입, Then 엑셀 버튼이 DOM에 없다"
    intent: "관리자 전용 엑셀 다운로드. 필터 조건 반영."

  - id: REQ-ORDER-LIST.002
    component: CMP-ORDER-LIST.table
    trigger: rowClick
    behavior: "주문 상세 화면으로 이동"
    outcome: { type: navigate, target: SCR-ORDER-DETAIL }  # 전체 페이지 이동
    permission: all
    acceptance:
      - "Given 목록, When 행 클릭, Then 해당 주문의 상세 화면으로 이동"
    intent: "행 클릭 → 상세 이동"

  - id: REQ-ORDER-LIST.003
    component: CMP-ORDER-LIST.createBtn
    trigger: click
    behavior: "주문 생성 팝업 오픈"
    outcome:
      type: open                      # 오버레이 오픈 (navigate 와 구분)
      target: SCR-ORDER-CREATE-POPUP  # template.page: DP-POPUP 인 화면 참조
    permission: manager
    acceptance:
      - "Given 목록, When 생성 버튼 클릭, Then 주문 생성 팝업이 오버레이로 표시된다"
    intent: "팝업으로 주문 생성 폼 표시"

# ─────────────────────────────────────────────
# NOTES — screen model notes[] 원문 그대로 (verbatim)
# ─────────────────────────────────────────────
notes:
  - id: NOTE-ORDER-LIST.001
    scope: CMP-ORDER-LIST.table
    body: |
      금액은 주문 시점 환율로 KRW 환산해서 보여줘야 함.
      환율 못 받아온 날은 전일자 환율 쓰고, 그것도 없으면 관리자한테 알림.
    complexity: high
  - id: NOTE-ORDER-LIST.002
    scope: screen
    body: "이 화면은 월말에 동시 접속이 몰림. 느려지면 안 됨."
    complexity: med

# ─────────────────────────────────────────────
# OPEN ITEMS — intake.open_questions 중 deferred 항목 원문
# ─────────────────────────────────────────────
open_items:
  - id: Q-002
    target: CMP-ORDER-LIST.filterbar
    question: "기간 필터의 기본값은?"
    defer_reason: "정책 미정."
```

---

## 팩에 포함하는 것 vs 하지 않는 것

| 포함 (PO 계약 원문) | 미포함 (speckit 산출) |
|---|---|
| screens: yaml_ref + render_ref + shell_ref | Data Model, ERD |
| scope: REQ-/CMP- 범위 | API endpoint 설계 |
| entities (ENT- ref) + externals (EXT- ref) | data-model.md 물리 설계·어댑터 코드 |
| journeys (JRN- ref) | Playwright E2E 코드 |
| actions + acceptance 원문 | bl-analyst decision_table |
| notes 원문 (verbatim, complexity) | T### task 목록 |
| open_items 원문 | 테스트 코드 |
| pinned_contract (version + hash + layout_hash + render_hash + from_template + git_ref) | impl 패턴·힌트 |

---

## speckit 명�