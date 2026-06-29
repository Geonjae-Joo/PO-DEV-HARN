---
name: ds-bootstrap
description: >
  ① PREREQUISITE 레이어 스킬. 사용자가 오픈소스 디자인 시스템(DS) 이름을 알려주면,
  웹서치로 설치법·컴포넌트 목록·토큰 API·SCSS 커스터마이징 방법을 조사하고,
  ds-source/ 에 해당 DS 를 설치한다. 이후 일반 웹 개발에서 자주 쓰는 컴포넌트와
  토큰(colors, typography, spacing, elevation, radius, transition, z-index)을 구성하고,
  앱 실행에만 필요한 파일(main, App, index.html)과 불필요한 의존성을 제거한다.
  harness 파이프라인이 요구하는 두 산출물—src/tokens.css(CSS 변수 단일 소스)와
  ds-allowlist.md(DS 폐쇄 계약)—을 항상 생성한다.
  사용자가 "디자인 시스템 설치", "[DS명] 써줘", "ds-source 구성", "design system 세팅"처럼
  말하면 이 스킬을 즉시 사용해야 한다.
when_to_use: >
  오픈소스 UI 라이브러리/DS(Vuetify, Ant Design Vue, shadcn-vue, Element Plus,
  Naive UI, PrimeVue, Bootstrap Vue, Radix Vue, Headless UI 등 무엇이든)를
  ds-source 에 처음 설치하거나 재구성할 때. 사용자가 DS 이름을 언급하며
  "설치", "구성", "세팅", "써줘", "추가해줘"를 말하면 즉시 트리거.
allowed-tools: Read Write Edit Bash WebSearch
layer: ① PREREQUISITE
stage: 준비 (프로젝트 1회)
owner: 개발 리드/운영자
version: 1.0.0
tags: [design-system, ds-source, tokens, allowlist, install, prerequisite]
inputs:
  - 사용자가 지정한 DS 이름 (예: "Ant Design Vue", "shadcn-vue", "Element Plus")
  - foundation/design-system/ds-source/ 디렉토리 (비어있거나 기존 상태)
outputs:
  - foundation/design-system/ds-source/package.json
  - foundation/design-system/ds-source/vite.config.js  (필요시)
  - foundation/design-system/ds-source/src/tokens.css
  - foundation/design-system/ds-source/src/plugins/<ds>.<ext>
  - foundation/design-system/ds-source/src/styles/settings.scss  (DS가 SCSS 지원 시)
  - foundation/design-system/ds-allowlist.md
spine-ids: []
---

# Skill: ds-bootstrap

## 역할

사용자가 **DS 이름 하나**를 알려주면, 그 DS 에 대해 아무것도 모르는 상태에서 출발해
harness 파이프라인이 소비 가능한 형태로 ds-source/ 를 완성한다.

ds-source/ 가 생산해야 하는 두 가지 핵심 산출물:

| 산출물 | 소비자 | 역할 |
|---|---|---|
| `src/tokens.css` | `harness-core/render/tokens.py` | CSS 변수 스캔 → 카탈로그·렌더 엔진 토큰 주입 |
| `../ds-allowlist.md` | PO-DEV-CHAT lint L1 | DS 폐쇄 계약 — 허용 집합 밖 컴포넌트 차단 |

나머지 파일(`plugins/`, `styles/`)은 **프론트엔드(③)가 DS를 소비하기 위한 진입점**이다.

**이 스킬은 실행 앱을 만들지 않는다.** `main.js / App.vue / index.html` 은 존재해서는 안 된다.

---

## 실행 순서

### Phase 1 — DS 리서치 (병렬 웹서치)

사용자가 알려준 DS 이름으로 **병렬로** 다음을 검색한다. 검색 결과에서 직접 내용을 읽어 정확한 값을 추출한다 — 추측하지 않는다.

