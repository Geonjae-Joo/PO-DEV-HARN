<!-- spec: SPEC-000 — 공통 기능 baseline 명세 (인증·앱 셸·테마·라우팅 가드) -->
<!-- 작성: ① PREREQUISITE / 구현: ③ Phase 0(전달 모드 A·B) -->

# SPEC-000 — 공통 기능 Baseline 명세 (DevLog)

> SPEC-OPS-000(배포·CI/CD = 공통 *운영* 요건)과 형제 명세. 이 문서는 **인증·앱 셸(Header)·테마 토글·라우팅 가드 등 공통 *기능* 요건**을 정의한다.
> **명세까지만** 한다 — *무엇이* 공통 기능인지(scope·수용 기준)는 여기서, *어떤 스택으로*는 `tech-stack.md`, *실제 코드*는 ③ Phase 0가 만든다.
> 스파인: `SPEC-000`. 커밋 머리말 `[SPEC-000/T###]` (REQ- 면제, `(baseline)` 사유 토큰).
> 본 요건은 DevLog SRS의 SFR-007/011/012 · SER-001/002/003/004 · SIR-002 · QAR-005에서 도출했다.

---

## 0. 전달 방식 (③ Phase 0가 모드 결정)

각 공통 기능은 ③ Phase 0에서 **모드 A(가이드 코드블럭)** 또는 **모드 B(직접 코드 주입)** 로 산출된다.
판정 한 줄: **"프로젝트마다 변형되나?"** → 예면 A, 아니면 B. 결과는 `app_repo/baseline-delivery-manifest.yaml`.

---

## 1. 인증 (Authentication) — SFR-007 · SFR-012 · SER-001

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-AUTH-1 | NextAuth Credentials 로그인 (`/login`) | 데모 계정(alice/bob/kim) 자격 검증 후 JWT 발급, 실패 시 "아이디 또는 비밀번호가 올바르지 않습니다". green 테스트(성공/실패) | B |
| FEAT-AUTH-2 | JWT 세션(쿠키) 관리 | `NEXTAUTH_SECRET` 서명 JWT를 쿠키에 저장(별도 세션 스토어 없음), 만료 시 보호 라우트 차단 | B |
| FEAT-AUTH-3 | 로그아웃 (SFR-012) | 세션 해제 후 메인(`/`)으로 이동, 로그인 상태일 때만 버튼 노출 | B |
| FEAT-AUTH-4 | 미인증 라우팅 가드 (다층 방어) | `middleware.ts` 1차 차단 + Server Action/Component 2차 재검증. 보호 라우트(`/write`,`/dashboard`) 미인증 진입 시 `/login?callbackUrl=...` 리다이렉트 | A |

> 데모 계정·평문 비교는 DAR-004 참조(운영 시 bcrypt 필수 — 코드 주석 명시). 외부 OAuth는 비-목표(COR-002).

## 2. 앱 셸 (Application Shell) — SIR-002

> ②의 design-page(DP-MAIN)·DS 허용집합과 정합해야 한다. 셸은 ds-allowlist의 `Header` 등만 사용(DS 폐쇄).

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-SHELL-1 | 공통 Header (전 페이지 상단 고정) | DP-MAIN의 `header` 슬롯(locked) 구조와 일치, `Header` DS 컴포넌트만 사용 | A |
| FEAT-SHELL-2 | Header 좌측 브랜드 | 로고 + "DevLog" 텍스트 → 메인(`/`) 링크 | A |
| FEAT-SHELL-3 | Header 우측 인증 영역 | 비로그인: "로그인" 버튼 / 로그인: 사용자 이름 + "대시보드" + "글 작성" + "로그아웃". 상태 확인 중 스켈레톤으로 깜빡임 방지 | A |

## 3. 테마 (Theme) — SFR-011

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-THEME-1 | 다크/라이트 토글 (🌙/☀️) | Header 우측 토글, 클릭 시 즉시 전환, **localStorage 영속**, 기본=다크, Tailwind `dark:` variant(`darkMode:"class"`) | A |

## 4. 공통 동작 (Cross-cutting) — SER-003/004 · QAR-003/005

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-VALID-1 | Server Action 입력 검증 패턴 | 세션 존재 + 필수 필드 + 타입 검증, 빈/과대 입력 방어 (SER-003) | A |
| FEAT-ERR-1 | 안전 에러 메시지 패턴 | throw 에러에 민감정보(DB pw·경로·스택) 비포함, 사용자에겐 친근 메시지만 (SER-004) | A |
| FEAT-ERR-2 | 전역 로딩/에러/빈 상태 패턴 | `loading.tsx`(스켈레톤)·`error.tsx`(다시 시도/목록으로)·빈 상태 UI 공통 패턴 (QAR-003) | A |
| FEAT-HYDRATION-1 | Hydration 안정성 패턴 | 시간 의존 코드(`new Date()` 등)는 mounted 패턴 또는 로컬 타임존 YYYY-MM-DD 키로 mismatch 방지 (QAR-005) | A |

---

## 5. ③ Phase 0 처리 흐름 (참고)

```
SPEC-000.md(이 명세) + tech-stack.md(스택 핀) 수신
  │
  ▼
/speckit.specify  공통 기능별 전달 모드(A/B) 결정 → app_repo/baseline-delivery-manifest.yaml
  ├─[mode B]→ /plan → /tasks(test-first) → Gate B → /implement → commit [SPEC-000/T### (baseline)]
  │            (완성 코드: NextAuth 설정·로그인/로그아웃 Server Action — 테스트 green)
  └─[mode A]→ app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md (예시 코드블럭·패턴)
               → Phase β가 도메인 구현 시 로드해 적용(라우팅 가드·테마·에러 경계 등)
```

---

## 6. 경계 (무엇을 하지 않는가)

- **스택·DS 핀 정의 금지** — `tech-stack.md`·`ds-allowlist.md`가 단일 출처.
- **운영 요건 정의 금지** — 배포·CI/CD는 SPEC-OPS-000.
- **도메인 기능 정의 금지** — 글 목록·상세·대시보드·타이머 등은 ②의 screen model(SCR-/REQ-)·PACK-.
- **구현 금지** — 코드·테스트는 ③ Phase 0(B) 또는 baseline-guides(A). ①은 명세까지만.
