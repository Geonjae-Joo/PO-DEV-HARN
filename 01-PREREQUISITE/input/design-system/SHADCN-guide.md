# SHADCN Design System 가이드 (① PREREQUISITE)

> 이 문서는 **shadcn/ui**를 npm으로 설치해 ①의 `input/design-system/` 폴더를 채우고,
> 그 결과를 `design-guide.md`(허용 집합 원본)로 등록해 ②·③이 쓰게 만드는 **예시 절차**다.
> 대상: 개발 리드/운영자. 시점: 프로젝트당 1회(준비 단계).
>
> 경계: 여기서는 **DS 자산을 준비**할 뿐이다. 화면 정의(②)·실제 구현(③)은 하지 않는다.
> 모든 컴포넌트는 `design-guide.md`에 등록돼야만 layout-recommend·lint가 사용을 허용한다(DS 폐쇄).

---

## 0. 왜 shadcn/ui인가

shadcn/ui는 npm 패키지를 런타임 의존성으로 import하는 라이브러리가 **아니다**.
CLI가 컴포넌트의 **소스 코드(.tsx)를 프로젝트 안으로 복사**해 넣는 방식이다.
따라서 우리는 복사된 소스를 **그대로 소유·수정**할 수 있고, 이 레이어의 목적(DS를 우리 자산으로 고정)과 잘 맞는다.

- 기술스택 고정값(`rules/tech-stack.md`): React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui.
- design token은 CSS custom properties로 두고 Tailwind에서 `extend`로 참조한다.

---

## 1. 사전 준비 — Vite + Tailwind 베이스

shadcn은 Tailwind가 깔린 React+TS 프로젝트 위에서 동작한다. DS만 추려낼 임시 작업 공간을 만든다.

```bash
# DS 추출용 임시 작업 폴더 (app_repo가 아니라 준비용)
npm create vite@latest ds-workbench -- --template react-ts
cd ds-workbench
npm install

# Tailwind v4 + Vite 플러그인
npm install tailwindcss @tailwindcss/vite
```

`vite.config.ts`에 Tailwind 플러그인과 `@` alias를 등록한다.

```ts
import path from "path"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

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

## 2. shadcn/ui 초기화

```bash
# 대화형 초기화 → components.json 생성
npx shadcn@latest init
```

초기화 시 묻는 항목 예시 답안:

| 질문 | 권장 답 | 의미 |
|---|---|---|
| Base color | `slate` (또는 디자이너 지정 팔레트) | design token 베이스 |
| CSS variables 사용 | **Yes** | 색을 CSS 변수로 → token 연동 쉬움 |
| Components alias | `@/components` | 복사될 경로 |

생성된 `components.json`이 이후 모든 `add`의 기준이 된다.

---

## 3. 필요한 컴포넌트만 npm(CLI)으로 설치

프로젝트에 **실제로 쓸 컴포넌트만** 추가한다(불필요한 발명 방지).

```bash
# 개별 추가
npx shadcn@latest add button input table dialog select

# 한 번에 여러 개
npx shadcn@latest add card badge dropdown-menu calendar popover form
```

각 명령은 `src/components/ui/<name>.tsx`로 소스를 복사하고, 필요한 Radix 의존성을 `npm install`한다.

> 권장 최소 세트(업무 웹앱 기준): `button`, `input`, `select`, `table`, `dialog`, `form`,
> `card`, `badge`, `dropdown-menu`, `calendar`, `popover`, `tabs`, `toast`.

---

## 4. design token 정의 (CSS custom properties)

디자이너가 준 토큰을 `src/index.css`의 `:root`에 변수로 박는다. shadcn 컴포넌트는 이 변수를 참조한다.

```css
@import "tailwindcss";

:root {
  /* 색상 토큰 */
  --color-primary:      #2563eb;
  --color-primary-fg:   #ffffff;
  --color-secondary:    #64748b;
  --color-destructive:  #dc2626;
  --color-border:       #e2e8f0;
  --color-bg:           #ffffff;
  --color-fg:           #0f172a;

  /* 간격·반경·타이포 토큰 */
  --spacing-md: 1rem;
  --radius:     0.5rem;
  --font-sans:  "Pretendard", system-ui, sans-serif;
}
```

Tailwind에서 토큰을 유틸리티로 노출하려면 `@theme`로 매핑한다(Tailwind v4).

```css
@theme {
  --color-primary: var(--color-primary);
  --radius-md: var(--radius);
  --font-sans: var(--font-sans);
}
```

> 원칙(`rules/tech-stack.md`): **색·간격·타이포는 토큰만 참조**한다. 컴포넌트에 hex/px를 하드코딩하지 않는다.

---

## 5. `input/design-system/` 로 옮겨 담기

추출이 끝나면 ds-workbench에서 **우리가 소유할 자산만** 이 폴더로 복사한다.
런타임 코드가 아니라 **DS 원본 + 토큰 + 메타**를 담는 것이 목적이다.

### 옮길 것 (✓)

```
01-PREREQUISITE/input/design-system/
├── components/              # ✓ src/components/ui/*.tsx 전체 복사 (DS 컴포넌트 소스)
│   ├── button.tsx
│   ├── input.tsx
│   ├── table.tsx
│   ├── dialog.tsx
│   └── ...
├── tokens/
│   ├── tokens.css           # ✓ :root 변수 + @theme 매핑 (4단계 결과물)
│   └── tailwind-preset.ts   # ✓ (선택) 토큰을 담은 Tailwind preset
├── components.json          # ✓ shadcn 설정 (재현·추가 설치 기준)
├── lib/
│   └── utils.ts             # ✓ shadcn이 쓰는 cn() 유틸 (clsx + tailwind-merge)
└── SHADCN-guide.md          # ✓ (이 문서)
```

### 옮기지 말 것 (✗)

- `node_modules/`, `package-lock.json` — 의존성은 ③의 `app_repo`가 다시 설치한다(✗).
- Vite 앱 골격(`main.tsx`, `App.tsx`, `index.html`) — 워크벤치 부산물(✗).
- 데모/예제 페이지 — DS 원본이 아님(✗).

> 판별 기준: **"이 화면들이 공통으로 재사용할 DS 원본인가?"** → 예면 옮기고, 앱 실행을 위한 부산물이면 버린다.

---

## 6. `design-guide.md` 등록 (허용 집합 원본)

복사만으로는 ②·③이 쓸 수 없다. `design-guide.md`에 **컴포넌트마다 한 섹션**(`## 컴포넌트명`)을
등록해야 비로소 허용 집합이 된다(`ds-guide-validate.py`가 형식을 검증).
이 파일의 위치는 `output/foundation/design-system/design-guide.md`.