```
① "<DS명> npm install vite setup 2024"
   추출: 패키지명, 최신 안정 버전, peer deps, Vite 플러그인(있다면)
   
② "<DS명> all components list"
   추출: 전체 컴포넌트 이름 목록 (ds-allowlist.md 작성에 사용)
   
③ "<DS명> theme customization design tokens colors"
   추출: 색상 토큰 재정의 API (JS 객체? CSS 변수? SCSS 변수?)
   
④ "<DS명> scss variable override customization"
   추출: SCSS 변수 API 유무 및 configFile 설정 방법
   
⑤ "<DS명> component props defaults global configuration"
   추출: 컴포넌트 기본 props 일괄 설정 방법 (있는 DS와 없는 DS가 다름)
```

리서치 완료 후 다음을 결정한다:

| 항목 | 내용 |
|---|---|
| npm 패키지명 | (예: `vuetify`, `ant-design-vue`, `element-plus`) |
| 최신 버전 | (예: `^3.8.8`) |
| 필요한 peer deps | (예: `vue@^3.5`, `@vitejs/plugin-vue`) |
| Vite 플러그인 | 있음/없음, 패키지명 |
| 토큰 정의 방식 | JS 테마 객체 / CSS 변수 오버라이드 / SCSS 변수 |
| SCSS 지원 여부 | 있음/없음 |
| 컴포넌트 defaults API | 있음(어떤 방식)/없음 |
| 기본 브랜드 컬러 | primary hex값 등 |

---

### Phase 2 — package.json + 설치

리서치 결과를 토대로 `package.json` 을 작성·갱신하고 `npm install` 을 실행한다.

**포함:**
```json
{
  "dependencies": {
    "<ds-package>": "^<latest-version>",
    "vue": "^3.5.x"                    // DS가 Vue 기반일 때
  },
  "devDependencies": {
    "vite": "^<latest>",
    "@vitejs/plugin-vue": "^<latest>",  // Vue 기반 DS
    "<vite-plugin>": "^<latest>",       // DS 전용 Vite 플러그인이 있다면
    "sass-embedded": "^<latest>"        // DS가 SCSS 지원 시
  },
  "scripts": {
    "build:css": "vite build --mode css"
  }
}
```

**제거:** `roboto-fontface`, 앱 실행 전용 패키지(폰트 CDN, 앱 라우터 등).

**`vite.config.js`** 작성:
- DS 전용 Vite 플러그인이 있으면 등록
- SCSS `configFile` 설정 (DS가 지원 시)
- DS 가 Vite 플러그인이 없는 CSS-only 방식이면 간단한 config 작성

```bash
cd <ds-source 경로>
npm install
```

---

### Phase 3 — `src/tokens.css` 작성

> **이 파일이 가장 중요하다.** `tokens.py` 는 `ds-source/**/*.css` 를 스캔해 `:root {}` 의 `--name: value;` 를 파싱한다.

**분류 기준 (tokens.py 내부 로직):**

| 분류 | 조건 |
|---|---|
| `color` | `#hex`, `rgb()`, `rgba()`, `hsl()`, `oklch()` 등 |
| `font` | 이름에 `font` 포함 OR 값이 `system-ui`·폰트명 |
| `dimension` | 값에 `px`/`rem`/`em`/`%` 포함, 이름에 `space`·`size`·`radius`·`spacing` |
| `other` | 나머지 (그림자, 전환, z-index) |

**필수 카테고리 (30개 이상):**

