---
name: complex-bl
description: >
  ③ AI-WEB-DEV 레이어 스킬. complexity:high 노트에 대해 bl-analyst가 생성한
  decision table·state machine·worked examples를 해석해 실행 코드로 구현하는 방법을 안내한다.
  분기/상태 전이가 많은 비즈니스 로직을 구현하거나 "복잡한 비즈니스 로직", "decision table",
  "state machine", "bl-analyst 산출물"을 다룰 때 사용.
when_to_use: complexity:high BL 구현, decision table·state machine 코드화, bl-analyst 산출물 적용 시.
allowed-tools: Read Write Edit
layer: 03-AI-WEB-DEV
phase: [Phase β]
version: 1.0.0
owner: 개발자 (VSCode + Claude Code)
tags: [business-logic, decision-table, state-machine, bl-analyst, tdd]
references:
  - ../../subagents/bl-analyst.md
  - ../../rules/tdd-policy.md
spine-ids: [REQ-, NOTE-, SPEC-, T###]
---

# Skill: complex-bl

## 역할

`complexity: high`로 태깅된 비즈니스 규칙을, speckit.plan 중 **bl-analyst subagent**가 만든
구조화 산출물(decision table·state machine·worked examples)을 받아 **결정론적 코드**로 구현한다.
자연어 규칙을 직접 코딩하지 않고, 먼저 표/상태기계로 정규화한 뒤 구현하는 것이 핵심이다.

**경계:** 규칙의 *정의*는 ②(note-intake verbatim), 구조 분석은 bl-analyst, 구현은 이 스킬이다.

---

## 구현 절차

1. **산출물 수신** — bl-analyst의 decision table(조건→결과 행렬), state machine(상태·전이·가드), worked examples(입력→기대출력)를 읽는다.
2. **테스트 먼저(TDD)** — worked examples를 실패 테스트로 옮긴다(test-author 협업). 각 decision row = 최소 1 테스트 케이스.
3. **decision table 구현** — 분기 폭주 대신 표를 자료구조(맵/룰셋)로 옮겨 평가한다. 모든 행이 커버되는지 검증.
4. **state machine 구현** — 허용 전이만 코드로 표현하고, 정의되지 않은 전이는 명시적으로 거부한다.
5. **red → green → refactor** — 테스트 green 후 중복 제거. `tdd-gate` hook이 테스트 없는 구현을 차단한다.
6. **미해결 항목** — bl-analyst가 남긴 open decision이 있으면 Gate B 통과 불가. 개발자 판정 후 진행.

---

## 규칙 (Rules)

- 모든 decision row·전이는 테스트로 커버한다(`rules/tdd-policy.md`).
- 정의되지 않은 입력/전이는 조용히 통과시키지 않고 명시적 에러로 처리한다.
- 규칙 원문(verbatim)을 임의 해석·요약하지 않는다 — 모호하면 ②에 Change Order/질의로 되돌린다.
- 커밋 메시지에 스파인 ID 포함: `[PACK-ORDER/T001] 요약 (REQ-...)`.