````markdown
## Button

- **import**: `import { Button } from "@/components/ui/button"`
- **props**:
  - `variant`: `default | secondary | destructive | outline | ghost | link`
  - `size`: `default | sm | lg | icon`
  - `disabled`: `boolean`
- **용도**: 화면의 액션 트리거(저장, 내보내기, 삭제 등).
- **토큰**: `--color-primary`(default), `--color-destructive`(destructive)
- **예시**:
  ```tsx
  <Button variant="secondary" size="sm">엑셀 내보내기</Button>
  ```

## Input

- **import**: `import { Input } from "@/components/ui/input"`
- **props**: `type`, `placeholder`, `value`, `onChange`, `disabled`
- **용도**: 단일 행 텍스트/숫자 입력.
- **예시**:
  ```tsx
  <Input type="text" placeholder="주문번호 검색" />
  ```

## Table

- **import**: `import { Table, TableHeader, TableBody, TableRow, TableCell } from "@/components/ui/table"`
- **props**: (compound) header/body/row/cell 조합
- **용도**: 목록(list archetype)의 데이터 표.
````

> `ds-guide-validate.py`가 요구하는 필수 필드: **이름(## 헤딩) · props · 용도**.
> 이 셋이 빠지면 저장이 차단된다.

등록 후 검증:

```bash
# design-guide.md 형식·필수 필드 검증 (저장 시 자동, 수동 실행도 가능)
python hooks/ds-guide-validate.py output/foundation/design-system/design-guide.md
```

---

## 7. 이후 흐름에서 어떻게 쓰이나

```
[① 여기]  shadcn add → design-system/ 적재 → design-guide.md 등록 → 검증 통과
   │
   ▼
[① design-page-builder]  design-guide.md 허용 집합만으로 DP-* 템플릿 골격 생성
   │  (design-page-lint.py가 DS 폐쇄 검증)
   ▼
[② layout-recommend]  PI 발화 → design-guide.md의 컴포넌트로만 매핑 (DS 밖 발명 금지)
   │  (on-save-lint-L1이 DS 폐쇄 검증)
   ▼
[③ design-system-usage]  design-system/components 를 React로 구현, 토큰만 참조해 스타일링
       (code-reviewer가 DS 준수 검증)
```

세 레이어 모두 **`design-guide.md`에 등록된 컴포넌트만** 쓸 수 있다 — 이것이 DS 폐쇄(`rules/ds-closure.md`)다.

---

## 8. 새 컴포넌트가 더 필요해질 때

PI가 허용 집합에 없는 컴포넌트를 원하면, 임의로 추가하지 않고 절차를 밟는다(`rules/ds-closure.md`).

```bash
# 1) 워크벤치에서 새 컴포넌트 추가
npx shadcn@latest add command

# 2) 소스를 input/design-system/components/ 로 복사
# 3) design-guide.md 에 ## Command 섹션 추가 (props·용도·예시)
# 4) 검증
python hooks/ds-guide-validate.py output/foundation/design-system/design-guide.md
python skills/design-page-builder/scripts/design-page-lint.py   # 기존 DP 영향 확인
```

> 어떤 경우에도 "design-guide.md에 없는 컴포넌트를 그냥 쓰는 것"은 허용되지 않는다.

---

## 9. 체크리스트 (DoD)

- [ ] 필요한 shadcn 컴포넌트만 `npx shadcn add`로 설치했다.
- [ ] design token을 CSS custom properties로 정의하고 Tailwind에 매핑했다.
- [ ] `components/`, `tokens/`, `components.json`, `lib/utils.ts`를 `input/design-system/`에 적재했다.
- [ ] `node_modules` 등 앱 부산물은 옮기지 않았다.
- [ ] 모든 컴포넌트를 `design-guide.md`에 `## 이름 + props + 용도 + 예시`로 등록했다.
- [ ] `ds-guide-validate.py` 검증을 통과했다.