```css
:root {
  /* Color · Brand — DS 리서치에서 추출한 기본 컬러 사용 */
  --color-primary:         #...;
  --color-primary-light:   #...;
  --color-primary-dark:    #...;
  --color-secondary:       #...;

  /* Color · Semantic */
  --color-success:  #...;
  --color-info:     #...;
  --color-warning:  #...;
  --color-error:    #...;

  /* Color · Surface */
  --color-background:    #...;
  --color-surface:       #...;
  --color-border:        #...;
  --color-text-primary:  #...;
  --color-text-secondary:#...;

  /* Typography */
  --font-sans:      '...', system-ui, sans-serif;
  --font-mono:      ui-monospace, Consolas, monospace;
  --font-size-sm:   0.875rem;
  --font-size-base: 1rem;
  --font-size-lg:   1.125rem;
  --font-size-xl:   1.25rem;
  --font-size-2xl:  1.5rem;

  /* Spacing (4px 배수) */
  --spacing-1:  4px;
  --spacing-2:  8px;
  --spacing-3:  12px;
  --spacing-4:  16px;
  --spacing-6:  24px;
  --spacing-8:  32px;
  --spacing-12: 48px;
  --spacing-16: 64px;

  /* Border Radius */
  --radius-sm:   2px;
  --radius-base: 4px;
  --radius-lg:   8px;
  --radius-full: 9999px;

  /* Elevation */
  --elevation-1: 0 1px 3px rgba(0,0,0,.12), 0 1px 2px rgba(0,0,0,.24);
  --elevation-2: 0 3px 6px rgba(0,0,0,.15), 0 2px 4px rgba(0,0,0,.12);
  --elevation-3: 0 10px 20px rgba(0,0,0,.15), 0 3px 6px rgba(0,0,0,.10);

  /* Transition */
  --transition-fast: 100ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);

  /* Z-Index */
  --z-index-dropdown: 1000;
  --z-index-dialog:   1050;
  --z-index-toast:    1060;
  --z-index-tooltip:  1070;
}
```

> **색상값은 반드시 리서치에서 가져온다.** DS 의 실제 기본 브랜드 컬러를 사용한다.
> DS 가 자체 CSS 변수를 이미 정의하면 해당 값을 그대로 맵핑한다.

---

### Phase 4 — `src/plugins/<ds>.<ext>` 작성

DS 인스턴스를 생성·export 하는 진입점 파일. 형식은 DS 에 따라 다르다:

**리서치 결과에 맞게 선택:**

```
Vue 기반 DS (Vuetify, Ant Design Vue, Element Plus, Naive UI, PrimeVue)
  → src/plugins/<ds>.js 또는 src/plugins/<ds>.ts
  → createVuetify({...}) / createPinia({...}) 등 DS API 사용

React 기반 DS (shadcn, MUI, Radix UI)
  → src/lib/utils.ts + src/styles/globals.css 또는 theme 객체

CSS-only DS (Bootstrap, Tailwind, UnoCSS)
  → src/styles/main.scss 또는 src/styles/globals.css
  → 토큰 변수 정의 + import
```

**포함 내용 (DS 가 지원하는 만큼):**
1. **테마/토큰 맵핑** — `tokens.css` 의 색상값을 DS 테마 API에 연결 (light/dark)
2. **컴포넌트 defaults** — 아래 카테고리 커버:
   - 폼: 입력·선택·다중선택·텍스트영역·체크박스·스위치·라디오·폼 래퍼
   - 액션: 버튼
   - 레이아웃: 카드
   - 오버레이: 다이얼로그·메뉴/드롭다운·툴팁·토스트
   - 데이터: 테이블·목록·페이지네이션
   - 피드백: 알림·뱃지·칩·진행바·스켈레톤
   - 네비게이션: 헤더·탭·브레드크럼
3. **아이콘** — 가능하면 트리쉐이킹 방식 (SVG > 웹폰트)

---

### Phase 5 — `src/styles/settings.scss` 작성

DS 가 SCSS 변수를 지원하면 오버라이드 파일을 작성하고, `vite.config.js` 의 `configFile` 에 연결한다.
지원하지 않으면 비워두거나 최소 주석 파일을 생성한다.

공통으로 다루는 변수:
- 폰트·폰트 크기
- 기본 border-radius
- 간격 단위(spacer)
- 그리드 브레이크포인트 (지원 DS)

---

### Phase 6 — 보일러플레이트 제거

**삭제 대상 (있을 경우):**
```
src/main.js / src/main.ts
src/App.vue / src/App.tsx / src/App.jsx
index.html
src/components/   (샘플·데모 컴포넌트 폴더)
public/           (앱 전용 정적 파일)
```

