# Feature Specification: [PACK-ID — 도메인명]

**Spec Pack**: `PACK-[NAME]` (② 발행)  
**Feature Branch**: `[###-pack-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: `model_repo/specs/PACK-[NAME]/spec.yaml` (PO 계약 원문 번들)

<!--
  하니스 규칙(constitution): 이 spec은 ②가 확정(Gate A)한 spec-pack에서 **파생**된다.
  새 화면(SCR-)·요구사항(REQ-)을 발명하지 않는다. 모든 항목은 PACK-의 scope/actions/notes 원문으로 추적된다.
  spec-kit 표준의 User Story = 본 하니스의 screen(SCR-) + actions(REQ-) 묶음.
-->

## Pack Scope *(mandatory)*

- **Screens (SCR-)**: [SCR-ORDER-LIST, SCR-ORDER-DETAIL …] — `yaml_ref` / `render_ref` / `shell_ref`(Phase α 산출) / `pinned_contract`(version·hash·git_ref)
- **Components (CMP-)**: [CMP-ORDER-LIST.table …]
- **Requirements (REQ-)**: [REQ-ORDER-LIST.001 …]
- **Actor/Entity 경계**: [예: user 플로우, ENT-ORDER 도메인]
- **Pinned contract**: 각 화면의 고정 계약 버전(version·hash·git_ref) — 구현은 이 스냅샷 위에서만(freeze).

## User Scenarios & Acceptance *(mandatory)*

<!-- 각 SCR-는 독립 테스트 가능한 슬라이스. acceptance는 ②가 확정한 Gherkin 원문을 그대로 옮긴다(임의 변경 금지). -->

### SCR-[ID] — [화면명] (Priority: P1)

[화면이 제공하는 사용자 여정 한 줄]

**Independent Test**: [이 화면만으로 검증하는 방법]

**Acceptance Scenarios** (REQ- 추적):

1. **[REQ-...001]** **Given** [상태], **When** [trigger], **Then** [결과]  ← outcome.type: [navigate|query|mutate|export|…], permission: [all|role]
2. **[REQ-...002]** **Given** [상태], **When** [trigger], **Then** [결과]

---

### SCR-[ID2] — [화면명] (Priority: P2)

[반복]

---

### Edge / Error / Empty States

<!-- screen model의 error_behavior·initial_state·intake.open_questions 기반. 추측 금지. -->

- **[REQ-...]** 실패: [error_behavior.default / network_fail / permission_denied]
- 빈 상태: [empty_state]
- 초기 진입: [initial_state.params / default_filter / auto_query]

## Business Rules & Notes (verbatim) *(include if present)*

<!-- screen model notes[] 원문 그대로. verbatim — 요약·수정 금지. complexity 태그 보존. -->

- **NOTE-[ID]** (scope: [CMP-/screen], complexity: [low|med|high]): "[PO 원문 그대로]"
  - `complexity: high` → `/speckit-plan`에서 **bl-analyst** subagent가 decision table·state machine으로 정규화(구현 전).

## Non-Functional Requirements *(include if present)*

- **NFR-[ID]** (category: [performance|concurrency|audit|security|availability]): [concurrent_users / response_target / priority]

## Data Contracts (ENT-/EXT-) *(include if present)*

<!-- 팩의 entities[]/externals[] ref. ②의 개념 계약 원본. ③ /speckit-plan이 data-model.md·ERD·어댑터로 *파생*(물리설계는 여기서 하지 않음). 새 엔티티 발명 금지. -->

- **ENT-[ID]** (`model_repo/entities/ENT-[ID].yaml`): [엔티티 의미 한 줄, owner_screens]
- **EXT-[ID]** (`model_repo/externals/EXT-[ID].yaml`): [외부 시스템 의미, protocol, failure_policy 요약]

## Journeys (E2E, JRN-) *(include if present)*

<!-- 팩 화면을 거치는 여정 ref. ③ Phase γ가 JRN-당 Playwright(+BDD) E2E 1개로 구현. step 검증은 각 화면 action의 acceptance를 재사용. -->

- **JRN-[ID]** (`model_repo/journeys/JRN-[ID].yaml`, priority: [high|med|low]): [여정 한 줄] — steps: [SCR-…/REQ-… 순서]

## Open Items (deferred) *(from intake.open_questions)*

<!-- ②가 deferred로 넘긴 항목. /speckit-clarify로 해소하거나, scope 외면 Change Order로 ②에 질의. -->

- **Q-[ID]** (target: [CMP-/screen]): "[질문]" — defer_reason: "[사유]"

## Clarifications

<!-- /speckit-clarify가 채운다. 각 답변은 위 적절한 섹션에도 반영된다. -->

### Session [DATE]

- Q: [질문] → A: [답변]

## Success Criteria *(mandatory)*

<!-- 측정 가능·기술 중립. acceptance 추적성으로 환원되는 것만. KPI/사업 지표 제외. -->

- **SC-001**: [예: 모든 REQ- acceptance가 2계층 테스트(API+화면) green]
- **SC-002**: [예: decision table 모든 row / state 모든 전이 테스트 커버 100%]
- **SC-003**: [측정 가능한 동작 지표 — NFR 반영 시]

## Assumptions

- 프레임워크·테스트 스택: ①의 `tech-stack.md` 핀(프로젝트마다 `/speckit-constitution`으로 정의). 임의 변경·가정 금지.
- 이 팩은 Gate A(confirmed) 계약만 포함한다. scope를 벗어난 요구는 Change Order 대상.
