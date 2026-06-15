# Command: /speckit.scaffold

## 목적

**Phase α 전용.** 전체 confirmed screen model → 프론트엔드 페이지 컴포넌트 shell 일괄 생성.

모든 화면이 layout만 있는 상태(데이터 없음, 이벤트 없음)로 먼저 존재하게 만든다.
이후 각 spec pack의 speckit.implement가 이 shell에 wiring만 추가한다.

> **프레임워크:** shell 생성 대상 프레임워크·파일 구조는 **①의 tech-stack.md**를 따른다(고정값 아님). 이 문서의 예시·파일 트리는 현재 선택인 **React + Vite + TS**(`.tsx`, `src/pages/`) 기준이며, ①이 다른 프론트엔드(예: Vue→`.vue`, Svelte→`.svelte`)를 정했으면 해당 확장자·구조로 동일 원칙을 적용한다.

## 실행 조건

- Phase 0 (SPEC-000 baseline) 완료 후 실행
- `model_repo/screens/` 안에 `status: confirmed` screen model이 1개 이상 존재
- `model_repo/renders/` 안에 대응하는 render.html 존재

## 입력

```
model_repo/screens/*.yaml       (status: confirmed 전체)
model_repo/renders/*.render.html (시각 참조)
foundation/design-system/       (DS 컴포넌트 — design token)
foundation/design-pages/        (DP-MAIN, DP-POPUP 등 템플릿)
```

## 실행 절차

1. `model_repo/screens/` 에서 `status: confirmed` 인 YAML 전체 수집.
2. 각 screen model에 대해:
   a. `screen.template.page` 로 design page 템플릿 선택.
   b. `layout[]` 의 컴포넌트를 `position.slot + position.order` 순서대로 배치.
   c. DS 컴포넌트를 ①의 `frontend.framework` 컴포넌트로 매핑 (design-system-usage skill 참조).
   d. `props` 를 그대로 컴포넌트 props로 전달 (placeholder 데이터).
   e. `meta.interactive: true` 컴포넌트에 빈 이벤트 핸들러 stub 추가 (프레임워크 관용 표기 — 예: React `onClick={() => {}}`, Vue `@click="() => {}"`).
   f. 데이터 fetch 없음, API 호출 없음, 상태 관리 없음.
3. 라우팅 연결: ①의 프레임워크 라우터(예: React `src/router/`)에 모든 화면의 Route 등록.
4. `app_repo/specs/PACK-*/spec.yaml` 의 `screens[].shell_ref` 업데이트.

## 산출물

> 경로·확장자·디렉터리 규약은 ①의 `frontend.framework`에서 파생한다. 아래는 **React + Vite 선택 시의 예시**다(Vue면 `src/views/*.vue`, Svelte면 `src/routes/*.svelte` 등 동일 원칙).

```
app_repo/frontend/src/pages/          # (예시: React)
  OrderList/
    index.tsx           ← shell (layout only)
    components/
      ExportBtn.tsx     ← DS Button stub
      FilterBar.tsx     ← DS FilterBar stub
      OrderTable.tsx    ← DS DataTable stub
  OrderDetail/
    index.tsx
  ...
app_repo/frontend/src/router/index.tsx  ← 전체 화면 Route 등록
```

## 생성 규칙

- **layout 구조만** — 데이터, 상태, API 호출은 Phase β에서 추가
- DS 컴포넌트를 import해서 사용. 스타일 재작성 금지. design token 그대로.
- 파일 상단 주석: `// SCAFFOLD — source: SCR-ORDER-LIST.yaml v12`
- 각 interactive 컴포넌트 stub에 TODO 주석: `// TODO [PACK-ORDER]: wire up onClick`

## Commit

tdd-gate hook은 scaffold commit에서 skip. commit-spine-id hook 실행.

```
[SCAFFOLD] 전체 화면 shell 생성 (SCR-ORDER-LIST, SCR-ORDER-DETAIL, ...)
```

## 주의

- 이미 shell이 있는 화면은 덮어쓰지 않는다 (Phase β wiring이 시작된 파일 보호).
- 새로 confirmed된 화면이 생기면 해당 화면만 추가로 scaffold한다.
- shell은 Phase β에서 layout 구조를 바꾸지 않는다는 전제 위에서만 의미가 있다.
  layout 변경이 필요한 Change Order가 오면 change-order-policy를 따른다.
