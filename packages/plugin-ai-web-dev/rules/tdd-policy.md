<!-- rule: ③ AI-WEB-DEV — TDD 정책 (tdd-gate hook이 강제) -->

# TDD Policy

constitution(①)의 하드 룰 5번(TDD)을 ③에서 구체화한다. `tdd-gate.py` hook이 commit 시 강제한다.

## 3겹 루프 (red → green → refactor)

1. **red** — 구현 전에 실패하는 테스트를 먼저 작성한다(test-author subagent). 처음에 반드시 실패해야 한다.
2. **green** — 테스트를 통과시키는 **최소 구현**만 한다.
3. **refactor** — 테스트 green 상태를 유지하며 중복·복잡도를 제거한다.

> **강제 한계(정직한 명시):** commit 시점 훅은 과거 상태를 알 수 없어 "red가 먼저였는지"를 기계적으로 검증할 수 없다.
> `tdd-gate.py`는 (a) 구현 변경에 대응 테스트가 함께/이미 존재하는가, (b) 현재 테스트가 green인가 — 이 둘만 강제한다.
> **red-우선 순서는 `/speckit.tasks`의 테스트-우선 정렬 + test-author 절차로 보장**하며, 훅은 백스톱이다.

## 강제 규칙

- **테스트 없는 구현 금지.** 대응 테스트가 없거나 실패 상태면 `tdd-gate.py`가 commit을 차단한다.
- **테스트 러너 필수.** `tdd-gate.py`가 러너를 자동 탐지하지 못하고 `HARNESS_TEST_CMD`도 없으면 구현 커밋을 **차단**한다(이전의 silent-pass 폐지). 초기 스캐폴드 등 의도적 우회는 `HARNESS_TDD_ALLOW_NO_RUNNER=1`로만 허용된다.
- **테스트 파일 판별은 네이밍 컨벤션 기준**(`test_*`/`*_test.*`/`*.test.*`/`*.spec.*`/`*_spec.*` 또는 `test/tests/__tests__/e2e` 디렉터리). 하니스의 spec-pack(`specs/`, `spec-pack.yaml/md`)은 테스트로 오인하지 않는다.
- 각 T### 구현 태스크는 앞선 테스트 태스크와 짝을 이룬다(`/speckit.tasks` 정렬).
- 2계층 테스트: **API 레벨 + 화면 레벨** 모두 요구된다(커버리지 책임은 `/speckit.tasks`·Gate B `gate-b-checklist.md`; 훅은 파일 존재·green만 본다).
- decision table의 모든 row, state machine의 모든 전이는 최소 1 테스트로 커버한다(Gate B 점검).

## 예외

- **scaffold commit**(Phase α)은 테스트 불필요 — `[SCAFFOLD]` skip 마커로 `tdd-gate`가 예외 처리.

## Change Order와 TDD 백스톱

- acceptance가 바뀌면 기존 테스트가 깨지는 것(breaking)이 정상 신호다 → regenerate/amend 판정.
- REQ 추가만이면 새 테스트·태스크를 더하는 additive 변경으로 처리한다.
