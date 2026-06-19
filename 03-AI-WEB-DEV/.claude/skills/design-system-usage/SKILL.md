---
name: design-system-usage
description: >
  ③ AI-WEB-DEV 레이어 스킬. ①의 design-system(DS 컴포넌트 + design token)과
  design-pages(DP-*)를 ①의 tech-stack.md가 정한 프론트엔드 프레임워크(예: React) 코드로
  구현하는 방법을 안내한다. screen model의 layout[]·position·props를 DS 컴포넌트로 매핑하고,
  design token만 참조해 스타일을 적용한다(스타일 재작성 금지). Phase α shell 생성과 Phase β
  wiring에서 DS 컴포넌트를 다루거나 "DS 컴포넌트", "design token", "shell 생성"을 언급할 때 사용.
when_to_use: DS 컴포넌트를 프론트엔드 코드로 구현, design token 적용, shell/페이지 컴포넌트 생성 시.
allowed-tools: Read Write Edit
layer: 03-AI-WEB-DEV
phase: [Phase α, Phase β]
version: 1.0.0
owner: 개발자 (VSCode + Claude Code)
tags: [design-system, design-token, react, shell, ds-closure]
inputs:
  - foundation/design-system/        # DS 컴포넌트 + design token
  - foundation/design-pages/          # DP-* 템플릿
  - model_repo/screens/SCR-*.yaml     # layout·position·props 원본
references:
  # 아래 둘은 ①에서 작성되어 핸드오프 시 ③로 번들된다(③ 자체 산출물 아님).
  # ds-closure(불변 규칙)는 .claude/rules/로, tech-stack(프로젝트 결정)은 foundation으로 번들된다.
  - ../../../input/harness/foundation/decisions/tech-stack.md  # 원본: 01-PREREQUISITE/output/foundation/decisions/tech-stack.md
  - ../../rules/ds-closure.md   # 원본: 01-PREREQUISITE/.claude/rules/ds-closure.md (①에서 번들)
spine-ids: [SCR-, CMP-, DP-]
---

# Skill: design-system-usage

## 역할

①이 제공한 **DS 컴포넌트와 design token**을 **①의 tech-stack.md가 정한 프론트엔드 프레임워크**(현재 예시: React)로
구현하는 표준 방법을 정의한다. screen model(②)의 `layout[]`을 화면 컴포넌트로 옮길 때, DS 밖 컴포넌트를 발명하지 않고
스타일을 새로 쓰지 않는 것이 핵심이다.

**경계:** 화면·요구사항의 *정의*는 ②, DS·design token의 *명세*는 ①의 책임이다.
이 스킬은 그 명세를 프론트엔드 코드로 **구현(how)** 할 뿐이다. 아래 예시는 React 기준이며, 다른 프레임워크면 동일 원칙을 그 프레임워크 컴포넌트 모델로 옮긴다.

---

## 매핑 규칙

1. **DS → 프레임워크 컴포넌트** — `layout[].source.kind: ds` 컴포넌트는 DS 패키지의 대응 컴포넌트(예: React 컴포넌트)를 import해 사용한다. 새 컴포넌트를 만들지 않는다(ds-closure).
2. **position → 배치** — `position.slot` + `position.order` + `position.area/span`을 design page(DP-*) 골격 위에 그대로 반영한다.
3. **props → 컴포넌트 props** — screen model의 `props`(예: `{label, variant}`)를 그대로 전달한다.
4. **design token → 스타일** — 색·간격·타이포는 design token만 참조한다. 임의 색상값·인라인 스타일 재작성 금지.
5. **interactive 표시** — `meta.interactive: true` 컴포넌트는 이벤트 핸들러 자리(stub)를 둔다. 실제 wiring은 Phase β.

---

## Phase별 사용

- **Phase α (shell)**: layout만 있는 페이지 컴포넌트 생성. 데이터·API·상태 없음. `onClick={() => {}}` stub + `// TODO [PACK-*]: wire up` 주석.
- **Phase β (wiring)**: shell의 layout은 건드리지 않고 API hook·상태·권한 조건부 렌더만 추가한다.

---

## 규칙 (Rules)

- 모든 산출 코드·주석은 한국어 주석을 허용하되 식별자는 tech-stack 컨벤션을 따른다.
- DS 집합 밖 컴포넌트 발명 금지(`.claude/rules/ds-closure.md`).
- design token 외 스타일 하드코딩 금지.
- shell 파일 상단 주석: `// SCAFFOLD — source: SCR-*.yaml v{version}`.
