---
name: design-page-builder
description: >
  ① PREREQUISITE 레이어 스킬. design-guide.md의 허용 집합(DS 컴포넌트)만 조합해
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
  - output/foundation/design-system/design-guide.md   # 허용 집합 원본
outputs:
  - output/foundation/design-pages/DP-*.yaml           # 빈 페이지 템플릿
supporting-files:
  - scripts/design-page-lint.py                        # 전용 출력 검증기 (스킬이 직접 호출)
spine-ids: [DP-]
---

# Skill: design-page-builder

## 역할

①의 준비 단계에서, 사용자가 `input/design-system/`에 투입한 기존 DS와 그 허용 목록인
`design-guide.md`를 토대로 **빈 페이지 템플릿(design page)** 을 만든다.
PO(②)에게 백지 캔버스를 주지 않기 위해, archetype별 레이아웃 골격을 상류에서 못 박는 것이 목적이다.

**경계:** 이 스킬은 *템플릿(레이아웃 골격)* 까지만 만든다. 실제 화면 정의(SCR-*)는 ②,
구현 코드는 ③의 책임이다. DS 집합 밖 컴포넌트는 절대 발명하지 않는다(ds-closure).

---

## 실행 순서

1. **허용 집합 로드** — `design-guide.md`의 `## <컴포넌트명>` 헤딩에서 사용 가능한 DS 컴포넌트 목록을 읽는다.
   (`ds-guide-validate.py` 훅이 형식·필수 필드를 먼저 보장한 상태여야 한다.)
2. **archetype 결정** — 만들 페이지 유형을 정한다: `main`(전체 페이지), `popup`(모달/팝업) 등.
3. **슬롯 구성** — 페이지를 region/slot으로 나누고(header, content, header-actions …),
   각 슬롯에 허용 집합 안의 DS 컴포넌트만 배치한다. 데이터·이벤트는 넣지 않는다(빈 골격).
4. **스파인 ID 부여** — 템플릿 최상단에 `id: DP-<NAME>` 를 부여한다 (예: `DP-MAIN`, `DP-POPUP`).
5. **저장** — `output/foundation/design-pages/DP-*.yaml`로 저장한다.
6. **검증(필수)** — 저장 직후 Bash로 전용 린터를 직접 호출한다:

   ```bash
   python skills/design-page-builder/scripts/design-page-lint.py
   ```

   - DS 폐쇄 위반(허용 집합 밖 컴포넌트) → error → 수정 후 재실행.
   - `DP-*` 스파인 ID 누락/형식 오류 → error.

---

## 규칙 (Rules)

- 모든 응답·산출물은 한국어로 작성한다.
- DS 허용 집합 밖의 컴포넌트를 **발명하지 않는다** (`rules/ds-closure.md`).
- 모든 템플릿은 `DP-` 스파인 ID를 가진다 (`rules/spine-ids.md`).
- 템플릿은 **빈 골격** 이다 — 실제 데이터·이벤트·비즈니스 로직을 넣지 않는다.
- 검증을 통과(lint error 0)하지 못한 템플릿은 산출로 간주하지 않는다.

---

## 출력 형식

`output/foundation/design-pages/` 아래 `DP-<NAME>.yaml` 파일.
각 파일은 `id`(DP-*) + 슬롯별 DS 컴포넌트 배치를 담는 레이아웃 골격이다.
최소 1세트(`DP-MAIN` + `DP-POPUP`)를 산출하는 것이 ① DoD 기준이다.
