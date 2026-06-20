# Project Design Guide — 이 프로젝트의 디자인 시스템 안내서

> **이 문서가 "실제 design guide"다** — 사람이 읽는 DS 셋업·사용·컴포넌트 추가 안내서.
> (허용 컴포넌트의 *기계 검증 계약*은 별도 파일 `foundation/design-system/ds-allowlist.md`이다. 그건 가드레일이고, 이 문서는 그 가드레일을 어떻게 채우고 운영하는지 설명한다.)
>
> 대상: 개발 리드/운영자. 시점: 프로젝트당 1회(① 준비 단계).
>
> ⚠️ **DS는 고정값이 아니다.** 이 프로젝트의 DS는 **shadcn/ui**지만, 그 결정의 단일 출처는 `foundation/decisions/tech-stack.md`다. 다른 프로젝트는 MUI·Antd·사내 DS 등으로 이 문서를 통째로 교체한다. 아래 shadcn 절차는 "현재 프로젝트의 구현 방법"일 뿐이며, **"DS를 ds-allowlist.md 허용집합으로 등록한다"는 원칙만 DS 종류와 무관하게 유지된다.**

---

## 0. 개념 — 디자인 시스템과 DS 폐쇄

디자인 시스템(DS)은 **"이 제품에서 쓸 수 있는 화면 부품(컴포넌트)의 공식 목록과 사용 규칙"** 이다. 버튼·입력창·표·팝업 같은 부품을 매번 새로 그리지 않고 미리 정해둔 한 벌만 재사용한다 → **일관성·속도·통제**.

이 하니스에서 가장 중요한 건 **통제**다. PO-DEV-HARN은 **"ds-allowlist.md에 정의된 컴포넌트만 화면에 쓸 수 있다"** 는 규칙(**DS 폐쇄, ds-closure**)을 코드로 강제한다(`.claude/rules/ds-closure.md`). 그래서 DS를 제대로 세팅하고 ds-allowlist.md에 정확히 등록하는 게 모든 단계의 출발점이다.

### 두 파일의 역할 구분 (헷갈리지 말 것)

| 파일 | 성격 | 위치 |
|---|---|---|
| **이 문서** (`project-design-guide.md`) | 사람용 **안내서** — 셋업·사용·추가 절차 | 플러그인 `docs/` (원본 DS 자산은 `foundation/design-system/ds-source/`) |
| **`ds-allowlist.md`** | 기계 검증 **계약/가드레일** — 허용 컴포넌트 집합 | `foundation/design-system/` (②③로 핸드오프) |

### shadcn/ui란? (현재 프로젝트의 DS)

