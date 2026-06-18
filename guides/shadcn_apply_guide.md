# shadcn/ui를 PO-DEV-HARN의 디자인 시스템으로 적용하기

> 디자인 시스템을 처음 다뤄보는 분을 위한 아주 자세한 단계별 가이드입니다.
> 명령어 하나하나, 파일 하나하나가 "왜 필요한지"를 같이 설명합니다.
> 순서대로 따라오시면 됩니다.

---

## 0. 먼저 개념부터: 디자인 시스템이 뭔가요?

디자인 시스템(Design System, 이하 DS)은 **"이 제품에서 쓸 수 있는 화면 부품(컴포넌트)의 공식 목록과 사용 규칙"** 입니다.
버튼, 입력창, 표(테이블), 팝업 같은 부품을 매번 새로 그리지 않고, **미리 정해둔 한 벌**만 재사용합니다.

왜 중요할까요?

- **일관성** — 모든 화면의 버튼이 똑같이 생깁니다.
- **속도** — 새 화면을 만들 때 부품을 조립만 하면 됩니다.
- **통제** — "이 목록에 없는 부품은 못 쓴다"는 규칙으로 무분별한 변형을 막습니다.

이 마지막 항목이 PO-DEV-HARN에서 가장 중요합니다. 이 프로젝트는 **"DS에 정의된 컴포넌트만 화면에 쓸 수 있다"** 는 규칙(이름하여 **DS 폐쇄, ds-closure**)을 코드로 강제합니다. 그래서 DS를 제대로 세팅하는 게 모든 단계의 출발점입니다.

### shadcn/ui란?

