# 첫 Design Page 만들기 가이드 (DP-MAIN)

> ds-allowlist.md(허용 컴포넌트 29개)가 검증 통과한 상태에서, **첫 번째 디자인 페이지**를 만드는 방법을 단계별로 설명합니다.
> 디자인 페이지를 처음 만들어 보는 분 기준으로, "무엇을·왜·어떻게"를 모두 적었습니다.

---

## 0. 시작 전 상태 확인

이 가이드는 아래가 끝난 다음 단계입니다.

- ✅ `foundation/design-system/ds-source/` 에 shadcn 컴포넌트 소스 29개
- ✅ `foundation/design-system/ds-allowlist.md` 에 컴포넌트 29개 매니페스트 (검증 통과)

지금부터 만들 것:

- 🎯 `foundation/design-pages/DP-MAIN.yaml` — 첫 디자인 페이지 (전체 화면용 골격)

---

## 1. 개념: 디자인 페이지(Design Page)가 뭔가요?

앞서 만든 **ds-allowlist.md**가 "쓸 수 있는 부품 목록"이라면,
**디자인 페이지(DP)**는 그 부품들을 **"화면 어디에 배치할지 미리 정해둔 빈 틀(레이아웃 골격)"** 입니다.

비유하자면:

- **ds-allowlist.md** = 레고 부품 상자 (어떤 블록이 있는지)
- **DP-\*.yaml** = 조립 설명서의 "기본 뼈대" (머리·몸통·다리 자리를 잡아둔 것)
- **화면(SCR-\*, ②단계)** = 그 뼈대에 실제 데이터·동작을 채운 완성품

### 왜 빈 틀을 미리 만드나요?

다음 단계(②)에서 화면을 설계하는 사람(PO)에게 **백지를 주지 않기 위해서**입니다. "주문 목록 화면을 만들자"고 할 때, 매번 "헤더는 어디 두지? 버튼은 어디?"를 고민하지 않도록, **상류에서 레이아웃 규칙을 못 박아 두는 것**이죠. 이렇게 하면 모든 목록 화면이 같은 구조를 갖게 됩니다.

### 중요한 경계 (이건 넣지 마세요)

디자인 페이지는 **빈 골격**입니다. 다음은 절대 넣지 않습니다.

- ❌ 실제 데이터 (예: 주문 목록 내용)
- ❌ 이벤트·동작 (예: "클릭하면 상세로 이동")
- ❌ 비즈니스 로직

이런 건 모두 ②(화면 모델), ③(구현)의 책임입니다. DP는 **"어떤 부품이 어느 슬롯에 들어간다"** 까지만 정합니다.

---

## 2. 두 가지 핵심 개념: archetype과 slot

DP를 만들려면 두 단어만 이해하면 됩니다.

### archetype (원형) — "이 페이지는 어떤 종류인가"

화면의 큰 유형입니다. 이 프로젝트에서 쓰는 값:

| archetype | 설명 | 예시 화면 |
|---|---|---|
| `main` | 전체 페이지 (목록·상세·폼·대시보드의 공통 뼈대) | 주문 목록, 상품 상세 |
| `popup` | 모달/팝업 | 삭제 확인, 간단 입력 |

첫 DP는 가장 많이 쓰이는 `main` 으로 만듭니다.

### slot (슬롯) — "페이지를 나눈 자리"

페이지를 위치별 영역으로 나눈 것입니다. 각 슬롯에 부품을 배치합니다.
`main` 페이지의 표준 슬롯 구성을 아래처럼 잡겠습니다.

```
┌─────────────────────────────────────────────┐
│ header            [ header-actions ]         │   ← 제목 영역 + 우측 액션 버튼
├─────────────────────────────────────────────┤
│                                              │
│ content                                      │   ← 메인 영역 (필터/표/폼 등)
│                                              │
├─────────────────────────────────────────────┤
│ footer                                       │   ← 하단 (페이지네이션/요약 등)
└─────────────────────────────────────────────┘
```

> 💡 이 슬롯 이름(`header`, `header-actions`, `content`, `footer`)은 ②의 화면 모델에서 그대로 참조됩니다. 화면 모델 예시를 보면 `template: { page: DP-MAIN, slots_used: [content, header-actions] }` 처럼 **DP의 슬롯명을 그대로 가져다 씁니다.** 그래서 슬롯 이름을 명확하게 정하는 게 중요합니다.

