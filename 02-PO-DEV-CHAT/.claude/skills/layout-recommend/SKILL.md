---
name: layout-recommend
description: >
  Stage 1 스킬. PO가 나열한 컴포넌트를 DS에 매핑해 screen model YAML 초안을 생성하고,
  model 변경 시마다 design token 기반 HTML 렌더를 자동 생성한다.
  PO가 "레이아웃", "화면 구성", "컴포넌트 배치"를 언급하거나 새 화면을 시작할 때 사용.
when_to_use: >
  layout 초안 작성, 컴포넌트 위치 수정, 화면 archetype 선택 시.
  "필터를 테이블 위로", "버튼 오른쪽에" 같은 patch 요청도 이 스킬로 처리.
  화면을 처음 그릴 때뿐 아니라 layout 수정 루프 전체를 담당한다.
allowed-tools: Read Write Edit Bash
paths: "model_repo/screens/SCR-*.yaml"
layer: 02-PO-DEV-CHAT
stage: Stage 1
version: 1.0.0
owner: PO (도메인 전문가)
tags: [layout, ds-mapping, screen-model, html-render, ds-closure]
supporting-files: [../../rules/screen-model-schema-v2.md, ../../rules/state-machine.md]
spine-ids: [SCR-, CMP-, DP-]
---

## 책임

두 가지를 수행한다: (1) layout 추천, (2) HTML 렌더링.

---

## 1. Layout 추천

**입력:** PO의 자연어 컴포넌트 나열 + `foundation/design-system/design-guide.md` + `foundation/design-pages/`

**프로세스:**

1. PO 발화에서 컴포넌트 의도 추출
2. `design-guide.md` 허용 목록에서 가장 적합한 DS 컴포넌트 매핑
   - 1:1 대응이 명확하면 바로 매핑
   - 애매하면 후보 2~3개 제시, PO 선택
   - DS 밖 컴포넌트는 절대 발명하지 않음 — 가장 근접한 DS 컴포넌트를 대안 제안
3. 화면 archetype(list/detail/form/dashboard/popup) 판단 → 적합한 design page 템플릿 선택
4. screen model YAML 초안 생성 — `position.slot` / `position.order` / `position.area` / `position.span` 포함
5. 초안 PO에게 제시 → patch 단위 수정 요청 시 반영
6. 저장 시 lint hook 자동 실행

**출력:** `model_repo/screens/SCR-{ID}.yaml`

> 스키마 상세: [screen-model-schema-v2.md](../../rules/screen-model-schema-v2.md)

---

## 2. HTML 렌더링

**트리거:** screen model YAML 저장 후 lint 통과 시 자동 실행

**원칙:**
- DS design token 참조 — 스타일 새로 작성 금지
- `screen.template.page`가 지정한 DP 템플릿(예: DP-MAIN)을 골격으로 사용
- `position.slot` + `position.order`에 따라 컴포넌트 배치
- `props` 그대로 반영 (예: `{label: "엑셀 내보내기", variant: secondary}`)
- `meta.interactive: true`인 컴포넌트는 클릭/입력 영역을 시각적으로 표시 (실제 동작 구현 아님)

**파일 생성 규칙:**
```
model_repo/
  screens/
    SCR-ORDER-LIST.yaml          ← 원본 (편집 대상)
  renders/
    SCR-ORDER-LIST.render.html   ← 파생 뷰 (편집 금지)
```

렌더 파일 상단 필수 주석:
```html
<!-- GENERATED VIEW — source: SCR-ORDER-LIST.yaml v{version} — DO NOT EDIT -->
<!-- Rendered by layout-recommend skill at {timestamp} -->
```

**렌더에 포함:** 컴포넌트 위치·배치·크기(span), DS design token 스타일, props, interactive 컴포넌트 시각 구분, 화면 ID·버전 워터마크

**렌더에 미포함:** 실제 API 연동, 실데이터, action 동작 구현

---

## 주의

- HTML을 직접 편집하면 다음 렌더링 시 덮어씌워진다. 수정은 반드시 YAML을 통해.
- 렌더 결과가 기대와 다르면 `position`·`props`를 조정하고 재저장.
