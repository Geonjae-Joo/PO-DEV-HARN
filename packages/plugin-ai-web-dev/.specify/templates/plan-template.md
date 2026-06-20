# Implementation Plan: [PACK-ID — 도메인명]

**Spec Pack**: `PACK-[NAME]` | **Branch**: `[###-pack-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: `specs/[###-pack-name]/spec.md` (← spec-pack PACK-[NAME])

**Note**: `/speckit-plan`이 채운다. 하니스에선 도메인 전체(Entity·Service·API)를 **한 번에** 설계한다(팩 단위). 산출물은 Gate B 검토 대상이다.

## Summary

[팩의 primary entity + 구현 접근. 어떤 화면(SCR-)·요구(REQ-)를 어떤 백엔드·wiring으로 충족하는가.]

## Technical Context (tech-stack 핀 고정)

**Framework (pinned ← foundation/decisions/tech-stack.md, 프로젝트별)**: [frontend … / backend … — ①의 `/speckit-constitution` 산출 그대로. 특정 스택 가정 금지]  
**Testing (2계층)**: API 레벨 [예: 백엔드 통합·계약 테스트] / 화면 레벨 [예: 컴포넌트 테스트 + 핵심 플로우 E2E]  
**Storage**: [DB/스키마] **Target/Scale/Perf**: [NFR 반영 — concurrent_users·response_target]  
**Project Type**: web (frontend + backend, 단일 `app_repo`)

## Constitution Check

*GATE: Phase 0 research 전 통과, Phase 1 설계 후 재확인. `.specify/memory/constitution.md` 권위.*

- [ ] I. Screen Model SSOT — 계약 재정의 없음, 구현만
- [ ] II. DS 폐쇄 — DS 밖 컴포넌트 없음
- [ ] III. 스파인 ID — 모든 산출물이 SCR/CMP/REQ/PACK/T### 추적
- [ ] IV. Test-First — 모든 구현에 2계층 테스트 선행 계획
- [ ] V. Gate B — Data Model·ERD·API 확정 + bl-analyst open=0 계획
- [ ] VI. 커밋 스파인 ID — 커밋 계획에 `[PACK/T###] (REQ-)` 형식
- [ ] tech-stack 핀 준수 (①)

## Phase 1 — Domain Design (팩 전체 일괄)

### Data Model + ERD
[엔티티·필드·타입·관계·제약. 도메인 전체. screen model의 ENT- 참조를 구체화.]

### API 설계
[endpoint, request/response 스키마, actor·role별 권한(action.permission ⊇ screen.permission). 에러 응답.]

### 복잡 BL (complexity: high → bl-analyst)
[`notes` 중 complexity:high 항목 → bl-analyst가 **decision table · state machine · worked examples** 산출. open decision이 1개라도 남으면 Gate B 통과 불가.]

### Frontend Wiring 계획
[Phase α shell(`shell_ref`) 기준: 컴포넌트 ↔ API hook ↔ 상태 ↔ 권한 조건부 렌더 ↔ 에러 처리 매핑. **layout 구조는 변경 금지**.]

## Project Structure (app_repo)

```text
specs/[###-pack-name]/
├── plan.md            # 이 파일
├── research.md        # Phase 0 (필요 시)
├── data-model.md      # 엔티티·ERD
├── contracts/         # API 스키마 (= phase contract, acceptance 추적)
├── bl/                # bl-analyst decision-table·state-machine (complexity:high)
└── tasks.md           # /speckit-tasks 산출 (test-first)

app_repo/
├── backend/   ...     # Entity → Service → Controller
└── frontend/src/pages/[Screen]/   # shell_ref 위 wiring (layout 불변)
```

**Structure Decision**: [단일 app_repo. 백엔드 → 프론트 wiring 순.]

## Complexity Tracking

> Constitution Check 위반을 정당화할 때만 작성.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |

## Next

`/speckit-tasks` (test-first 분해) → `/speckit-analyze` (Gate B 일관성) → Gate B approve → `/speckit-implement`.