[shadcn/ui](https://ui.shadcn.com)는 React + Tailwind CSS 기반의 컴포넌트 모음입니다. 보통의 라이브러리와 결정적으로 다른 점이 하나 있습니다:

> **shadcn은 npm으로 "설치"하는 게 아니라, 컴포넌트의 소스 코드를 내 프로젝트로 "복사"해 옵니다.**

즉 `Button.tsx`, `Input.tsx` 같은 파일이 **내 레포 안에 직접 들어오고, 내가 소유**합니다. 이게 PO-DEV-HARN과 궁합이 좋은 이유입니다. 이 하니스는 `input/design-system/` 폴더에 "실제 DS 원본을 투입"하는 구조인데, shadcn은 그 원본이 곧 내 코드라서 폴더에 그대로 담기 딱 좋습니다. 또 "내가 복사한 컴포넌트 = 쓸 수 있는 컴포넌트 전부"가 되므로, DS 폐쇄(닫힌 집합)가 저절로 성립합니다.

참고로 shadcn은 unstyled(맨몸)가 아닙니다. 맨몸인 건 그 밑에 깔린 Radix UI이고, shadcn은 그 위에 Tailwind 스타일을 입혀 제공합니다. 복사해 오는 순간 이미 보기 좋은 스타일이 적용돼 있습니다.

---

## 1. 큰 그림: 이 하니스에서 DS가 흘러가는 경로

작업을 시작하기 전에 전체 그림을 머리에 넣어두면 헷갈리지 않습니다.

```
[①  01-PREREQUISITE]  ← 지금 우리가 세팅할 단계
  input/design-system/                 (A) shadcn 원본을 여기에 담는다
        │  (컴포넌트 목록을 옮겨 적는다)
        ▼
  output/foundation/design-system/design-guide.md   (B) 허용 컴포넌트 "매니페스트"
        │  (이 목록만 조합해서)
        ▼
  output/foundation/design-pages/DP-*.yaml          (C) 빈 페이지 골격(템플릿)

[②  02-PO-DEV-CHAT]
  화면 모델(SCR-*.yaml)을 작성. layout 의 ref 는 (B) 목록 안에 있어야만 통과.

[③  03-AI-WEB-DEV]
  app_repo/frontend 에서 실제 구현. 같은 shadcn 컴포넌트를 사용.
  code-reviewer 가 "DS 밖 컴포넌트 / 임의 스타일"을 다시 검사.
```

핵심은 **(B) `design-guide.md`** 입니다. 이 파일이 "허용 목록(single source of truth)"이고, 저장할 때마다 검증기(`ds-guide-validate.py`)가 형식을 자동으로 확인합니다. ②와 ③의 모든 검사가 이 목록을 기준으로 돌아갑니다.

우리가 이 가이드에서 할 일은 순서대로:

1. shadcn 프로젝트를 만들고 컴포넌트를 가져온다 → (A)
2. 가져온 컴포넌트를 `design-guide.md`에 목록으로 옮겨 적는다 → (B)
3. 그 목록만으로 페이지 템플릿 `DP-*.yaml`을 만든다 → (C)
4. 검증기를 돌려 통과를 확인한다
5. ②③에서 같은 컴포넌트를 쓰도록 연결한다

---

## 2. 사전 준비물

작업 전에 아래가 준비돼 있어야 합니다.

- **Node.js 18 이상** — 터미널에서 `node -v` 로 확인하세요. 없으면 [nodejs.org](https://nodejs.org)에서 LTS 버전 설치.
- **터미널(명령 프롬프트/PowerShell)** 사용법 — 폴더 이동(`cd`)과 명령 실행 정도면 충분합니다.
- 이 프로젝트 폴더의 위치: `C:\Users\geonjae.joo\Desktop\DEV\PO-DEV-HARN`

> 💡 이 프로젝트는 한국어로 산출물을 작성하는 게 규칙입니다(design-page-builder 스킬 규칙). 설명·주석도 한국어로 적으면 좋습니다.

---

## 3. Step 1 — shadcn 작업용 프로젝트 만들기

shadcn 컴포넌트는 혼자 떠다닐 수 없고, React 프로젝트 안에 들어가야 합니다. 그래서 먼저 **DS 원본을 담을 작은 프로젝트**를 `input/design-system/` 안에 만듭니다.

> 왜 여기에 만드나요? 하니스의 `01-PREREQUISITE/input/design-system/` 폴더는 "기존 DS 원본을 투입하는 곳"으로 정의돼 있습니다. shadcn은 소스를 내가 소유하므로, 그 소스 자체가 곧 DS 원본입니다.

터미널에서 아래를 실행합니다.

```bash
cd C:\Users\geonjae.joo\Desktop\DEV\PO-DEV-HARN\01-PREREQUISITE\input\design-system

# Vite + React + TypeScript 프로젝트 생성 (가볍고 빠릅니다)
npm create vite@latest ds-source -- --template react-ts
cd ds-source
npm install
```

이제 `input/design-system/ds-source/` 안에 React 프로젝트가 생겼습니다.

> 📌 굳이 동작하는 앱을 만들려는 게 아닙니다. shadcn 컴포넌트 소스를 **담아두고 목록화하기 위한 그릇**입니다. 실제 화면 구현은 ③(`app_repo/frontend`)에서 합니다.

---

## 4. Step 2 — Tailwind CSS 준비

shadcn은 Tailwind CSS로 스타일을 입힙니다. 먼저 Tailwind를 설치합니다.

```bash
npm install tailwindcss @tailwindcss/vite
```

`vite.config.ts` 를 열어 Tailwind 플러그인을 추가합니다.

```ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

`src/index.css` 의 맨 위에 다음 한 줄을 넣습니다.

```css
@import "tailwindcss";
```

> 이 단계는 "스타일 엔진을 켜는" 작업입니다. shadcn 컴포넌트가 사용하는 색·간격·라운드 같은 디자인 토큰이 Tailwind를 통해 적용됩니다.

---

## 5. Step 3 — shadcn 초기화 (`init`)

이제 shadcn을 초기화합니다. 프로젝트 폴더(`ds-source`) 안에서 실행하세요.

```bash
npx shadcn@latest init
```

실행하면 CLI가 몇 가지를 자동으로 처리하고, 한 가지를 물어봅니다.

1. **사전 점검** — 프레임워크(Vite/React)·Tailwind 설정·경로 별칭(import alias)이 올바른지 확인합니다.
2. **기본 색상(base color) 질문** — `Neutral`, `Slate`, `Zinc`, `Stone`, `Gray` 중 하나를 고릅니다. 잘 모르겠으면 `Neutral`을 고르세요. (나중에 바꿀 수 있습니다.)
3. **자동 설정** — `components.json` 파일 생성, 전역 CSS에 디자인 토큰(CSS 변수) 추가, `lib/utils.ts`(클래스 합치는 `cn` 헬퍼) 생성, 필요한 의존성 설치.

끝나면 프로젝트에 `components.json` 이 생깁니다. 이 파일이 "shadcn이 컴포넌트를 어디에 어떤 스타일로 넣을지"를 담은 설정표입니다.

> 💡 `components.json` 은 나중에 ③의 프론트엔드에서 **똑같이 복사**해 쓸 겁니다. 그래야 ①에서 정한 DS와 ③의 구현이 같은 부품·같은 테마를 공유합니다.

---

## 6. Step 4 — 쓸 컴포넌트를 골라서 가져오기 (DS의 "닫힌 집합" 정하기)

이게 디자인 시스템의 핵심 결정입니다. **"우리 제품에서 허용할 부품은 이것들이다"** 를 여기서 확정합니다.

PO-DEV-HARN의 예시 화면들은 전형적인 **업무용 CRUD 화면**(목록·상세·폼·필터·팝업)입니다. 거기에 맞춰 아래 정도를 권장 출발 세트로 가져옵니다.

```bash
npx shadcn@latest add button input select table dialog
npx shadcn@latest add card badge tabs checkbox dropdown-menu
npx shadcn@latest add form label toast calendar popover
```

각 명령은 해당 컴포넌트의 `.tsx` 소스를 `src/components/ui/` 안에 복사해 넣습니다. 한번 열어보세요 — 평범한 React 컴포넌트 코드이고, 이제 **여러분이 소유**합니다.

> 🔑 **여기서 가져온 컴포넌트가 곧 우리 DS의 전부입니다.** 나중에 화면을 만들다 목록에 없는 부품이 필요하면, "그냥 새로 만들기"가 아니라 "DS에 정식으로 추가하는 절차"(이 문서 11장)를 밟아야 합니다. 이것이 DS 폐쇄 원칙입니다.

### 합성 컴포넌트: DataTable, FilterBar

②의 화면 모델 예시를 보면 `DataTable`, `FilterBar` 같은 이름이 등장합니다. shadcn에는 `Table`은 있지만 `DataTable`(정렬·페이지네이션 포함 표)과 `FilterBar`(필터 묶음)는 기본 단품이 아니라 **여러 부품을 조합한 패턴**입니다.

shadcn 공식 문서의 [Data Table](https://ui.shadcn.com/docs/components/data-table) 예시처럼 `Table` + TanStack Table을 묶어 `DataTable.tsx` 를 직접 만들고, `Input`+`Select`+`Button`을 묶어 `FilterBar.tsx` 를 만들어 `src/components/ui/` 에 둡니다. **내가 소유하는 코드이므로 이렇게 합성 컴포넌트를 만들어 DS에 등록하는 것이 정상적인 방법입니다.** 이 둘도 design-guide.md에 똑같이 등록하면 됩니다.

---

## 7. Step 5 — `design-guide.md` 작성하기 (가장 중요한 파일)

이제 가져온 컴포넌트 목록을 하니스가 읽을 수 있는 **매니페스트**로 옮겨 적습니다.
위치는 정확히 여기입니다:

```
01-PREREQUISITE/output/foundation/design-system/design-guide.md
```

### 형식 규칙 (검증기가 강제합니다)

`ds-guide-validate.py` 검증기는 저장할 때마다 아래를 확인합니다. 어기면 저장이 막히거나 경고가 뜹니다.

- 맨 위에 `# Design Guide` 헤더가 있을 것
- 컴포넌트 1개 = `## ComponentName` (H2 헤딩). 이름은 **PascalCase**(예: `Button`, `DataTable`)
- 각 컴포넌트마다 **필수 필드** 두 개를 불릿으로:
  - `- **description**: 설명`
  - `- **props**: 속성 목록`
- `props` 값은 `:` 또는 `,` 를 포함해야 함(예: `label: string, variant: primary|secondary`). 속성이 없으면 `없음` 이라고 적기.
- 선택 필드: `usage`, `variants`, `slots`

### 예시 (그대로 복사해서 다듬으세요)

```markdown
# Design Guide

> 이 프로젝트의 허용 컴포넌트 집합(DS 폐쇄). 여기 없는 컴포넌트는 화면에 쓸 수 없다.
> 기반: shadcn/ui (Radix + Tailwind). 컴포넌트 소스는 input/design-system/ds-source/src/components/ui/.

## Button
- **description**: 액션을 실행하는 기본 버튼
- **props**: label: string, variant: default|secondary|destructive|outline|ghost, disabled: boolean
- **usage**: 폼 제출, 액션 트리거, 다이얼로그 확인/취소

## Input
- **description**: 한 줄 텍스트 입력 필드
- **props**: value: string, placeholder: string, type: text|email|password, disabled: boolean

## Select
- **description**: 드롭다운 단일 선택 컴포넌트
- **props**: options: array, value: string, placeholder: string

## DataTable
- **description**: 정렬·페이지네이션을 지원하는 데이터 테이블(Table + TanStack Table 합성)
- **props**: columns: array, rows: array, sortable: boolean, pageSize: number

## FilterBar
- **description**: 목록 화면 상단의 필터 묶음(Input + Select + Button 합성)
- **props**: fields: array, onApply: function

## Dialog
- **description**: 모달 팝업 컨테이너
- **props**: open: boolean, title: string, onClose: function

## Card
- **description**: 정보를 묶어 보여주는 카드 컨테이너
- **props**: title: string, footer: slot

## Badge
- **description**: 상태·분류를 표시하는 작은 라벨
- **props**: label: string, variant: default|secondary|destructive|outline

## DatePicker
- **description**: 날짜 선택기(Calendar + Popover 합성)
- **props**: value: date, range: boolean, placeholder: string
```

> 위 목록은 "예시"입니다. **6장에서 실제로 가져온 컴포넌트와 정확히 일치**시키세요. design-guide.md에 적었는데 소스가 없거나, 소스는 있는데 목록에 없으면 ②③에서 혼란이 생깁니다.

### 저장 후 검증

저장하면 하니스의 훅이 자동으로 검증기를 돌립니다. 수동으로도 돌려볼 수 있습니다(프로젝트 루트에서):

```bash
python 01-PREREQUISITE/.claude/hooks/ds-guide-validate.py
```

`✓ 컴포넌트 N개 발견` 과 `✓ design-guide.md 검증 통과` 가 나오면 성공입니다. `ERROR:` 가 나오면 그 줄의 안내대로 형식을 고치세요(보통 필수 필드 누락).

---

## 8. Step 6 — 페이지 템플릿 `DP-*.yaml` 만들기

이제 허용 목록만 조합해서 **빈 페이지 골격**을 만듭니다. 이건 PO에게 "백지"가 아니라 "기본 레이아웃이 깔린 틀"을 주기 위한 것입니다.

위치:

```
01-PREREQUISITE/output/foundation/design-pages/DP-MAIN.yaml
01-PREREQUISITE/output/foundation/design-pages/DP-POPUP.yaml
```

이 프로젝트의 완료 기준(DoD)은 최소 `DP-MAIN`(전체 페이지) + `DP-POPUP`(팝업) 한 세트입니다.

### 형식 규칙 (`design-page-lint.py`가 강제)

- `id:` 는 `DP-` 로 시작하는 대문자 ID (예: `DP-MAIN`)
- `slots:` 슬롯 목록을 명시
- 컴포넌트의 `ref:` 는 **반드시 design-guide.md의 컴포넌트 이름 안에** 있어야 함 (밖이면 DS 폐쇄 위반 ERROR)
- **raw HTML 태그 직접 작성 금지** (`<div>` 같은 것 쓰면 ERROR) — 부품은 DS 컴포넌트로만
- 데이터·이벤트·로직은 넣지 않음 (빈 골격이어야 함)

### DP-MAIN.yaml 예시

```yaml
id: DP-MAIN
archetype: main
description: 목록/상세/폼 화면이 공통으로 쓰는 기본 페이지 골격
slots:
  - header
  - header-actions
  - content
  - footer
components:
  - ref: FilterBar
    slot: content
    order: 1
  - ref: DataTable
    slot: content
    order: 2
  - ref: Button
    slot: header-actions
    order: 1
```

### DP-POPUP.yaml 예시

```yaml
id: DP-POPUP
archetype: popup
description: 확인/입력용 모달 팝업 골격
slots:
  - dialog-header
  - dialog-body
  - dialog-footer
components:
  - ref: Dialog
    slot: dialog-body
    order: 1
  - ref: Input
    slot: dialog-body
    order: 2
  - ref: Button
    slot: dialog-footer
    order: 1
```

### 저장 후 검증

```bash
python 01-PREREQUISITE/skills/design-page-builder/scripts/design-page-lint.py
```

`✓ design-page lint 통과` 가 나오면 성공입니다. `DS 폐쇄 위반` 에러가 나오면, 그 `ref` 이름이 design-guide.md에 없는 것이니 (1) 이름 오타인지, (2) 7장 목록에 빠뜨렸는지 확인하세요.

> 💡 이 `DP-*.yaml` 작성은 원래 `design-page-builder` 스킬이 도와주는 작업입니다. 위 형식을 이해했다면 스킬에게 "DP-MAIN, DP-POPUP 템플릿 만들어줘" 라고 맡겨도 됩니다.

---

## 9. Step 7 — 플랫폼 기준선(SPEC-000) 한 줄 연결

`output/foundation/platform-baseline/SPEC-000.md` 는 플랫폼 공통 사항을 적는 파일입니다. DS 관점에서는 최소한 아래를 적어두면 ②③에서 참조하기 좋습니다.

- 사용 DS: **shadcn/ui (Radix + Tailwind v4)**, 기반 색상: (init에서 고른 값)
- 컴포넌트 소스 위치: `input/design-system/ds-source/src/components/ui/`
- 허용 목록 원본: `output/foundation/design-system/design-guide.md`
- 프레임워크: React + TypeScript + Vite

> 이건 "이 프로젝트가 어떤 기술 위에 서 있는지"를 한 곳에 적어두는 메모입니다. 나중에 사람이 바뀌어도 길을 잃지 않게 합니다.

---

## 10. Step 8 — ③ 구현 단계와 연결하기

①에서 DS를 정했으니, ③(`03-AI-WEB-DEV/output/app_repo/frontend`)에서 실제 화면을 만들 때 **같은 컴포넌트를 그대로** 써야 합니다. 방법은 둘 중 하나:

1. **`components.json` 과 `components/ui/` 를 그대로 복사** — ①의 `ds-source`에서 만든 설정·컴포넌트를 frontend로 옮깁니다. 가장 확실하게 "같은 DS"를 보장합니다.
2. **같은 버전으로 다시 `add`** — frontend에서 `npx shadcn@latest init` 후, design-guide.md에 적힌 목록과 **똑같은 컴포넌트만** `add` 합니다.

어느 쪽이든 핵심 규칙은 같습니다:

> **design-guide.md 목록 밖의 컴포넌트를 쓰거나, 컴포넌트에 임의 스타일을 하드코딩하면 안 됩니다.**

③의 `code-reviewer` 서브에이전트가 PR 단계에서 바로 이 두 가지(DS 밖 컴포넌트 사용 / 임의 스타일 하드코딩)를 검사하고, 위반 시 수정 요청을 냅니다. 또한 ②에서 화면 모델(SCR-*.yaml)을 만들 때 `layout[].source.ref` 가 design-guide.md 목록에 없으면 저장 단계 lint에서 막힙니다.

즉, 7장에서 목록을 잘 정해두면 그 뒤 단계들이 자동으로 그 목록을 지키도록 강제됩니다.

---

## 11. 나중에: DS에 새 컴포넌트를 추가하고 싶을 때

화면을 만들다 "이 부품이 DS에 없네?" 싶을 때가 옵니다. 그럴 때 **그냥 새로 만들어 쓰면 안 됩니다.** 아래 절차를 밟습니다(`01-PREREQUISITE/.claude/rules/ds-closure.md`).

1. 먼저 **가장 비슷한 기존 DS 컴포넌트로 대체할 수 있는지** 검토합니다. (예: 커스텀 달력 → `DatePicker` + `FilterBar` 조합)
2. 정말 없으면, 정식으로 추가합니다:
   - shadcn에서 `npx shadcn@latest add <컴포넌트>` 로 소스를 `ds-source` 에 가져오거나, 합성 컴포넌트를 만들어 `components/ui/` 에 둡니다.
   - `design-guide.md` 에 `## NewComponent` 섹션을 추가합니다(필수 필드 포함).
   - `python 01-PREREQUISITE/.claude/hooks/ds-guide-validate.py` 로 형식 통과 확인.
   - `python 01-PREREQUISITE/skills/design-page-builder/scripts/design-page-lint.py` 로 기존 페이지에 영향 없는지 확인.
3. **"목록에 없는 컴포넌트를 그냥 쓰는 것"은 어떤 경우에도 허용되지 않습니다.**

이 절차가 번거로워 보여도, 이게 디자인 시스템이 시간이 지나도 망가지지 않게 지켜주는 안전장치입니다.

---

## 12. 빠른 점검표 (Checklist)

작업을 마쳤다면 아래를 확인하세요.

- [ ] `input/design-system/ds-source/` 에 shadcn 프로젝트가 있고, `components/ui/` 에 컴포넌트 소스가 들어있다
- [ ] `components.json` 이 생성되어 있다
- [ ] `output/foundation/design-system/design-guide.md` 에 `# Design Guide` + 컴포넌트별 `## 이름` + `description`/`props` 가 적혀 있다
- [ ] `ds-guide-validate.py` 가 **통과**한다
- [ ] `output/foundation/design-pages/` 에 `DP-MAIN.yaml`, `DP-POPUP.yaml` 이 있다
- [ ] 각 DP의 `ref` 가 모두 design-guide.md 목록 안에 있다
- [ ] `design-page-lint.py` 가 **통과**한다
- [ ] `SPEC-000.md` 에 사용 DS·소스 위치가 적혀 있다

이 8개가 다 체크되면, ②(화면 모델링)로 넘어갈 준비가 된 것입니다.

---

## 부록: 자주 막히는 지점

| 증상 | 원인 | 해결 |
|---|---|---|
| `필수 필드 누락: 'props'` | design-guide.md 컴포넌트에 `- **props**:` 줄 없음 | 해당 컴포넌트에 props 줄 추가 |
| `props 형식을 확인하세요` 경고 | props 값에 `:` 나 `,` 가 없음 | `label: string` 처럼 콜론/콤마 포함, 없으면 `없음` |
| `DS 폐쇄 위반: 'XXX'` | DP/화면의 ref가 목록에 없음 | 이름 오타 확인, 또는 design-guide.md에 정식 추가(11장) |
| `raw HTML 직접 작성 금지` | DP yaml에 `<div>` 등 태그를 씀 | DS 컴포넌트 ref로만 구성 |
| `id ... DP-* 형식이 아닙니다` | DP 파일의 id가 규칙 위반 | `DP-MAIN` 처럼 대문자 + 하이픈 |
| shadcn `add` 가 안 됨 | `init` 을 안 했거나 Tailwind 미설정 | 3~5장 순서대로 다시 |

---

### 참고 링크

- shadcn/ui 설치 문서: https://ui.shadcn.com/docs/installation
- shadcn CLI 문서: https://ui.shadcn.com/docs/cli
- components.json 설명: https://ui.shadcn.com/docs/components-json
- Data Table 패턴: https://ui.shadcn.com/docs/components/data-table

프로젝트 내부 규칙 파일도 함께 참고하세요: `01-PREREQUISITE/.claude/rules/ds-closure.md`, `01-PREREQUISITE/.claude/skills/design-page-builder/SKILL.md`, `02-PO-DEV-CHAT/.claude/rules/screen-model-schema-v2.md`.
