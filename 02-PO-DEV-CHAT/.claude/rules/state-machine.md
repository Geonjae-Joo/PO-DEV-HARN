<!-- supporting-file: skills/gate-a-check, skills/layout-recommend -->
<!-- loaded-by: gate-a-check 스킬이 Gate A 판정 시, layout-recommend가 상태 전환 조건 확인 시 참조 -->

# State Machine — Screen Model 상태 전환

## 상태 정의

```
draft               초안. 편집 중.
layout_confirmed    layout 확정. L1 error 0.
actions_in_progress Stage 2 action 인터뷰 진행 중.
review              PO가 최종 검토 중.
confirmed           Gate A 통과. 계약 확정.
```

## 전환 다이어그램

```
draft
  │ layout 안정(L1 error 0)
  ▼
layout_confirmed
  │ Stage 2 시작
  ▼
actions_in_progress
  │ 모든 interactive CMP 처리 완료
  │ (action + acceptance + user_confirmed)
  ▼
review
  │ sufficiency pass/pass_with_deferred
  │ + 모든 action user_confirmed
  │ + PO 승인
  ▼
confirmed ──(Gate A)──► spec-generator 실행 → PACK-* 발행

confirmed 후 변경: Change Order 프로세스 (③ change-order-policy.md)
```

## 저장(Save) 시마다 자동 실행

```
1. schema-validate (on-save-schema-validate.py)
   └ 실패 → 저장 차단 (400)

2. lint L1~L4 (on-save-lint-L1-L4.py)
   └ L1 error → 저장 차단
   └ L2~L4 error → 저장 허용, 경고 표시
   └ warn → 저장 허용, 경고 표시

3. optimistic lock 체크
   └ 요청 version ≠ 현재 version → 409 충돌

4. 새 version 발급 → 저장 완료

5. layout-recommend 렌더링 (lint 통과 시에만)
   └ renders/SCR-*.render.html 갱신
```

## Gate A 통과 조건 (gate-a-check.py)

```
✓ lint error 0 (L1~L4)
✓ sufficiency == 'pass' OR 'pass_with_deferred'
✓ 모든 REQ-* status == 'user_confirmed'
✓ open_questions 중 status=open 항목 0개 (deferred는 defer_reason 필수)
✓ PO 명시적 승인 (--pi-approved 플래그)
→ status: confirmed + version 고정 + git tag
```

## Stage 전환 조건 상세

| 전환 | 조건 |
|---|---|
| draft → layout_confirmed | lint L1 error 0 |
| layout_confirmed → actions_in_progress | 자동 (Stage 2 시작 시) |
| actions_in_progress → review | 모든 interactive CMP에 action 존재 + 모두 user_confirmed |
| review → confirmed | Gate A 전체 통과 |

## optimistic locking

- 모든 save 요청에 현재 `version` 포함.
- 서버가 저장 시 DB version과 비교.
- 불일치 → HTTP 409 반환.
- 클라이언트가 최신 버전을 다시 읽고 병합 후 재시도.
- last-write-wins 절대 금지.

## 확정 후 변경 처리

```
confirmed 상태에서 PO가 수정 요청
  → Change Order 큐에 추가 (구현 중이면 소프트 프리즈)
  → ③의 개발자가 판정: dismiss | amend | regenerate
  → 판정 결과에 따라 re-pin 또는 새 Gate B
```
