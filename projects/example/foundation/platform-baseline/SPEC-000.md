# SPEC-000: 플랫폼 공통 기준선

## 디자인 시스템

| 항목 | 값 |
|---|---|
| 사용 DS | shadcn/ui (Radix UI + Tailwind CSS v4) |
| 스타일 | new-york |
| 기반 색상 | neutral |
| 컴포넌트 소스 위치 | `input/design-system/ds-source/src/components/ui/` |
| 허용 목록 원본 | `foundation/design-system/ds-allowlist.md` |

## 기술 스택

| 항목 | 값 |
|---|---|
| 프레임워크 | React + TypeScript |
| 빌드 도구 | Vite |
| 스타일링 | Tailwind CSS v4 |
| 테이블 | TanStack Table v8 |
| 폼 | react-hook-form |
| 날짜 | date-fns |
| 아이콘 | lucide-react |
| 알림 | sonner |

## DS 폐쇄(ds-closure) 원칙

- `ds-allowlist.md`에 등록된 컴포넌트만 화면에 사용한다.
- 목록에 없는 컴포넌트를 신규로 사용하려면 `.claude/rules/ds-closure.md`의 추가 절차를 먼저 밟는다.
- raw HTML 태그(`<div>`, `<span>` 등)를 직접 스타일링하는 것은 금지한다.
- 컴포넌트에 임의 inline 스타일을 하드코딩하는 것은 금지한다.

## 경로 별칭

| 별칭 | 실제 경로 |
|---|---|
| `@/components/ui` | `src/components/ui/` |
| `@/lib` | `src/lib/` |
| `@/hooks` | `src/hooks/` |