---

## 3. DP 파일이 지켜야 하는 규칙 (검증기가 강제)

저장하면 `design-page-lint.py` 가 아래를 검사합니다. 어기면 ERROR로 막힙니다.

1. **`id` 필수** — `DP-` 로 시작하는 대문자 ID (예: `DP-MAIN`). 형식: `DP-` + 영대문자/숫자, 하이픈으로 단어 연결.
2. **`slots` 명시** — 슬롯 목록이 있어야 함 (없으면 경고).
3. **`source.ref` 는 닫힌 집합 안에서만** — `layout[]` 모든 아이템의 `source.ref` 가 ds-allowlist.md의 29개 이름 중 하나여야 함. 밖이면 **DS 폐쇄 위반 ERROR**. (`position.slot` 도 위에서 선언한 슬롯 id 중 하나여야 함.)
4. **raw HTML 금지** — `<div>`, `<span>` 같은 태그를 직접 쓰면 ERROR. 부품은 오직 DS 컴포넌트 `source.ref` 로만.
5. **데이터·이벤트 없음** — 빈 골격 유지(editable 슬롯의 시작 디자인도 컴포넌트 배치까지만, 실데이터·동작은 ②에서).

> 사용 가능한 ref 목록(우리 ds-allowlist.md 기준, 29개): `Button`, `Input`, `Select`, `Table`, `Dialog`, `Card`, `Badge`, `Tabs`, `Checkbox`, `DropdownMenu`, `Form`, `Label`, `Sonner`, `Calendar`, `Popover`, `DataTable`, `FilterBar`, `DatePicker`, `Header`, `NavMenu`, `Avatar`, `Separator`, `Tooltip`, `Skeleton`, `Switch`, `Textarea`, `Alert`, `Breadcrumb`, `Sheet`

---

## 4. Step 1 — 무엇을 배치할지 종이에 먼저 그려보기

코드를 쓰기 전에 "main 페이지의 기본 뼈대에 어떤 부품을 둘까"를 정합니다. 업무용 목록 화면을 기준으로 가장 흔한 조합은:

- `header-actions` 슬롯 → **Button** (예: "새로 만들기", "내보내기" 같은 우측 상단 액션 자리)
- `content` 슬롯 → **FilterBar** (상단 필터 영역) + **DataTable** (메인 데이터 표)

> ⚠️ 여기서 "내보내기 버튼"이라는 **구체적 의미**까지 정하면 안 됩니다. DP는 "여기에 Button이 하나 들어간다"까지만. 그 버튼이 무엇을 하는지는 ②에서 정합니다.

---

## 5. Step 2 — DP-MAIN.yaml 작성하기

파일을 아래 위치에 만듭니다.

```
foundation/design-pages/DP-MAIN.yaml
```

내용:

```yaml
schema_version: 2
id: DP-MAIN
version: 1
archetype: main
description: 목록·상세·폼 화면이 공통으로 사용하는 전체 페이지 기본 골격
slots:
  - { id: header,         editable: false, locks: [Header] }   # 고정 → 참조 상속
  - { id: header-actions, editable: true,  grid_columns: 12 }  # 시작 디자인 → 복사 시딩
  - { id: content,        editable: true,  grid_columns: 12 }
  - { id: footer,         editable: false, locks: [Separator] }
layout:                                                         # ②의 화면 모델과 같은 layout 스키마
  - id: DPC-MAIN.actionBtn
    source: { kind: ds, ref: Button }
    position: { slot: header-actions, base: { col_start: 1, col_span: full, row: 1 } }
    meta: { label: 우측 상단 주요 액션 자리 }
  - id: DPC-MAIN.filterbar
    source: { kind: ds, ref: FilterBar }
    position: { slot: content, base: { col_start: 1, col_span: full, row: 1 } }
    meta: { label: 목록 검색/필터 영역 }
  - id: DPC-MAIN.table
    source: { kind: ds, ref: DataTable }
    position: { slot: content, base: { col_start: 1, col_span: full, row: 2 } }
    meta: { label: 메인 데이터 표 }
```

### 각 줄이 무슨 뜻인지