PowerShell 또는 Bash 로 삭제:
```bash
# 예시
rm -f src/main.js src/App.vue index.html
rm -rf src/components public
```
없으면 무시한다.

---

### Phase 7 — `ds-allowlist.md` 작성

위치: `foundation/design-system/ds-allowlist.md` (ds-source/ 의 **한 단계 위**)

#### 형식 규칙

파서(`load_allowlist_full`)가 사용하는 정규식:
- `^##\s+(\w+)` → 컴포넌트명 추출 (`\w+` = 단어 문자만, 공백·하이픈 없이 PascalCase)
- `- **description**: ...`
- `- **props**: propName: type, ...`
- `- **usage**: ...`
- `- **states**: default, hover, ...` ← 선택

```markdown
# DS Allowlist — 허용 컴포넌트 집합 (가드레일)

> **이 파일은 DS 폐쇄를 강제하는 계약/가드레일이다.** [표준 전문]

## Button
- **description**: 액션을 실행하는 기본 버튼
- **props**: label: string, variant: string, disabled: boolean, loading: boolean
- **usage**: 폼 제출, 액션 트리거, 다이얼로그 확인/취소
- **states**: default, hover, focus, active, disabled, loading
```

#### 어떤 컴포넌트를 등록하는가

리서치에서 수집한 DS 의 실제 컴포넌트 목록을 기준으로,
**일반 웹 개발에서 자주 쓰이는 것** 우선 선별한다. 최소 25개.

| 카테고리 | 등록 대상 예시 |
|---|---|
| 폼 입력 | Button, TextField(또는 Input), Select, Textarea, Checkbox, Switch, RadioGroup, Form |
| 레이아웃 | Card, Divider |
| 오버레이 | Dialog, Menu(또는 Dropdown), Tooltip, Snackbar(또는 Toast), NavigationDrawer(또는 Drawer) |
| 데이터 표시 | DataTable(또는 Table), Pagination |
| 피드백 | Alert, Badge, Chip(또는 Tag), ProgressLinear, Skeleton |
| 네비게이션 | AppBar(또는 Header), Tabs, Breadcrumbs |
| 날짜 | DatePicker |
| 합성 | FilterBar (TextField+Select+Button 합성 패턴) |

> 컴포넌트명은 DS 의 실제 이름을 따른다 (예: Vuetify → `Button` 또는 `VBtn`, Element Plus → `ElButton`).
> `\w+` 패턴이어야 하므로 공백·하이픈은 제거하고 PascalCase 로 작성한다.

---

### Phase 8 — DS Plugin ↔ ds-allowlist.md Sync 확인 및 수정

Phase 7까지 완료한 뒤, DS 플러그인 파일과 ds-allowlist.md 가 **일치하는지 대조**하고 불일치를 수정한다.

#### 8.1 양쪽 목록 추출

**DS 플러그인 파일(`src/plugins/<ds>.*`)에서:**
- `defaults` 객체(또는 상응하는 컴포넌트 설정)의 키 목록 추출
- 예: `{ VBtn, VTextField, VSelect, VCombobox, ... }` → `[VBtn, VTextField, ...]`

**ds-allowlist.md에서:**
- `^## (\w+)` 정규식으로 헤딩 목록 추출
- 예: `[Button, TextField, Select, ...]`

#### 8.2 매핑 테이블 작성

DS 컴포넌트명과 allowlist 이름의 대응 표를 직접 만든다.
예(Vuetify 기준):

