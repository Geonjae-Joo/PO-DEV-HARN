---
name: baseline-guides
description: >
  ③ AI-WEB-DEV 레이어 스킬 (Phase 0 모드 A 산출물의 템플릿/메타 정의).
  공통 기능(로그인·SSO·RBAC·공통 레이아웃 등) 중 "프로젝트마다 변형되는" 기능에 대해
  동작하는 예시 코드블럭 + 적용 패턴을 reference 스킬로 제공한다(전체 구현이 아님).
  Phase 0가 기능별로 이 템플릿에 맞춰 app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md를
  생성하고, Phase β가 도메인 코드 구현 시 로드해 변형 적용한다.
  "baseline 가이드", "모드 A", "권한 조건부 렌더 패턴", "감사 로그 삽입 패턴"을 다룰 때 사용.
when_to_use: Phase 0에서 mode:A 기능 가이드 작성 시, Phase β에서 공통 기능 패턴을 도메인 코드에 적용 시.
allowed-tools: Read Write Edit
layer: ③ AI-WEB-DEV
phase: [Phase 0, Phase β]
delivery-mode: A
runtime-location: app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md
version: 1.0.0
owner: 개발자 (VSCode + Claude Code)
tags: [baseline, mode-a, reference-pattern, common-feature, sso, rbac]
references:
  - ../../../README.md            # Phase 0 전달 모드 A/B 설명
  - baseline-delivery-manifest.yaml
spine-ids: [SPEC-000]
---

# Skill: baseline-guides

## 역할

Phase 0의 공통 기능 전달 **모드 A(가이드 코드블럭)** 의 산출 형식을 정의한다.
"프로젝트마다 변형되는" 공통 기능은 완성 코드를 주입(모드 B)하지 않고, **예시 코드 + 패턴 설명**을
feature별 reference 스킬로 적재한다. Phase β가 도메인 맥락에 맞게 로드·변형해 적용한다.

> 모드 판정 한 줄: **"프로젝트마다 변형되나?"** → 예면 A(이 가이드), 아니면 B(직접 코드 주입).
> 결정은 `baseline-delivery-manifest.yaml`에 기록된다(전체 baseline의 단일 진실원).

**경계:** *무엇이 공통 기능인지(scope)* 는 ①의 SPEC-000이 정한다. *A로 줄지 B로 줄지와 실제 가이드* 는 ③ Phase 0가 만든다.

---

## 생성 구조 (feature 1개당)

각 mode:A 기능은 아래 위치·형식으로 생성한다:

```
app_repo/.claude/skills/baseline-guides/<feature>/
  SKILL.md          # name·description(WHEN 포함) + 적용 패턴 + 예시 코드블럭
  examples/         # (선택) 동작하는 예시 스니펫
```

`<feature>/SKILL.md` 본문 권장 구성:

1. **목적** — 이 공통 기능이 무엇이고 어디에 끼어드는가.
2. **변형 지점** — 프로젝트/도메인마다 달라지는 부분을 명시(예: 권한 조건, 감사 로그 대상).
3. **예시 코드블럭** — 동작하는 패턴 코드(①의 tech-stack.md 스택 기준, 예: Spring Boot / React). 전체 구현이 아닌 참조 패턴.
4. **적용 절차** — Phase β가 도메인 코드에 이식할 때의 단계.

---

## 대표 예시 (mode:A 후보)

- 권한 조건부 렌더 패턴 (RBAC role에 따른 UI/엔드포인트 노출)
- 감사 로그(audit log) 삽입 패턴
- 공통 레이아웃 슬롯에 도메인 위젯 끼우기

> 변형이 불필요한 로그인/SSO 모듈, JWT 필터, RBAC 엔티티 등은 모드 B(직접 코드 주입)로 처리한다 — 이 스킬 대상 아님.

---

## 규칙 (Rules)

- 가이드는 **예시·패턴** 까지만. 완성 코드를 통째로 넣지 않는다(그건 모드 B).
- 모든 mode:A/B 결정과 사유는 `baseline-delivery-manifest.yaml`에 기록한다.
- 생성된 feature 가이드의 description에는 Phase β가 언제 로드해야 하는지(WHEN)를 반드시 포함한다.
