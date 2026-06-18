---
name: note-intake
description: >
  Stage 3 스킬. PO의 자유 발화 비즈니스 규칙·도메인 지식·제약사항을 verbatim으로 수집한다.
  본문은 절대 수정하지 않고 분류(kind)와 복잡도(complexity)만 제안한다.
  Stage 2 완료 후, 또는 PO가 "추가 설명", "비즈니스 규칙", "특이사항"을 언급할 때 사용.
when_to_use: '"추가 설명", "비즈니스 규칙", "특이사항", "노트 추가", "예외 케이스" 언급 시.'
allowed-tools: Read Write Edit
layer: 02-PO-DEV-CHAT
stage: Stage 3
version: 1.0.0
owner: PO (도메인 전문가)
tags: [note, verbatim, business-rule, complexity, nfr]
supporting-files: [../../rules/prompt-log-policy.md]
spine-ids: [NOTE-, NFR-]
---

# Skill: note-intake

## 역할

Stage 3 담당. 사용자가 컴포넌트 또는 화면 전체에 대해 **자유롭게 기입하는 원문 요구**를 수집한다.
AI는 분류와 복잡도 태그만 제안하고, **본문은 절대 수정·요약·재작성하지 않는다**.

---

## 핵심 원칙: verbatim 보존

비즈니스 로직과 도메인 지식은 PO의 표현 그대로가 중요하다.
- AI가 "더 명확하게" 재작성하면 뉘앙스와 의도가 손실된다.
- 개발자는 PO가 실제로 어떻게 표현했는지 원문을 보아야 한다.
- `verbatim: true` 필드로 강제 표시.

---

## 수집 방법

### 유도 방식

action 인터뷰(Stage 2)가 끝난 후:
```
AI: 이 화면이나 각 컴포넌트에 대해 추가로 설명하고 싶은 비즈니스 규칙, 
    도메인 지식, 특별한 요구사항이 있으시면 자유롭게 적어주세요.
    예: 계산 방식, 예외 케이스, 성능 요구, 권한 세부사항 등
```

### scope 지정

사용자가 특정 컴포넌트에 대한 노트를 입력하면:
- `scope: CMP-ORDER-LIST.table` (컴포넌트별)
- `scope: screen` (화면 전체에 해당)

---

## AI의 역할 (제한적)

### 허용: 분류(kind) 제안
```
AI: 이 내용은 비즈니스 로직 규칙으로 분류하겠습니다. (kind: business_rule)
    맞나요?
```

종류: `business_rule` | `nfr` | `ux` | `constraint` | `assumption` | `open_question`

### 허용: NFR follow-up 질문 (kind: nfr 분류 시에만)

`kind: nfr`로 분류된 경우에만, 본문 수정 없이 수치를 추가로 물어본다.

```
AI: 성능 요구사항으로 분류했습니다. 조금 더 구체화할게요:
    - 몇 명이 동시에 이 화면을 사용하나요?
    - 응답이 몇 초 이내여야 하나요?
    - 반드시 지켜야 하나요, 아니면 가능하면 좋은 수준인가요?
    (모르시면 괜찮아요. 나중에 답할 수 있습니다.)
```

결과를 `nfr_detail`로 구조화 (본문 `body`는 절대 변경하지 않음):
```yaml
- id: NOTE-ORDER-LIST.002
  body: "이 화면은 월말에 동시 접속이 몰림. 느려지면 안 됨."  # 원문 그대로
  kind: nfr
  nfr_detail:                 # follow-up으로 추가 수집
    category: performance
    concurrent_users: 500
    response_target: "2초 이내"
    priority: must
```

PO가 모르거나 미정이면 `nfr_detail` 생략 → sufficiency-check가 open_question 생성.

### 허용: 복잡도(complexity) 제안
```
AI: 환율 환산 로직은 분기 조건이 여러 개 있어 복잡도가 높아 보입니다. (complexity: high)
    나중에 개발 단계에서 세부 분석이 필요할 것 같습니다.
```
- `low`: 단순 표시, 계산 없음
- `med`: 조건 1~2개
- `high`: 다중 분기, 상태 머신, 외부 의존

### 금지: 본문 수정
```
❌ AI가 "더 명확하게" 바꿔쓰기
❌ AI가 요약하거나 핵심만 추출
❌ AI가 기술 용어로 치환
```

---

## 산출 YAML

```yaml
notes:
  - id: NOTE-ORDER-LIST.001
    scope: CMP-ORDER-LIST.table
    verbatim: true
    body: |
      금액은 주문 시점 환율로 KRW 환산해서 보여줘야 함.
      환율 못 받아온 날은 전일자 환율 쓰고, 그것도 없으면 관리자한테 알림.
    kind: business_rule        # AI 제안, PO 확인
    complexity: high           # high → speckit.plan 중 bl-analyst 자동 호출
    author: ubc
    at: 2026-06-12T11:02:00Z
```

---

## complexity: high 처리

`complexity: high`로 분류된 노트는 팩에 그대로 포함된다.
③ speckit.plan 단계에서 bl-analyst subagent가 자동으로 호출되어
decision_table / state_machine / worked_examples를 생성한다.
**spec-generator는 bl-analyst를 호출하지 않는다.**
