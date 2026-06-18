<!-- supporting-file: skills/layout-recommend, skills/action-interview, skills/note-intake, skills/sufficiency-check, skills/spec-generator -->
<!-- loaded-by: layout-recommend 스킬이 screen model 초안 생성 시, on-save-schema-validate.py가 검증 시 참조 -->

# Screen Model Schema v2

화면 1개 = YAML 1개 = 단일 원본(single source of truth).
6개 부분으로 구성된다.

---

## 전체 구조

```yaml
schema_version: 2

# (0) screen  — 식별 메타데이터
screen:
  id: SCR-ORDER-LIST
  name: "주문 목록"
  archetype: list           # list | detail | form | dashboard | wizard | popup
  menu: { major: ORDER, minor: LIST }
  template:
    page: DP-MAIN           # ① design page ID
    version: 2
    slots_used: [content, header-actions]
  pins:
    design_guide: v3        # 이 화면이 참조한 자산 버전 (재현성)
    ds_contract: v5
    constitution: v3
  status: draft             # draft → layout_confirmed → actions_in_progress → review → confirmed
  version: 12               # optimistic lock + Change Order 기준
  created_by: ubc
  updated_at: 2026-06-12T10:30:00Z
  permission: all           # 화면 접근 권한: all | login | {role} — action-interview 시작 전 수집
  initial_state:            # 화면 초기 진입 조건 — action-interview 시작 전 수집
    params: [orderId]       # URL/라우터에서 받는 파라미터
    default_filter: { dateRange: "last30days" }  # 필터 기본값
    preloaded_from: SCR-ORDER-LIST  # 이전 화면에서 전달받는 데이터 (없으면 omit)
    auto_query: true        # 진입 시 자동 조회 여부

# (1) layout  — 화면 구성 (design page + DS + 위치)
layout:
  - id: CMP-ORDER-LIST.filterbar
    source:
      kind: ds              # ds | page-region
      ref: FilterBar        # design-guide.md 허용 목록의 키 (밖이면 lint L1 error)
      version: "1.2"
    position:
      slot: content         # design page 슬롯명
      order: 1              # 슬롯 내 배치 순서
      area: top             # top | main | side | footer
      span: full            # full | half | third | auto
    props: { fields: [dateRange, status] }
    meta:
      label: "기간/상태 필터"
      added_by: PRM-0002    # 이 노드를 만들게 한 발화
      interactive: true     # actions 인터뷰 대상 여부

  - id: CMP-ORDER-LIST.table
    source: { kind: ds, ref: DataTable, version: "1.2" }
    position: { slot: content, order: 2, area: main, span: full }
    props: { columns: [orderNo, customer, amount, status] }
    meta: { label: "주문 테이블", added_by: PRM-0002, interactive: true }
    reactive:               # 이 컴포넌트를 갱신시키는 트리거 — action-interview 중 query 타입에서 수집
      requery_on: [CMP-ORDER-LIST.filterbar]   # 이 컴포넌트들이 변경되면 재조회
      linked_action: REQ-ORDER-LIST.filterQuery # 재조회에 사용하는 action ID

  - id: CMP-ORDER-LIST.exportBtn
    source: { kind: ds, ref: Button, version: "1.2" }
    position: { slot: header-actions, order: 1 }
    props: { label: "엑셀 내보내기", variant: secondary }
    meta: { label: "엑셀 버튼", added_by: PRM-0005, interactive: true }

# (2) actions  — 컴포넌트별 기능 (Stage 2 인터뷰 산출)
actions:
  - id: REQ-ORDER-LIST.001
    component: CMP-ORDER-LIST.exportBtn
    trigger: click          # click | submit | load | rowClick | change | schedule
    behavior: "현재 필터 조건의 주문 목록을 엑셀 파일로 다운로드"
    outcome:
      type: export          # navigate | query | mutate | export | open | validate | noop
      target: ENT-ORDER     # SCR-(이동) | ENT-(데이터) | EXT-(외부)
    type: behavior          # behavior | validation | permission | data
    permission: admin       # 역할 제한 (없으면 all). screen.permission보다 좁을 수 없음 (sufficiency L3 체크)
    error_behavior:         # 실패 케이스별 UX — action-interview Step 3에서 수집
      default: "토스트 에러 메시지 표시"
      network_fail: "재시도 버튼 표시, 3회 후 고객센터 안내"
      permission_denied: "버튼이 DOM에 없어 도달 불가"
    acceptance:             # PO↔개발자 단일 계약 (Gherkin)
      - "Given ADMIN 로그인, When 엑셀 버튼 클릭, Then 현재 필터 조건의 xlsx 다운로드"
      - "Given 일반 사용자, When 화면 진입, Then 엑셀 버튼이 보이지 않는다"
    status: user_confirmed  # proposed | user_confirmed
    provenance:
      intent: >
        관리자 전용 엑셀 다운로드. 필터 조건 반영.
        처음엔 전체 다운로드 요청이었으나 v9에서 필터 반영으로 변경.
      prompts: [PRM-0005, PRM-0009]

  - id: REQ-ORDER-LIST.002
    component: CMP-ORDER-LIST.table
    trigger: rowClick
    behavior: "주문 상세 화면으로 이동"
    outcome: { type: navigate, target: SCR-ORDER-DETAIL }
    type: behavior
    acceptance:
      - "Given 목록, When 행 클릭, Then 해당 주문의 상세 화면으로 이동"
    status: user_confirmed
    provenance: { intent: "행 클릭 → 상세 이동", prompts: [PRM-0006] }

# (3) notes  — 사용자 직접 기입 원문 (Stage 3, AI 미가공)
notes:
  - id: NOTE-ORDER-LIST.001
    scope: CMP-ORDER-LIST.table   # CMP-... | screen
    verbatim: true                # 본문은 사용자 원문 그대로 — AI 수정 금지
    body: |
      금액은 주문 시점 환율로 KRW 환산해서 보여줘야 함.
      환율 못 받아온 날은 전일자 환율 쓰고, 그것도 없으면 관리자한테 알림.
    kind: business_rule           # AI가 '제안'한 분류 (본문 불변)
    complexity: high              # high → speckit.plan 중 bl-analyst 자동 호출
    author: ubc
    at: 2026-06-12T11:02:00Z

  - id: NOTE-ORDER-LIST.002
    scope: screen
    verbatim: true
    body: "이 화면은 월말에 동시 접속이 몰림. 느려지면 안 됨."
    kind: nfr
    complexity: med
    nfr_detail:             # kind: nfr일 때 note-intake가 follow-up으로 수집
      category: performance # performance | concurrency | audit | security | availability
      concurrent_users: 500
      response_target: "2초 이내"
      priority: must        # must | should | nice-to-have

# (4) prompt_log  — 사용자 발화 원장 (append-only)
prompt_log:
  - id: PRM-0005
    at: 2026-06-12T10:41:00Z
    author: ubc
    stage: action           # layout | action | revision | note
    text: "엑셀로 전체 다운로드 받는 버튼 하나 추가해줘"
    affected: [CMP-ORDER-LIST.exportBtn, REQ-ORDER-LIST.001]
    applied_version: 8
  - id: PRM-0009
    at: 2026-06-12T11:15:00Z
    author: ubc
    stage: revision
    text: "아 엑셀은 전체 말고 지금 필터된 것만. 그리고 관리자만 보이게"
    affected: [REQ-ORDER-LIST.001]
    applied_version: 9
    supersedes: [PRM-0005]

# (5) intake  — HITL 정보 수집 상태 (Stage 4)
intake:
  open_questions:
    - id: Q-001
      target: CMP-ORDER-LIST.table
      ask: "주문이 0건일 때 무엇을 보여줄까요?"
      reason: checklist.empty_state
      status: answered       # open → answered | deferred
      answer_ref: PRM-0011
    - id: Q-002
      target: CMP-ORDER-LIST.filterbar
      ask: "기간 필터의 기본값은?"
      reason: checklist.default_value
      status: deferred
      defer_reason: "정책 미정. 개발 시 우선 '최근 7일'로 구현 후 확인"
  checklist:
    CMP-ORDER-LIST.table:    { action: ok, data_source: ok, empty_state: ok, permission: ok }
    CMP-ORDER-LIST.exportBtn:{ action: ok, data_source: ok, permission: ok, error_state: ok }
    CMP-ORDER-LIST.filterbar:{ action: ok, default_value: deferred }
  sufficiency:
    result: pass_with_deferred   # pass | pass_with_deferred | fail
    checked_at: 2026-06-12T11:30:00Z

checkpoints:
  - { name: "layout 확정", version: 7 }
  - { name: "Gate A", version: 12 }
```

---

## 필드별 규칙 요약

| 필드 | 변경 가능 | AI 수정 가능 | 해시 포함 |
|---|---|---|---|
| layout | 확정 전 | 패치 반영 | ✓ |
| layout[].reactive | 확정 전 | 인터뷰 결과 반영 | ✓ |
| screen.permission | 확정 전 | 인터뷰 결과 반영 | ✓ |
| screen.initial_state | 확정 전 | 인터뷰 결과 반영 | ✓ |
| actions.behavior | 확정 전 | 의도 반영 | ✓ |
| actions.error_behavior | 확정 전 | 인터뷰 결과 반영 | ✓ |
| actions.acceptance | 확정 전 | 초안 제안 | ✓ |
| notes.body | 확정 전 | **금지** (verbatim) | ✓ |
| notes.nfr_detail | 확정 전 | follow-up 결과 반영 | ✓ |
| prompt_log | append-only | **금지** | ✗ |
| provenance.intent | 자동 갱신 | 재생성 | ✗ |
| intake | 답변 갱신 | 질문 생성 | ✗ |

## screen.status 전환
`draft → layout_confirmed → actions_in_progress → review → confirmed`
상세: `.claude/rules/state-machine.md`