- `schema_version: 2` — ②의 화면 모델과 **같은 스키마**임을 표시(복사해서 시작하므로 통일).
- `id: DP-MAIN` — 이 페이지의 고유 ID(스파인 ID). ②에서 이 이름으로 페이지를 가리킵니다.
- `archetype: main` — 전체 페이지 유형.
- `slots:` — 영역 목록. 각 슬롯은 `editable: false`(고정→참조 상속) 또는 `editable: true`(시작 디자인→복사 시딩)로 구분.
- `layout:` — 각 슬롯에 배치할 부품(②의 `layout`과 동일 형태). `source.ref` 는 반드시 허용 목록 안의 이름, `position.slot` 은 위 슬롯 id 중 하나.
- `meta.label` — 사람이 읽는 메모(선택). 다음 단계 작업자에게 의도를 전달합니다.

> 💡 **왜 layout 형태인가:** ②가 화면을 시작할 때 이 DP를 **복사**합니다. editable 슬롯의 `actionBtn`·`filterbar`·`table`은 새 화면의 `CMP-<SCR>.*`로 복사되어 **첫 화면이 이 DP와 똑같이** 보이고, locked 슬롯(`header`)은 DP를 참조만 합니다. 그래서 DP와 SCR이 같은 스키마를 써야 합니다.

---

## 6. Step 3 — 검증하기

저장 후 프로젝트 루트에서 린터를 돌립니다.

```bash
python packages/plugin-prerequisite/skills/design-page-builder/scripts/design-page-lint.py
```

성공 시 출력:

```
✓ design page 1개 검사: ['DP-MAIN.yaml']
✓ design-page lint 통과 (경고 N개)
```

이 메시지가 나오면 첫 디자인 페이지 완성입니다. 🎉

### 에러가 나면

| 메시지 | 원인 | 해결 |
|---|---|---|
| `DS 폐쇄 위반: 'XXX'` | `ref` 이름이 허용 목록 밖 | 오타 확인, 또는 ds-allowlist.md에 없는 부품 → 11장(이전 가이드) 절차로 정식 추가 |
| `id='...' DP-* 형식이 아닙니다` | id 형식 오류 | `DP-MAIN` 처럼 대문자+하이픈 |
| `raw HTML 직접 작성 금지` | yaml에 `<태그>` 가 들어감 | DS 컴포넌트 ref 로만 구성 |
| `'slots' 정의 없음` (경고) | slots 누락 | slots 목록 추가 |

---

## 7. Step 4 — design-page-builder 스킬에 맡기는 방법 (권장)

위 형식을 직접 손으로 써도 되지만, 이 작업은 원래 **`design-page-builder` 스킬**이 담당합니다. 형식을 이해했으니 이제 스킬에게 맡기면 더 안전하고 빠릅니다. 예를 들어 이렇게 요청하면 됩니다.

> "ds-allowlist.md의 허용 집합만 써서 DP-MAIN(main 아키타입, 슬롯 header/header-actions/content/footer) 템플릿을 만들어줘. 만든 뒤 design-page-lint.py로 검증까지 해줘."

스킬은 ① 허용 집합을 로드하고 → ② 슬롯을 구성하고 → ③ `DP-` ID를 부여하고 → ④ 저장 후 린터를 자동 호출합니다. 직접 작성한 결과와 스킬 결과를 비교해 보면 형식 감을 빠르게 익힐 수 있습니다.

---

## 8. Step 5 — 다음 디자인 페이지: DP-POPUP

이 프로젝트의 완료 기준(DoD)은 최소 **DP-MAIN + DP-POPUP** 한 세트입니다. DP-MAIN을 만들었으니 같은 방법으로 팝업용 골격을 하나 더 만듭니다.

`foundation/design-pages/DP-POPUP.yaml`:

```yaml
schema_version: 2
id: DP-POPUP
version: 1
archetype: popup
description: 확인·간단 입력용 모달 팝업 기본 골격
slots:
  - { id: dialog-frame,  editable: false, locks: [Dialog] }   # 팝업 컨테이너(고정)
  - { id: dialog-body,   editable: true,  grid_columns: 12 }  # 입력 영역(시작 디자인)
  - { id: dialog-footer, editable: true,  grid_columns: 12 }  # 확인/취소 버튼 자리
layout:
  - id: DPC-POPUP.frame
    source: { kind: ds, ref: Dialog }
    position: { slot: dialog-frame, base: { col_start: 1, col_span: full, row: 1 } }
    meta: { label: 모달 컨테이너 }
  - id: DPC-POPUP.input
    source: { kind: ds, ref: Input }
    position: { slot: dialog-body, base: { col_start: 1, col_span: full, row: 1 } }
    meta: { label: 입력 필드 자리 }
  - id: DPC-POPUP.confirmBtn
    source: { kind: ds, ref: Button }
    position: { slot: dialog-footer, base: { col_start: 1, col_span: full, row: 1 } }
    meta: { label: 확인/취소 버튼 자리 }
```

