# Command: /speckit.implement

## 목적

T### 태스크를 순서대로 **TDD 루프(red → green → refactor)** 로 구현하고 커밋한다.

## 실행 조건

- `/speckit.tasks` 의 T### 목록이 **Gate B 통과**(개발자 approve) 상태
- bl-analyst 미해결 항목 0

## 실행 절차 (T### 1개 기준)

1. **테스트 먼저 (subagent: test-author)**
   - acceptance(Gherkin) + worked examples 에서 **실패 테스트**를 먼저 생성한다.
   - 2계층: **API 레벨** 테스트 + **화면 레벨** 테스트. (`subagents/test-author.md`)
2. **구현 — red → green → refactor**
   - red: 테스트 실패 확인 → green: 통과 최소 구현 → refactor: 중복 제거.
   - DS·코딩 컨벤션 준수 (`skills/design-system-usage`, `skills/coding-style`).
   - complexity:high BL은 `skills/complex-bl` 로 decision table/state machine 구현.
3. **hook: tdd-gate.py** — 테스트 없음/실패 시 commit 차단.
4. **hook: commit-spine-id.py** — 커밋 메시지에 스파인 ID 자동 포함: `[PACK-ORDER/T001] 요약 (REQ-...)`.

## 반복 후

- 팩의 모든 T### 완료 → **subagent: code-reviewer** 로 DS 준수·보안·스타일·TDD·스파인 ID 검토.
- integration 브랜치 머지 → PR.

## frontend wiring 원칙

- Phase α shell 컴포넌트에 API hook·상태·권한 조건부 렌더·에러 처리를 **추가**한다.
- layout 구조(컴포넌트 위치·배치)는 바꾸지 않는다.
- screen model에 없던 신규 컴포넌트(modal/drawer 등)는 이 팩에서 shell+wiring 동시 생성.

## 경계

- 구현만. 새 계약·요구사항을 만들지 않는다.
- acceptance가 바뀌면 기존 테스트가 깨지는 것이 정상(TDD 백스톱) — Change Order 절차를 따른다.