[shadcn/ui](https://ui.shadcn.com)는 React + Tailwind 기반 컴포넌트 모음인데, 보통 라이브러리와 결정적으로 다르다:

> **shadcn은 npm으로 "설치"하지 않고, 컴포넌트 소스 코드(.tsx)를 내 프로젝트로 "복사"해 온다.**

즉 `button.tsx` 같은 파일이 내 레포 안에 직접 들어와 **내가 소유**한다. 이 하니스의 `foundation/design-system/ds-source/` = "기존 DS 원본을 투입하는 곳"과 궁합이 좋고, "내가 복사한 컴포넌트 = 쓸 수 있는 전부"라서 DS 폐쇄가 저절로 성립한다. (맨몸인 건 그 아래 Radix UI이고, shadcn은 그 위에 Tailwind 스타일을 입혀 제공한다.)

---

## 1. 큰 그림 — 이 하니스에서 DS가 흐르는 경로

```
[① 01-PREREQUISITE]  ← 여기서 세팅
  foundation/design-system/ds-source/                   (A) DS 원본(shadcn 소스)을 담는다
        │  (이 문서의 절차로 가져온다)
        ▼
  foundation/design-system/ds-allowlist.md       (B) 허용 컴포넌트 "계약"(가드레일)
        │  (이 집합만 조합해서)
        ▼
  foundation/design-pages/DP-*.yaml              (C) 빈 페이지 골격(템플릿)

[② 02-PO-DEV-CHAT]
  화면 모델(SCR-*.yaml) 작성. layout 의 ref 는 (B) 목록 안에 있어야만 통과.

[③ 03-AI-WEB-DEV]
  app_repo/frontend 에서 실제 구현. 같은 shadcn 컴포넌트 사용.
  code-reviewer 가 "DS 밖 컴포넌트 / 임의 스타일"을 다시 검사.
```

핵심은 **(B) `ds-allowlist.md`** — "허용 목록(single source of truth)"이고, 저장할 때마다 `ds-guide-validate.py`가 형식을 자동 검증한다. ②③의 모든 검사가 이 목록을 기준으로 돈다.

---

## 2. 사전 준비물

- **Node.js 18+** — `node -v` 로 확인(없으면 [nodejs.org](https://nodejs.org) LTS).
- **터미널** — 폴더 이동(`cd`)·명령 실행 정도.
- 산출물·주석은 **한국어**로 작성(프로젝트 규칙).

---

## 3. Step 1 — shadcn 작업용 프로젝트 만들기

shadcn 컴포넌트는 React 프로젝트 안에 들어가야 하므로, **DS 원본을 담을 작은 프로젝트**를 `foundation/design-system/ds-source/` 로 만든다. (하니스가 이 폴더를 "기존 DS 원본 투입처"로 정의하고, shadcn 소스는 내가 소유하므로 그 자체가 DS 원본이 된다.)

```bash
cd foundation/design-system
npm create vite@latest ds-source -- --template react-ts
cd ds-source
npm install
```

> 📌 동작하는 앱을 만들려는 게 아니라, shadcn 소스를 **담아두고 목록화할 그릇**이다. 실제 구현은 ③(`app_repo/frontend`)에서 한다.

---

## 4. Step 2 — Tailwind CSS 준비

```bash
npm install tailwindcss @tailwindcss/vite
```

`vite.config.ts`에 플러그인과 `@` alias 등록:

```ts
import path from "path"
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
})
```

`src/index.css` 최상단:

```css
@import "tailwindcss";
```

---

## 5. Step 3 — shadcn 초기화 (`init`)

```bash
npx shadcn@latest init
```

CLI가 프레임워크·Tailwind·경로 별칭을 점검하고, **기본 색상(base color)** 을 묻는다(모르면 `Neutral`). 끝나면 `components.json`(어디에 어떤 스타일로 넣을지 설정), 전역 CSS의 디자인 토큰(CSS 변수), `lib/utils.ts`(`cn` 헬퍼)가 생긴다.

> 💡 `components.json` 은 ③ 프론트엔드에서 **똑같이 복사**해 쓴다 → ①의 DS와 ③ 구현이 같은 부품·테마를 공유.

### design token (CSS custom properties)

디자이너가 준 토큰을 `src/index.css`의 `:root`에 변수로 박고 Tailwind v4 `@theme`로 매핑한다. **색·간격·타이포는 토큰만 참조**하고 컴포넌트에 hex/px를 하드코딩하지 않는다(`tech-stack.md` 원칙).

---

## 6. Step 4 — 쓸 컴포넌트를 골라 가져오기 (닫힌 집합 결정)

DS의 핵심 결정 = **"우리 제품에서 허용할 부품"** 확정. 업무용 CRUD 화면(목록·상세·폼·필터·팝업) 기준 권장 출발 세트:

```bash
npx shadcn@latest add button input select table dialog
npx shadcn@latest add card badge tabs checkbox dropdown-menu
npx shadcn@latest add form label sonner calendar popover
```

각 명령이 `.tsx` 소스를 `src/components/ui/`에 복사한다. **여기서 가져온 컴포넌트가 곧 DS의 전부**다.

### 합성 컴포넌트 (DataTable, FilterBar, Header, NavMenu …)

shadcn 단품에 없는 패턴은 **여러 부품을 조합한 합성 컴포넌트**로 직접 만들어 `src/components/ui/`에 두고 ds-allowlist.md에 똑같이 등록한다. 예:
- `DataTable` = `Table` + TanStack Table, `FilterBar` = `Input`+`Select`+`Button`
- `Header` = 브랜드 + `NavMenu` + actions, `NavMenu` = `Button(ghost)` 묶음

> **내가 소유하는 코드이므로 합성 컴포넌트를 만들어 DS에 등록하는 것이 정상적인 방법이다.** CLI에 없는 컴포넌트는 합성만 손코딩한다(아래 8장 참조).

---

## 7. Step 5 — `ds-allowlist.md` 작성 (가장 중요한 파일)

가져온 컴포넌트 목록을 하니스가 읽는 **계약(매니페스트)** 으로 옮겨 적는다. 위치는 정확히:

```
foundation/design-system/ds-allowlist.md
```

### 형식 규칙 (검증기가 강제 — 매우 strict)

`ds-guide-validate.py`는 저장 시 아래를 확인한다. **세 lint 모두 `## 헤딩`을 컴포넌트로 간주**하므로, 튜토리얼·설명 같은 산문 `##` 헤딩을 넣으면 "컴포넌트"로 오인돼 검증이 깨진다. → 이 파일엔 **컴포넌트 섹션만** 둔다(설명은 이 문서에).

- 맨 위 `# DS Allowlist` 헤더
- 컴포넌트 1개 = `## ComponentName` (PascalCase)
- 컴포넌트마다 **필수 필드**: `- **description**: …`, `- **props**: …`
- `props` 값은 `:` 또는 `,` 포함(없으면 `없음`). 선택 필드: `usage`, `variants`, `slots`

### 예시

```markdown
# DS Allowlist — 허용 컴포넌트 집합 (가드레일)

> 이 파일은 가이드가 아니라 DS 폐쇄를 강제하는 계약이다. DS 정체성·절차는 project-design-guide.md 참조.

## Button
- **description**: 액션을 실행하는 기본 버튼
- **props**: label: string, variant: default|secondary|destructive|outline|ghost|link, size: default|sm|lg|icon, disabled: boolean
- **usage**: 폼 제출, 액션 트리거, 다이얼로그 확인/취소

## DataTable
- **description**: 정렬·페이지네이션을 지원하는 데이터 테이블 (Table + TanStack Table 합성)
- **props**: columns: array, rows: array, sortable: boolean, pageSize: number
```

### 저장 후 검증

```bash
# Windows 콘솔은 PYTHONUTF8=1 권장(✓ 문자 출력)
PYTHONUTF8=1 python packages/plugin-prerequisite/hooks/ds-guide-validate.py
```

`✓ 컴포넌트 N개 발견` + `✓ ds-allowlist.md 검증 통과` 가 나오면 성공. `ERROR:`는 보통 필수 필드 누락.

---

## 8. 새 컴포넌트를 DS에 추가할 때 (절차 — 손코딩 금지)

화면을 만들다 "이 부품이 DS에 없네?" 싶을 때, **그냥 새로 만들어 쓰면 안 된다.**

1. **가장 비슷한 기존 DS 컴포넌트로 대체 가능한지** 먼저 검토(예: 커스텀 달력 → `DatePicker`).
2. 정말 없으면 정식 추가:
   - **CLI로 공식 소스를 가져온다** — `ds-source/`에서 `npx shadcn@latest add <comp> --overwrite --yes`.
     > ⚠️ **소스를 기억으로 손코딩하지 말 것.** 손코딩본은 실제 shadcn 최신본과 드리프트한다(예: avatar의 size·AvatarBadge·AvatarGroup 누락). CLI가 정식 소스 + 의존성을 정확히 가져온다.
     > CLI에 없는 **합성 컴포넌트(Header/NavMenu 등)만** 손코딩한다.
   - `ds-allowlist.md`에 `## NewComponent` 섹션 추가(필수 필드 포함).
   - `PYTHONUTF8=1 python packages/plugin-prerequisite/hooks/ds-guide-validate.py` → 형식 통과 확인.
   - `PYTHONUTF8=1 python packages/plugin-prerequisite/skills/design-page-builder/scripts/design-page-lint.py` → 기존 DP 영향 없는지 확인.
3. **"목록에 없는 컴포넌트를 그냥 쓰는 것"은 어떤 경우에도 허용되지 않는다.**

> 🐛 **CLI 함정:** `node_modules` 미설치 상태로 `add`를 돌리면 alias가 안 풀려 파일이 `src/components/ui/`가 아니라 **리터럴 `@/components/ui/`** 폴더에 써진다. 이때는 `@/components/ui/*` 를 `src/components/ui/`로 옮기고 `@` 폴더를 삭제한다.

---

## 9. Step 6 — 페이지 템플릿 `DP-*.yaml`

ds-allowlist.md 허용 집합만 조합해 **빈 페이지 골격**을 만든다(PO에게 백지 대신 기본 틀 제공). `design-page-builder` 스킬에게 맡기면 된다 — 상세는 `guides/first_design_page_guide.md` 참조. DoD 최소 세트: `DP-MAIN`(전체 페이지) + `DP-POPUP`(팝업).

---

## 10. Step 7 — ③ 구현 단계와 연결

①에서 정한 DS를 ③(`app_repo/frontend`)에서 **그대로** 쓴다:
1. `components.json` + `components/ui/`를 frontend로 **복사**(가장 확실), 또는
2. frontend에서 같은 목록만 다시 `add`.

어느 쪽이든 규칙은 같다: **ds-allowlist.md 목록 밖 컴포넌트 사용·임의 스타일 하드코딩 금지.** ③의 `code-reviewer`가 PR에서, ②의 `on-save-lint-L1-L4.py`가 저장 시 이를 강제한다.

---

## 11. 체크리스트 (DoD)

- [ ] `foundation/design-system/ds-source/`에 shadcn 프로젝트 + `components/ui/` 소스
- [ ] `components.json` 생성
- [ ] design token을 CSS 변수로 정의하고 Tailwind에 매핑
- [ ] `foundation/design-system/ds-allowlist.md`에 `# DS Allowlist` + 컴포넌트별 `## 이름` + `description`/`props`
- [ ] `ds-guide-validate.py` **통과**
- [ ] `foundation/design-pages/`에 `DP-MAIN.yaml`, `DP-POPUP.yaml`
- [ ] 각 DP의 `ref`가 모두 ds-allowlist.md 목록 안
- [ ] `design-page-lint.py` **통과**
- [ ] `SPEC-000.md`에 사용 DS·소스 위치 기재

---

## 부록 — 자주 막히는 지점

| 증상 | 원인 | 해결 |
|---|---|---|
| `필수 필드 누락: 'props'` | ds-allowlist.md 컴포넌트에 `- **props**:` 없음 | props 줄 추가 |
| `props 형식을 확인하세요` 경고 | props에 `:`/`,` 없음 | `label: string`처럼, 없으면 `없음` |
| `DS 폐쇄 위반: 'XXX'` | DP/화면 ref가 목록에 없음 | 오타 확인 또는 8장 절차로 정식 추가 |
| `raw HTML 직접 작성 금지` | DP yaml에 `<div>` 등 태그 | DS 컴포넌트 ref로만 구성 |
| 산문 `## 헤딩`에서 검증 실패 | ds-allowlist.md에 컴포넌트 아닌 `##` 헤딩 | 설명은 이 문서로, 계약엔 컴포넌트만 |
| CLI `add` 결과가 `@/` 폴더에 생김 | node_modules 미설치로 alias 미해결 | `src/components/ui/`로 이동 후 `@` 삭제 |

### 참고
- shadcn 설치: https://ui.shadcn.com/docs/installation · CLI: https://ui.shadcn.com/docs/cli · Data Table: https://ui.shadcn.com/docs/components/data-table
- 프로젝트 규칙: `.claude/rules/ds-closure.md`, `.claude/rules/constitution.md` · 프로젝트 결정: `foundation/decisions/tech-stack.md`
- 첫 DP 만들기: `guides/first_design_page_guide.md`