```
VBtn               → Button
VTextField         → TextField
VSelect            → Select
VAutocomplete      → Autocomplete
VCombobox          → Combobox
VTextarea          → Textarea
VCheckbox          → Checkbox
VSwitch            → Switch
VRadioGroup        → RadioGroup      ← VRadio (서브)와 구분
VFileInput         → FileInput
VSlider            → Slider
VRangeSlider       → RangeSlider
VForm              → Form
VCard              → Card
VDialog            → Dialog
VBottomSheet       → BottomSheet
VNavigationDrawer  → NavigationDrawer
VDataTable         → DataTable
VTable             → Table
VList              → List
VAlert             → Alert
VBadge             → Badge
VChip              → Chip
VProgressLinear    → ProgressLinear
VProgressCircular  → ProgressCircular
VSkeletonLoader    → Skeleton
VAppBar            → AppBar
VTabs              → Tabs
VBreadcrumbs       → Breadcrumbs
VPagination        → Pagination
VDatePicker        → DatePicker
VTimePicker        → TimePicker
VAvatar            → Avatar
VDivider           → Divider
VExpansionPanels   → Expansion
VSnackbar          → Snackbar
VTooltip           → Tooltip
VMenu              → Menu
```

#### 8.3 불일치 분류

매핑 테이블을 기반으로 세 가지로 분류한다:

| 케이스 | 조건 | 처리 |
|---|---|---|
| **A. allowlist 추가 필요** | plugin에 있고 allowlist에 없는 *독립 컴포넌트* | ds-allowlist.md에 `## Name` 항목 추가 |
| **B. plugin defaults 추가 필요** | allowlist에 있고 plugin에 없는 컴포넌트 | plugin 파일에 defaults 키 추가 |
| **C. 서브컴포넌트/유틸 (skip)** | plugin에 있지만 독립 사용 불가 항목 | 무시 (allowlist 등록 불필요) |

**C 판정 기준 — 다음에 해당하면 서브컴포넌트로 분류:**
- 다른 컴포넌트의 하위 슬롯에서만 동작 (VListItem, VTab, VExpansionPanel 등)
- 레이아웃 프리미티브 (VContainer, VSheet)
- 아이콘·이미지 래퍼 (VIcon, VImg)
- 복합 컴포넌트의 서버 변형 (VDataTableServer → DataTable로 통합)
- 버튼 그룹/FAB (VBtnGroup, VFab → Button으로 표현 가능)

#### 8.4 수정 실행

**A 케이스 → ds-allowlist.md 에 항목 추가:**

```markdown
## Combobox
- **description**: 직접 입력과 선택을 동시에 지원하는 콤보 입력 컴포넌트
- **props**: items: array, modelValue: string, label: string, multiple: boolean, disabled: boolean
- **usage**: 자유 입력 가능한 선택 필드, 검색 제안, 태그 입력
- **states**: default, focus, disabled, error
```

**B 케이스 → plugin defaults 에 키 추가:**

```js
VRadioGroup: {
  density: 'comfortable',
  color:   'primary',
},
```

#### 8.5 수정 후 재확인

수정 완료 후 대조를 한 번 더 실행해 A·B 케이스가 **0건**인지 확인한다.
C 케이스(서브컴포넌트)는 잔여 항목으로 남아도 정상이다.

---

## 검증 체크리스트

```
[ ] src/tokens.css  존재, :root {} 블록 내 CSS 변수 ≥ 30개
[ ] src/plugins/<ds>.<ext>  존재, DS 인스턴스 export 포함
[ ] ds-allowlist.md  존재, ## HeadingName 항목 ≥ 25개 (각 description·props·usage 포함)
[ ] src/main.js / src/App.vue / index.html  없음
[ ] npm install  오류 없음
[ ] ds-allowlist.md 헤딩이 정규식 \w+ 통과 (공백·하이픈 없음)
[ ] Sync 확인: plugin 독립 컴포넌트 ↔ allowlist 헤딩 A·B 케이스 0건
```

---

## 규칙

- DS 공식 문서·npm 에서 확인한 값만 사용한다. 추측한 컴포넌트명·컬러값은 사용하지 않는다.
- 색상 토큰은 DS 기본 브랜드 컬러로 채운다.
- `ds-allowlist.md` 헤딩은 파서 정규식 `\w+` 를 통과하는 PascalCase 로만 작성한다.
- ds-source 는 참조 라이브러리이다 — 앱 실행 파일을 만들거나 남기지 않는다.
- 모든 응답·산출물 설명은 한국어로 작성한다.
