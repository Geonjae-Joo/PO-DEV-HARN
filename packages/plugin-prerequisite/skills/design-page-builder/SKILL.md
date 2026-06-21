---
name: design-page-builder
description: >
  ① PREREQUISITE 레이어 스킬. ds-allowlist.md의 허용 집합(DS 컴포넌트)만 조합해
  빈 페이지 템플릿(DP-MAIN, DP-POPUP 등)을 생성하고 각 템플릿에 스파인 ID(DP-*)를 부여한다.
  DS 밖 컴포넌트 발명은 금지. 생성 직후 design-page-lint.py로 DS 폐쇄·ID를 검증한다.
  운영자가 "디자인 페이지 만들기", "페이지 템플릿 생성", "DP 추가"를 요청하거나
  ②에 넘길 design page 골격이 필요할 때 사용.
when_to_use: 페이지 템플릿(DP-*) 생성·추가, DS 조합 레이아웃 골격이 필요할 때.
allowed-tools: Read Write Edit Bash
layer: 01-PREREQUISITE
stage: 준비 (프로젝트 1회)
owner: 개발 리드/운영자
version: 1.0.0
tags: [design-page, design-system, ds-closure, spine-id, foundation]
inputs:
  - foundation/design-system/ds-allowlist.md   # 허용 집합 원본
outputs:
  - foundation/design-pages/DP-*.yaml           # 빈 페이지 템플릿
supporting-files:
  - scripts/design-page-lint.py                        # 전용 출력 검증기 (스킬이 직접 호출)
spine-ids: [DP-]
---

# Skill: design-page-builder

## 역할

①의 준비 단계에서, 사용자가 `foundation/design-system/ds-source/`에 투입한 기존 DS와 그 허용 목록인
`foundation/design-system/ds-allowlist.md`를 토대로 **빈 페이지 템플릿(design page)** 을 만든다.
PO(②)에게 백지 캔버스를 주지 않기 위해, archetype별 레이아웃 골격을 상류에서 못 박는 것이 목적이다.

**경계:** 이 스킬은 *템플릿(레이아웃 골격)* 까지만 만든다. 실제 화면 정의(SCR-*)는 ②,
구현 코드는 ③의 책임이다. DS 집합 밖 컴포넌트는 절대 발명하지 않는다(ds-closure).

---

## 실행 순서

1. **허용 집합 로드** — `ds-allowlist.md`의 `## <컴포넌트명>` 헤딩에서 사용 가능한 DS 컴포넌트 목록을 읽는다.
   (`ds-guide-validate.py` 훅이 형식·필수 필드를 먼저 보장한 상태여야 한다.)
2. **archetype 결정** — 만들 페이지 유형을 정한다: `main`(전체 페이지), `popup`(모달/팝업) 등.
3. **캔버스 모델 구성 (ADR-002 D3)** — 페이지를 슬롯으로 나누되 각 슬롯을 두 종류로 구분한다:
   - **locked**(`editable: false`, `locks: [DS...]`): ①이 컴포넌트까지 확정하는 고정 구성(Header·Breadcrumb·Footer 등). SCR은 이를 읽기전용 참조로 상속한다.
   - **editable**(`editable: true`, `grid_columns`, `overflow`): PO/AI가 채우는 빈 캔버스.
   또한 `canvas.grid`(columns·gap·max_width)와 `canvas.breakpoints`(lg/md/sm)를 선언한다(ADR 결정 1: 12/8/4). locked 슬롯의 `locks`·`components.ref`는 허용 집합 안의 DS만. 데이터·이벤트는 넣지 않는다(빈 골격).
4. **스파인 ID·버전** — 최상단에 `id: DP-<NAME>` + `version: N`을 부여한다(인스턴스화 `from_template` 핀이 버전을 참조).
5. **저장** — `foundation/design-pages/DP-*.yaml`로 저장한다.
6. **검증(필수)** — 저장 직후 Bash로 전용 린터를 직접 호출한다. **프로젝트 루트(`projects/<id>/`)에서 실행**해야 `foundation/` 경로가 맞는다(다른 cwd면 `--root <project>` 지정):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/design-page-builder/scripts/design-page-lint.py" --root projects/<id>
   ```

   - DS 폐쇄 위반(허용 집합 밖 컴포넌트/locks) → error → 수정 후 재실행.
   - `DP-*` 스파인 ID 누락/형식 오류, canvas/slots 모델 오류 → error.
7. **DP 미리보기 렌더(결정론적)** — 검증 통과 후 엔진으로 DP 골격을 렌더해 PO가 본다(locked=실제 컴포넌트, editable=그리드 오버레이+경계):

   ```bash
   python "${HARNESS_CORE}/render/render_designpage.py" --root projects/<id>
   # 출력: foundation/design-pages/renders/DP-*.html
   ```

> 레거시 평면 `slots: [header, content, ...]` 형식도 계속 유효하다(엔진/린터가 모두 editable로 간주). 신규 페이지는 캔버스 모델 권장.

8. **DS 카탈로그 생성 (ADR-002 D4)** — DP 골격과 별개로, PO가 이름으로 디자인을 지시할 근거가 되는 DS 카탈로그(대시보드)를 생성한다. 토큰은 **현재 design-system 폴더 내용**(`ds-source`의 CSS 변수)에서 추출하고 컴포넌트는 `ds-allowlist.md`에서 읽는다:

   ```bash
   python "${HARNESS_CORE}/render/render_catalog.py" --root projects/<id>
   # 출력: foundation/design-system/catalog/index.html (색상·타이포·치수 토큰 + 컴포넌트 갤러리(표준 상태) + 사용 가이드)
   ```

   - 카탈로그의 컴포넌트명·토큰명 = screen model `source.ref`·토큰명과 **동일** → PO가 이름으로 지목하면 AI가 곧장 model 매핑. ②에서 챗봇 읽기전용 패널로 노출 예정.
   - 컴포넌트별 표시 상태는 `ds-allowlist.md`의 선택 `- **states**:` 선언을 따르고, 없으면 종류 기반 기본 상태셋을 추정한다(표준 집합: default·hover·focus·active·disabled·loading·error·selected·read-only·empty).

---

## 규칙 (Rules)

- 모든 응답·산출물은 한국어로 작성한다.
- DS 허용 집합 밖의 컴포넌트를 **발명하지 않는다** (`harness-core/rules/ds-closure.md`).
- 모든 템플릿은 `DP-` 스파인 ID를 가진다 (`harness-core/rules/spine-ids.md`).
- 템플릿은 **빈 골격** 이다 — 실제 데이터·이벤트·비즈니스 로직을 넣지 않는다.
- 검증을 통과(lint error 0)하지 못한 템플릿은 산출로 간주하지 않는다.

---

## 출력 형식

`foundation/design-pages/` 아래 `DP-<NAME>.yaml` 파일.
각 파일은 `id`(DP-*) + 슬롯별 DS 컴포넌트 배치를 담는 레이아웃 골격이다.
최소 1세트(`DP-MAIN` + `DP-POPUP`)를 산출하는 것이 ① DoD 기준이다.
