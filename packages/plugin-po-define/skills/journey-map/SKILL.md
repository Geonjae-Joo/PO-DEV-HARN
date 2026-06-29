---
name: journey-map
description: >
  여러 화면을 가로지르는 사용자 여정(JRN-*)을 navigate action 집계로 정의한다 — E2E 시나리오의 계약.
  step은 각 화면 action의 acceptance(Gherkin)를 재사용하며, 고립 화면을 탐지하고 (선택) Mermaid 흐름도를 만든다.
  복수 화면이 confirmed된 뒤, 또는 PO가 "전체 흐름", "화면 이동", "사용자 시나리오", "E2E"를 언급할 때 사용.
when_to_use: '"전체 화면 흐름", "처음부터 끝까지 시나리오", "E2E", "화면 흐름도", confirmed 화면이 여러 개 쌓였을 때.'
allowed-tools: Read Write Edit
layer: ② PO-DEV-CHAT
stage: Stage 후반 (복수 SCR confirmed 후)
version: 1.0.0
owner: PO (도메인 전문가)
tags: [journey, e2e, navigation, JRN]
supporting-files: [../../rules/journey-schema.md]
spine-ids: [JRN-]
---

# Skill: journey-map

## 역할

화면 내부가 아니라 **화면 간** 흐름을 다룬다. 각 `SCR-*.yaml`의 `navigate` action을 집계해
end-to-end 사용자 여정 `JRN-*.yaml`을 정의한다. 이것이 ③ Phase γ Playwright E2E의 **시나리오 출처**다.

**경계:** E2E 테스트 코드는 만들지 않는다(③의 몫). 여정 *계약*(어떤 화면·action을 어떤 순서로)만 만든다.
step 검증은 새로 쓰지 않고 각 action의 acceptance(Gherkin)를 재사용한다.

---

## 흐름

```
model_repo/screens/*.yaml (confirmed) 전체 로드
  │
  ▼
1. navigate 간선 추출: 각 action 중 outcome.type: navigate → (from SCR, to SCR) edge
2. 경로 합성: 간선을 이어 의미 있는 end-to-end 경로 후보 생성
3. PO 확정: 후보 제시 → PO가 여정 선택·명명(JRN-{도메인}-{시나리오}) + precondition/postcondition 보충
4. 고립 화면 탐지: 어떤 navigate로도 도달 불가한 SCR- 경고 보고
5. (선택) Mermaid 흐름도 산출 (PO 시각 확인용)
6. journey-schema.md 형식으로 model_repo/journeys/JRN-*.yaml 저장
```

## 질문 가이드

```
Q-JRN-GOAL:   이 흐름에서 사용자가 최종적으로 이루려는 게 뭔가요?
Q-JRN-START:  어떤 상태에서 시작하나요? (로그인 여부, 사전 데이터)
Q-JRN-PATH:   어떤 화면들을 순서대로 거치나요?
Q-JRN-END:    끝났을 때 무엇이 바뀌어 있어야 하나요? (postcondition)
Q-JRN-PRIO:   이 여정은 반드시 깨지면 안 되는 핵심인가요? (E2E 우선순위)
```

## 산출 & 인계

- 산출: `model_repo/journeys/JRN-*.yaml` (journey-schema.md 준수)
- spec-generator가 PACK 발행 시 관련 `JRN-` ref를 포함 → ③ Phase γ가 Playwright(+BDD)로 구현
- 추적: `JRN- → (거치는 SCR/action) → e2e-test → commit`
