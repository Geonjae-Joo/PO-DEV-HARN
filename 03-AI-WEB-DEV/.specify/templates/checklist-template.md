# [GATE] Checklist: [PACK-ID — 도메인명]

**Purpose**: [예: Gate B 구현 전 점검 / Gate A 인계 점검 / NFR 점검]
**Created**: [DATE]
**Spec Pack**: `PACK-[NAME]` — [spec.md / plan.md / tasks.md 링크]

**Note**: `/speckit-checklist`가 spec/plan/tasks + constitution 기준으로 채운다. 아래는 하니스 게이트 표준 항목 — 컨텍스트에 맞게 구체화한다.

## Gate A 인계 확인 (② → ③)

- [ ] CHK001 모든 대상 화면 `status: confirmed` (Gate A 통과)
- [ ] CHK002 pinned_contract(version·hash·git_ref) 고정됨
- [ ] CHK003 acceptance(Gherkin) 원문 보존 — ③에서 임의 변경 없음
- [ ] CHK004 open_items(deferred) 처리 방향 결정됨 (이번 팩/보류/Change Order)

## Constitution 준수 (NON-NEGOTIABLE)

- [ ] CHK010 Screen Model SSOT — 계약 재정의 없음, 구현만
- [ ] CHK011 DS 폐쇄 — DS 밖 컴포넌트 0 (lint L1)
- [ ] CHK012 스파인 ID — SCR→CMP→REQ→PACK→T###→test→commit 추적 끊김 0
- [ ] CHK013 tech-stack 핀(①) 준수 — 임의 프레임워크/스택 변경 없음

## Gate B 구현 전 (개발자 소유)

- [ ] CHK020 Data Model·ERD 확정 (엔티티·필드·관계·제약)
- [ ] CHK021 API 설계 확정 (endpoint·req/res·권한)
- [ ] CHK022 complexity:high BL → bl-analyst decision table/state machine, **open decision = 0**
- [ ] CHK023 T### test-first 정렬 — 모든 구현 태스크에 대응 테스트 태스크
- [ ] CHK024 `/speckit-analyze` CRITICAL = 0
- [ ] CHK025 개발자 approve

## TDD 충족 (구현 중·후)

- [ ] CHK030 각 REQ- 2계층 테스트(API + 화면) 존재
- [ ] CHK031 모든 테스트 red→green 흔적 (red 실패 증명 로그)
- [ ] CHK032 decision table 모든 row / state machine 모든 전이 테스트 커버
- [ ] CHK033 tdd-gate 통과 (테스트 없는 구현 commit 0)
- [ ] CHK034 커버리지 임계치 충족 (권고 ≥ 80%)

## 커밋·추적

- [ ] CHK040 모든 commit에 스파인 ID (`[PACK/T###] (REQ-)`) — commit-spine-id 통과
- [ ] CHK041 구조/행위 분리 커밋 (Tidy First)
- [ ] CHK042 Change Order는 `[CO/<판정>]` + re-pin 버전 표기

## Notes

- 완료: `[x]`. 위반은 `/speckit-analyze` 기준 CRITICAL/HIGH로 분류해 해소 후 진행.
