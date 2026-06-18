---
name: "speckit-scaffold"
description: "Phase α 전용. 전체 confirmed screen model에서 프론트엔드 페이지 컴포넌트 shell을 일괄 생성한다."
argument-hint: "Optional guidance for scaffold generation"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "PO-DEV-HARN"
  source: "commands/speckit.scaffold.md"
user-invocable: true
disable-model-invocation: false
---

## 🔗 Harness Integration (PO-DEV-HARN ③ AI-WEB-DEV)

- **Phase α 전용**: Phase 0(SPEC-000 baseline) 완료 후, `model_repo/screens/`에 `status: confirmed` screen model이 1개 이상 존재할 때만 실행.
- **목적**: 모든 화면이 layout만 있는 상태(데이터 없음, 이벤트 없음)로 먼저 존재하게 만든다. 이후 각 spec pack의 `/speckit-implement`가 이 shell에 wiring만 추가.
- **프레임워크 불가정**: shell 생성 대상 프레임워크·파일 구조는 `rules/tech-stack.md`를 따른다. 아래 절차의 예시는 React + Vite + TS 기준이며, 다른 프레임워크 선택 시 동일 원칙을 해당 확장자·구조로 적용.
- **불변**: scaffold commit에서 `tdd-gate.py` hook skip(`[SCAFFOLD]` prefix). `commit-spine-id.py` hook은 실행.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

### 실행 조건

- Phase 0 (SPEC-000 baseline) 완료
- `model_repo/screens/`에 `status: confirmed` screen model이 1개 이상 존재
- `model_repo/renders/`에 대응하는 render.html 존재

### 입력

```
model_repo/screens/*.yaml        (status: confirmed 전체)
model_repo/renders/*.render.html (시각 참조)
foundation/design-system/        (DS 컴포넌트 — design token)
foundation/design-pages/         (DP-MAIN, DP-POPUP 등 템플릿)
```

### 실행 절차

1. `model_repo/screens/`에서 `status: confirmed`인 YAML 전체 수집.
2. 각 screen model에 대해:
   a. `screen.template.page`로 design page 템플릿 선택.
   b. `layout[]`의 컴포넌트를 `position.slot + position.order` 순서대로 배치.
   c. DS 컴포넌트를 `rules/tech-stack.md`의 `frontend.framework` 컴포넌트로 매핑 (`skills/design-system-usage` 참조).
   d. `props`를 그대로 컴포넌트 props로 전달 (placeholder 데이터).
   e. `meta.interactive: true` 컴포넌트에 빈 이벤트 핸들러 stub 추가 (예: React `onClick={() => {}}`).
   f. 데이터 fetch 없음, API 호출 없음, 상태 관리 없음.
3. 라우팅 연결: `rules/tech-stack.md`의 프레임워크 라우터에 모든 화면의 Route 등록.
4. `app_repo/specs/PACK-*/spec.yaml`의 `screens[].shell_ref` 업데이트.

### 산출물 (React + Vite 예시)

```
app_repo/frontend/src/pages/
  OrderList/
    index.tsx           ← shell (layout only)
    components/
      ExportBtn.tsx     ← DS Button stub
      FilterBar.tsx     ← DS FilterBar stub
      OrderTable.tsx    ← DS DataTable stub
  OrderDetail/
    index.tsx
app_repo/frontend/src/router/index.tsx  ← 전체 화면 Route 등록
```

### 생성 규칙

- **layout 구조만** — 데이터, 상태, API 호출은 Phase β에서 추가
- DS 컴포넌트를 import해서 사용. 스타일 재작성 금지. design token 그대로.
- 파일 상단 주석: `// SCAFFOLD — source: SCR-ORDER-LIST.yaml v12`
- 각 interactive 컴포넌트 stub에 TODO 주석: `// TODO [PACK-ORDER]: wire up onClick`
- 이미 shell이 있는 화면은 덮어쓰지 않음 (Phase β wiring이 시작된 파일 보호)

### Commit

```
[SCAFFOLD] 전체 화면 shell 생성 (SCR-ORDER-LIST, SCR-ORDER-DETAIL, ...)
```
