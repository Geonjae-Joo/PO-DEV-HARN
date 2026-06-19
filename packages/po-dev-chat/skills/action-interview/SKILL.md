---
name: action-interview
description: >
  Stage 2 스킬. layout_confirmed 이후 interactive 컴포넌트를 하나씩 순회하며
  action·trigger·behavior·acceptance criteria를 인터뷰하고 구조화한다.
  PO가 "이 버튼은 뭐 해요?", "동작 정의", "기능 정의"를 언급하거나
  status가 layout_confirmed인 화면이 있을 때 사용.
when_to_use: action 인터뷰, 버튼·입력·링크 동작 정의, Gherkin acceptance 작성 요청 시.
allowed-tools: Read Write Edit
layer: 02-PO-DEV-CHAT
stage: Stage 2
version: 1.0.0
owner: PO (도메인 전문가)
tags: [action, interview, gherkin, acceptance, requirement]
supporting-files: [question-bank.md]
spine-ids: [REQ-, CMP-]
---

# Skill: action-interview

## 역할

Stage 2 담당. layout이 `layout_confirmed` 상태가 된 후, `meta.interactive: true`인 컴포넌트를
**하나씩 순회하며 action을 인터뷰**한다.
사용자의 자연어 답변 → `actions[]` 구조화 + Gherkin acceptance 초안.

---

## 실행 순서

### Phase 0. 화면 레벨 질문 (컴포넌트 루프 시작 전 — 1회만)

`screen.permission`·`screen.initial_state`가 이미 채워진 경우 건너뜀.

```
AI: "컴포넌트 동작을 정의하기 전에 화면 전체에 대해 먼저 확인할게요."

Q-SCREEN-PERM:
  이 화면은 누구나 들어올 수 있나요, 아니면 특정 사용자만 볼 수 있나요?
  (예: 누구나 / 로그인 필수 / 관리자만 / 특정 팀원만)
  → screen.permission 저장

Q-INIT-STATE:
  이 화면에 처음 들어왔을 때 데이터가 자동으로 불러와지나요?
  기본으로 적용되는 필터나 조건이 있나요?
  이전 화면에서 넘어오는 값이 있나요? (예: 선택한 주문 ID)
  → screen.initial_state 저장
```

---

### Phase 1. 컴포넌트 순회

1. `layout[]`에서 `meta.interactive: true`인 컴포넌트를 `position.slot` + `position.order` 순서로 정렬.
2. 이미 `actions[]`에 `user_confirmed` 상태의 entry가 있는 컴포넌트는 건너뜀.
3. 남은 컴포넌트를 하나씩 처리.

---

## 인터뷰 프로세스 (컴포넌트 1개 기준)

### Step 1: 컨텍스트 제공
```
AI: "[CMP-ORDER-LIST.exportBtn — Button '엑셀 내보내기'] 이 버튼을 누르면 무엇이 일어나야 하나요?"
```
- 컴포넌트 ID + DS 컴포넌트 종류 + props.label을 함께 제시해 맥락 제공.

### Step 2: 질문 선택
`question-bank.md`의 공통 질문 + 컴포넌트 특성에 맞는 추가 질문 사용.
한 번에 모든 질문을 하지 않는다. 사용자 답변에 따라 필요한 질문만 이어간다.

> 질문 목록: [question-bank.md](question-bank.md)

### Step 3: 답변 → 구조화
사용자의 자연어 답변을 `actions[]` 포맷으로 구조화:
```yaml
- id: REQ-ORDER-LIST.001        # 자동 채번 (link-manifest 참조)
  component: CMP-ORDER-LIST.exportBtn
  trigger: click
  behavior: "현재 필터 조건의 주문 목록을 엑셀 파일로 다운로드"
  outcome:
    type: export                # navigate | query | mutate | export | open | validate | noop
    target: ENT-ORDER
  permission: admin             # screen.permission보다 좁을 수 없으면 sufficiency error
  error_behavior:               # Q-ERROR 답변을 케이스별로 구조화 (필수)
    default: "토스트 에러 메시지 표시"
    network_fail: "재시도 버튼 표시"
    permission_denied: "버튼이 DOM에 없어 도달 불가"
```

**`error_behavior` 수집 규칙:**
- Q-ERROR 답변 후 케이스를 분리해 구조화. PO가 케이스를 구분하지 않으면 `default`만.
- `outcome.type`이 `mutate` / `export` / `query`면 필수. `navigate` / `noop`은 선택.
- permission_denied는 `permission != all`이면 항상 포함.

**`reactive` 수집 규칙 (`outcome.type: query`인 컴포넌트만):**
- Q-REACTIVE 질문 후, 응답하는 컴포넌트가 있으면 `layout[]` 해당 컴포넌트에 `reactive` 추가:
```yaml
# layout[] 수정 예시 (actions 작성 후 반영)
- id: CMP-ORDER-LIST.table
  reactive:
    requery_on: [CMP-ORDER-LIST.filterbar]
    linked_action: REQ-ORDER-LIST.001
```

- `outcome.type` 판단 기준: `question-bank.md`(이 스킬 폴더) outcome.type별 섹션 참조.
- 사용자가 권한을 언급하지 않으면 `permission: all`로 기본 설정 후 spec-readiness 체크에서 warn.
- `permission`이 `screen.permission`보다 더 좁은 경우(예: screen=all, action=admin) → 정상. 반대면 sufficiency error.

### Step 4: Acceptance 초안 제시
구조화 결과를 바탕으로 Gherkin acceptance 초안 제시:
```
AI: 이렇게 정리했습니다. 확인해 주세요:
    - Given ADMIN 로그인, When 엑셀 버튼 클릭, Then 현재 필터 조건의 xlsx 다운로드
    - Given 일반 사용자, When 화면 진입, Then 엑셀 버튼이 DOM에 없다
    맞나요? 추가하거나 바꿀 것이 있으면 말씀해 주세요.
```

### Step 5: 사용자 확인 → status 갱신
사용자가 확인하면 `status: user_confirmed`.
수정이 있으면 반영 후 재확인.

### Step 6: prompt_log 기록
```yaml
prompt_log:
  - id: PRM-{다음번호}
    stage: action
    text: {사용자 원문 그대로}
    affected: [CMP-ORDER-LIST.exportBtn, REQ-ORDER-LIST.001]
    applied_version: {현재 version + 1}
```
`provenance.intent` 재생성: 관련 발화들의 compact 요약.

---

## 주의사항

- **발화 원문 보존**: 사용자가 말한 그대로를 `prompt_log.text`에 기록. 요약·정제 금지.
- **acceptance는 PO 관점으로 작성**: 기술 구현이 아닌 "사용자가 무엇을 경험하는가" 중심.
- **outcome.target 명시**: navigate면 어느 SCR-, export면 어느 ENT-/EXT-인지 명확히.
- **한 번에 하나씩**: 여러 컴포넌트를 동시에 처리하지 않는다.