저장 후 다시 린터를 돌리면 두 페이지를 함께 검사합니다.

```bash
python packages/plugin-prerequisite/skills/design-page-builder/scripts/design-page-lint.py
# ✓ design page 2개 검사: ['DP-MAIN.yaml', 'DP-POPUP.yaml']
```

둘 다 통과하면 ① 단계의 디자인 페이지 산출 요건을 충족한 것입니다.

---

## 9. 이게 ② 단계와 어떻게 연결되나요?

만든 DP가 다음 단계에서 어떻게 쓰이는지 알아두면 "왜 이렇게 만드는지"가 분명해집니다.

②(PO-DEV-CHAT)에서 실제 화면 모델(`SCR-*.yaml`)을 만들 때, 화면은 **어떤 DP 위에 세워질지**를 명시합니다.

```yaml
screen:
  id: SCR-ORDER-LIST
  archetype: list
  template:
    page: DP-MAIN              # ← 우리가 만든 디자인 페이지를 가리킴
    slots_used: [content, header-actions]   # ← DP-MAIN의 슬롯 중 사용할 것
layout:
  - id: CMP-ORDER-LIST.filterbar
    source: { kind: ds, ref: FilterBar }    # ← ds-allowlist.md 허용 목록의 부품
    position: { slot: content, order: 1 }    # ← DP-MAIN의 슬롯에 배치
```

즉, ②의 화면은 (1) **우리 DP의 슬롯**에 (2) **우리 ds-allowlist.md의 부품**을 배치합니다. 두 가지 모두 ①에서 우리가 정한 범위 안에서만 가능하고, 벗어나면 ②의 저장 단계 lint에서 막힙니다. **그래서 ①을 잘 만들면 그 뒤가 자동으로 규칙을 지키게 됩니다.**

게다가 ②는 화면을 **백지에서 쓰지 않고 이 DP를 복사해서 시작**합니다. editable 슬롯에 둔 부품(FilterBar·DataTable 등)은 새 화면의 `CMP-<SCR>.*`로 그대로 복사되고, locked 슬롯(header)은 DP를 참조만 합니다. **첫 화면이 이 DP와 똑같이 보이는 것**이 목표이므로, editable 슬롯에 "비어 보이지 않을 표준 시작 디자인"을 담아 두는 게 좋습니다. (자세한 동작: `screen-model-schema-v2.md` §7.)

---

## 10. 마무리 체크리스트

- [ ] `foundation/design-pages/DP-MAIN.yaml` 생성
- [ ] `id` 가 `DP-MAIN`, `archetype: main`
- [ ] `slots` 목록 명시
- [ ] 모든 `ref` 가 ds-allowlist.md 29개 안에 있음
- [ ] raw HTML 태그 없음, 데이터·이벤트 없음
- [ ] `design-page-lint.py` **통과**
- [ ] (DoD) `DP-POPUP.yaml` 도 동일하게 작성·통과

여기까지 하면 ①(PREREQUISITE) 단계의 디자인 기반(DS + 디자인 페이지)이 완성됩니다. 다음은 ②에서 실제 화면 모델을 만들 차례입니다.

---

### 참고 파일

- 디자인 페이지 스킬: `packages/plugin-prerequisite/skills/design-page-builder/SKILL.md`
- 검증기: `packages/plugin-prerequisite/skills/design-page-builder/scripts/design-page-lint.py`
- DS 폐쇄 규칙: `packages/harness-core/rules/ds-closure.md`
- 화면 모델 스키마(②에서 DP를 어떻게 쓰는지): `packages/harness-core/rules/screen-model-schema-v2.md`
- 허용 컴포넌트 목록: `foundation/design-system/ds-allowlist.md`
