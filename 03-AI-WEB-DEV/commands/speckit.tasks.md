# Command: /speckit.tasks

## 목적

`/speckit.plan` 산출을 **T### 태스크 목록**으로 분해한다. test-first로 정렬하고,
독립 태스크는 병렬 마커를 단다.

## 실행 조건

- `/speckit.plan` 완료 (Data Model·ERD·API·wiring 계획 확정)

## 실행 절차

1. **태스크 채번** — 구현 단위마다 `T###` ID 부여 (스파인 ID, `rules/` 채번 규칙).
2. **test-first 정렬** — 각 구현 태스크 **앞에** 대응 테스트 태스크를 배치한다(red 먼저).
3. **순서** — backend 태스크 → frontend wiring 태스크 순.
4. **[P] 병렬 마커** — 서로 의존이 없는 독립 태스크는 `[P]` 로 표시한다.
5. **추적 연결** — 각 태스크에 관련 SPEC-/REQ-/CMP- 를 연결해 acceptance까지 추적 가능하게 한다.

## 산출물 (예시)

```
T001 [P] OrderEntity 테스트 작성 (REQ-ORDER-LIST.001)
T002      OrderEntity 구현
T003      OrderService.list 테스트 작성
T004      OrderService.list 구현
T005      GET /api/orders 컨트롤러 테스트
T006      GET /api/orders 컨트롤러 구현
T007      OrderList shell wiring 테스트 (화면 레벨)
T008      OrderList API hook + 상태 연결
```

## 경계

- 태스크 목록까지만. 구현·커밋은 `/speckit.implement`.
- 테스트 태스크 없는 구현 태스크는 만들지 않는다 (TDD 강제, `rules/tdd-policy.md`).
- 이 목록은 Gate B 검토 대상이다 — approve 전 구현 금지.
