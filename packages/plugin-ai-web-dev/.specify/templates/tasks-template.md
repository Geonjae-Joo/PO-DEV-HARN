---
description: "Task list template — 하니스 test-first TDD (2계층)"
---

# Tasks: [PACK-ID — 도메인명]

**Input**: `specs/[###-pack-name]/` (plan.md, spec.md, data-model.md, contracts/, bl/)
**Spec Pack**: `PACK-[NAME]`

**규칙 (constitution IV·V·VI 강제)**:
- **테스트는 OPTIONAL이 아니다.** 모든 구현 태스크는 앞선 **테스트 태스크**와 짝을 이룬다(test-first). 테스트 없는 구현 태스크는 만들지 않는다 — `tdd-gate.py`가 commit 레벨에서 차단.
- **2계층**: 각 REQ-는 **API 레벨** 테스트 + **화면 레벨** 테스트를 모두 가진다.
- **커버리지**: decision table 모든 row, state machine 모든 전이 ≥ 1 테스트.
- **스파인 ID**: 각 태스크에 연결 `SPEC-/PACK-/REQ-/CMP-` 표기. 커밋은 `[PACK/T###] (REQ-)`.
- **[P]**: 서로 의존 없는(다른 파일) 태스크 병렬 가능.

## Format: `[T###] [P?] [SCR/REQ] 설명 (파일경로)`

## Phase α 참조 — Scaffold (이 팩 이전, 1회)

> shell은 `/speckit-scaffold`가 생성. `[SCAFFOLD]` 커밋은 tdd-gate **면제**(commit-spine-id는 적용). 이 tasks.md엔 포함하지 않음(이미 존재 전제).

## Phase 1: Backend — Domain (test-first)

<!-- Entity → Service → Controller. 각 구현 앞에 RED 테스트. -->

- [ ] T001 [P] [REQ-...001] **RED** OrderEntity 테스트 작성 + 실패 증명 (`backend/tests/...`)
- [ ] T002 [REQ-...001] **GREEN** OrderEntity 최소 구현 (`backend/src/models/order.*`)
- [ ] T003 [P] [REQ-...001] **RED** OrderService.list 테스트 (경계·권한·에러)
- [ ] T004 [REQ-...001] **GREEN** OrderService.list 구현 → **REFACTOR**
- [ ] T005 [REQ-...001] **RED** GET /api/orders 컨트롤러 테스트 (API 레벨: 요청/응답/권한)
- [ ] T006 [REQ-...001] **GREEN** GET /api/orders 구현

### complexity:high BL (bl-analyst 산출 → 테스트)

- [ ] T0xx [NOTE-...] **RED** decision table 각 row → 테스트 / state machine 각 전이 → 테스트
- [ ] T0xx [NOTE-...] **GREEN** complex-bl 구현 (모든 row/전이 green)

## Phase 2: Frontend — Wiring (test-first, 화면 레벨)

<!-- shell_ref 컴포넌트에 wiring 추가. layout 구조 불변. -->

- [ ] T0xx [SCR-...] **RED** OrderList 화면 테스트 (상태 전이·권한 조건부 렌더·에러)
- [ ] T0xx [SCR-...] **GREEN** OrderList API hook + 상태 연결 (`frontend/src/pages/OrderList/...`)
- [ ] T0xx [REQ-...002] **RED/GREEN** rowClick → navigate(SCR-ORDER-DETAIL) 테스트·wiring

## Phase 3: Integration / NFR (Phase γ 대비)

- [ ] T0xx [P] E2E 핵심 플로우 (navigate 체인)
- [ ] T0xx [NFR-...] 성능·동시성 검증 (response_target·concurrent_users)
- [ ] T0xx 보안 (authN/Z, 입력 검증, 민감정보)

## Dependencies & Order

- Backend(Entity→Service→Controller) → Frontend wiring.
- 각 태스크 내: **RED(실패 증명) → GREEN(최소) → REFACTOR**. red 미증명 시 green 진입 금지.
- acceptance 변경 시 기존 테스트 깨짐 = 정상(Change Order: amend/regenerate). REQ 추가만이면 additive.

## Gate B (구현 전 필수)

- [ ] Data Model·ERD·API 확정  - [ ] bl-analyst open decision = 0
- [ ] 모든 구현 태스크에 대응 테스트 태스크 존재  - [ ] 개발자 approve
- [ ] `/speckit-analyze` CRITICAL = 0 (constitution 위반 없음)

## Notes

- 커밋: 행위=`[PACK/T###] 요약 (REQ-)`, 구조 리팩터=`refactor(T###)`, scaffold=`[SCAFFOLD]`, Change Order=`[CO/<판정>] (re-pin v…)`. (Tidy First: 구조/행위 분리 커밋)
- `/speckit-implement`가 태스크 1개씩 RED→GREEN→REFACTOR→COMMIT 수행, `tdd-gate.py`·`commit-spine-id.py` 강제.
