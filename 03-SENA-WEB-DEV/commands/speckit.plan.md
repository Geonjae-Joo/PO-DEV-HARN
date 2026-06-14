# Command: /speckit.plan

## 목적

확정된 팩 scope에 대해 **도메인 전체의 Data Model · ERD · API 설계 · frontend wiring 계획**을
한 번에 수립한다. complexity:high 노트는 bl-analyst subagent로 넘긴다.

## 실행 조건

- `/speckit.specify` 로 팩 scope 확정 완료
- 대상 화면들이 ② 기준 `status: confirmed`

## 실행 절차

1. **Data Model + ERD** — 팩의 primary entity와 관계를 도메인 전체에 대해 한 번에 설계한다(엔티티·필드·관계·제약).
2. **API 설계** — endpoint, request/response 스키마, 권한(actor·role)별 접근을 정의한다.
3. **복잡 BL 위임** — `complexity: high` 노트는 **bl-analyst subagent**를 호출해
   decision table·state machine·worked examples를 받는다. (`subagents/bl-analyst.md`)
4. **frontend wiring 계획** — Phase α shell(`shell_ref`)을 기준으로, 어느 컴포넌트에 무엇을
   연결할지(API hook, 상태, 권한 조건부 렌더, 에러 처리)를 명시한다. layout은 건드리지 않는다.
5. 산출을 `/speckit.tasks` 입력으로 넘긴다.

## 입력

```
input/spec-pack/PACK-X/spec.yaml      # scope·actions·acceptance·notes(verbatim·complexity)
model_repo/renders/*.render.html      # 시각 참조
app_repo/specs/PACK-X/spec.yaml       # shell_ref (Phase α 이후)
```

## 산출물

- 도메인 Data Model + ERD
- API 명세 (endpoint·request·response·권한)
- bl-analyst decision table/state machine (complexity:high 항목)
- frontend wiring 계획 (컴포넌트 ↔ API ↔ 상태 매핑)

## 경계

- 설계까지만. 코드 구현은 `/speckit.implement`.
- bl-analyst 미해결 decision이 남으면 Gate B 통과 불가.
