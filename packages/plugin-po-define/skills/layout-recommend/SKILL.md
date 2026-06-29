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
layer: ② PO-DEV-CHAT
stage: Stage 1
version: 1.0.0
owner: PO (도메인 전문가)
tags: [layout, ds-mapping, screen-model, html-render, ds-closure]
supporting-files: [../../../harness-core/rules/screen-model-schema-v2.md, ../../rules/state-machine.md]
spine-ids: [SCR-, CMP-, DP-]
---

## 책임

세 가지를 수행한다: (0) DP 인스턴스화로 화면 시작, (1) layout 추천, (2) HTML 렌더링(결정론적 엔진 위임).

---

## 0. DP 인스턴스화 — 새 화면 시작 (ADR-002 §6)

PO가 카탈로그/DP 미리보기에서 **design page를 고르면** 그 DP를 인스턴스화해 화면을 시작한다.
화면을 백지에서 쓰지 않고 **DP를 복사해서 시작**한다(스키마 통일 — DP와 SCR은 같은 `layout` 스키마):
- DP의 고정 구성(**locked** 슬롯)은 복제하지 않고 **참조 상속**(단일 출처·드리프트 0).
- DP의 **editable** 슬롯 아이템은 `SCR.layout`으로 **복사 시딩**되어 **첫 렌더가 DP와 동일**(이름·메타 제외).
**DP 원본 YAML은 절대 수정하지 않는다.**

```bash
python "${HARNESS_CORE}/render/instantiate_screen.py" \
  --project <projects/id> --template DP-MAIN \
  --name "상품 목록" --domain PRODUCT --type LIST
```
- `spine_ledger.mint_scr_id`가 `SCR-{DOMAIN}-{TYPE}` 전역 유일 채번.
- 산출: `status: draft`, `layout: [editable seed 복사분]`(CMP-<SCR>.* 재채번, `meta.seeded_from` provenance), `screen.from_template: {page, version}` 핀.
- `link-manifest.yaml`에 DP→SCR 엣지 + seed CMP를 `components`/`next_seq.CMP`에 기록. 이후 1·2 단계에서 seed를 조정·추가.
- (DP에 editable seed가 없으면 `layout: []` 빈 캔버스로 시작 — 기존 동작과 동일.)

---

## 1. Layout 추천

**입력:** PO의 자연어 컴포넌트 나열 + `foundation/design-system/ds-allowlist.md` + `foundation/design-pages/`

**프로세스:**

1. PO 발화에서 컴포넌트 의도 추출
2. `ds-allowlist.md` 허용 목록에서 가장 적합한 DS 컴포넌트 매핑
   - 1:1 대응이 명확하면 바로 매핑
   - 애매하면 후보 2~3개 제시, PO 선택
   - DS 밖 컴포넌트는 절대 발명하지 않음 — 가장 근접한 DS 컴포넌트를 대안 제안
3. 화면 archetype(list/detail/form/dashboard/popup) 판단 → 적합한 design page 템플릿 선택
4. screen model YAML 초안 생성 — `position.slot` + 반응형 정수 좌표 `position.base: {col_start, col_span, row, row_span}` (필요 시 `position.at: {md, sm}` 오버라이드). `col_span` shorthand(full/half/third/quarter) 사용 가능(렌더러가 정수 resolve). **editable 슬롯에만 배치**(locked 슬롯 침범 시 lint L5 차단). 픽셀 좌표·`auto` 금지. 레거시 `{slot, order}`도 허용(엔진 자동 변환)
5. 초안 PO에게 제시 → patch 단위 수정 요청 시 반영
6. YAML 저장 완료 직후 HTML 렌더 실행 (§2 참조):
   ```bash
   python "${HARNESS_CORE}/render/render_screen.py" \
     projects/<id>/model_repo/screens/SCR-<ID>.yaml
   ```
   - 산출: `model_repo/renders/SCR-<ID>.render.html`
   - 실패 시(lint 오류 등) stderr 확인 후 YAML 수정, 성공할 때까지 반복
7. 저장 시 lint hook 자동 실행

**출력:** `model_repo/screens/SCR-{ID}.yaml` + `model_repo/renders/SCR-{ID}.render.html`

> 스키마 상세: [screen-model-schema-v2.md](../../../harness-core/rules/screen-model-schema-v2.md)

---

## 2. HTML 렌더링 — 결정론적 엔진 위임 (ADR-002 D1)

**트리거:** screen model YAML 저장 후 lint 통과 시 자동 실행.
**LLM은 HTML을 직접 쓰지 않는다.** 항상 순수 Python 엔진이 생성한다.

```bash
python "${HARNESS_CORE}/render/render_screen.py" model_repo/screens/SCR-*.yaml
# 결정성 검사: --check (재렌더 후 render_hash 동일성만 확인, 파일 미수정)
```

**계약(엔진이 보장):** 같은 입력 → **바이트 동일** HTML(rendered-at 주석 제외). 인라인 style 금지,
외부 CDN/폰트 금지, 토큰 컴파일 CSS만 `<style>`에. `layout_hash`(전 브레이크포인트 좌표)·
`render_hash`(HTML) 산출 → `pinned_contract`에 동결, ③ Phase α가 재렌더로 위치 계약 재현 검증.

**엔진 동작:**
- `screen.template.page`가 지정한 DP의 canvas(grid·breakpoints·slots locked/editable)를 골격으로 사용
- `position.base`/`at`를 슬롯 grid_columns에 맞춰 정수 좌표로 resolve → CSS 그리드 배치(반응형)
- 오버라이드 미지정 브레이크포인트는 결정론적 자동 강등(full-width 세로 스택)
- `props` 반영, locked 슬롯은 DP 실제 컴포넌트로 그려 맥락 제공
- `meta.interactive`는 시각 구분만 (실제 동작 구현 아님)

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
