---
name: coding-style
description: >
  ③ AI-WEB-DEV 레이어 스킬. ①의 tech-stack.md가 정한 백엔드·프론트엔드 스택의 코딩 컨벤션
  — 패키지/폴더 구조, 네이밍, 예외 처리, 레이어 분리 — 을 정의한다. 아래 본문은 현재 스택 선택
  (백엔드 Spring Boot / 프론트엔드 React+Vite+TS+Tailwind+shadcn/ui)의 예시이며, ①이 다른 스택을
  정했으면 그 스택 컨벤션으로 대체한다. speckit.implement로 코드를 작성·리뷰하거나 "코딩 컨벤션",
  "패키지 구조", "네이밍", "예외 처리"를 언급할 때 사용.
when_to_use: backend·frontend 코드 작성/리뷰, 패키지 구조·네이밍·예외 처리 결정 시.
allowed-tools: Read Write Edit
layer: 03-AI-WEB-DEV
phase: [Phase 0, Phase β, Phase γ]
version: 1.0.0
owner: 개발자 (VSCode + Claude Code)
tags: [coding-style, spring-boot, react, typescript, convention]
references:
  # tech-stack.md는 ①의 프로젝트 결정(규칙 아님)으로, 핸드오프 시 foundation으로 번들된다.
  # 원본: foundation/decisions/tech-stack.md
  - foundation/decisions/tech-stack.md
  - ../../rules/commit-convention.md
---

# Skill: coding-style

## 역할

`app_repo` 전체에서 일관된 코드 스타일을 강제한다. **스택은 ①의 tech-stack.md가 단일 출처**이며 고정값이 아니다.
그 스택 위에서 패키지 구조·네이밍·예외 처리 패턴을 통일해, code-reviewer subagent가 기계적으로 점검할 수 있게 한다.

> 아래 Backend/Frontend 절은 **현재 스택 선택(Spring Boot / React)** 기준의 예시다.
> ①이 다른 스택(예: NestJS·FastAPI·Go / Vue·Svelte·Angular)을 정했으면, 그 스택의 레이어 분리·네이밍·예외 처리 컨벤션으로 같은 골격을 채운다.

---

## Backend — 예시: Spring Boot

- **레이어 분리**: `controller → service → repository` 단방향. 도메인 단위 패키지(`com.app.<domain>`).
- **네이밍**: 클래스 `PascalCase`, 메서드/필드 `camelCase`, 상수 `UPPER_SNAKE`, 엔티티 `<Domain>Entity`.
- **DTO 경계**: controller는 DTO만 주고받는다. 엔티티를 외부로 직접 노출하지 않는다.
- **예외 처리**: 도메인 예외 → `@ControllerAdvice` 전역 핸들러에서 표준 에러 응답으로 변환. 빈 catch 금지.
- **트랜잭션**: 쓰기 서비스 메서드에 `@Transactional`. 읽기는 `readOnly = true`.

---

## Frontend — 예시: React + Vite + TypeScript + Tailwind + shadcn/ui

- **폴더 구조**: `src/pages/<Screen>/`(shell + components), `src/api/`, `src/hooks/`, `src/router/`.
- **네이밍**: 컴포넌트 파일·심볼 `PascalCase`, hook `useXxx`, 타입 `PascalCase`.
- **타입**: `any` 금지. API 응답/요청은 명시 타입. props 인터페이스 명시.
- **스타일**: Tailwind 유틸 + shadcn/ui + design token. 임의 색·간격 하드코딩 금지(design-system-usage 참조).
- **상태/데이터**: API 호출은 `src/hooks`의 데이터 hook으로 격리. 컴포넌트는 표현에 집중.
- **에러 처리**: 사용자 노출 에러는 표준 토스트/배너 패턴. 콘솔 무시 금지.

---

## 규칙 (Rules)

- 식별자는 영어, 주석/문서는 한국어 허용.
- 한 파일 한 책임. layout 구조(Phase α shell)는 wiring 단계에서 바꾸지 않는다.
- 커밋은 스파인 ID 포함(`.claude/rules/commit-convention.md`).
