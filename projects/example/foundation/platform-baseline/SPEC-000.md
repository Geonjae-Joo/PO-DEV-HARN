<!-- spec: SPEC-000 — 공통 기능 baseline 명세 (인증·RBAC·앱 셸·감사·공통 상태) -->
<!-- 작성: ① PREREQUISITE / 구현: ③ Phase 0(전달 모드 A·B) -->

# SPEC-000 — 공통 기능 Baseline 명세

> SPEC-OPS-000(배포·CI/CD·관측성 = 공통 *운영* 요건)과 형제 명세. 이 문서는 **로그인·SSO·RBAC·앱 셸·감사 로그 등 공통 *기능* 요건**을 정의한다.
> **명세까지만** 한다 — *무엇이* 공통 기능인지(scope·요구사항·수용 기준)는 여기서, *어떤 스택으로*는 `foundation/decisions/tech-stack.md`, *실제 코드*는 ③ Phase 0가 만든다. ①은 기능 코드를 구현하지 않는다.
> 스파인: `SPEC-000`. 커밋 머리말 `[SPEC-000/T###]` (SPEC- 계열 — REQ- 면제, `(baseline)` 등 사유 토큰 표기. commit-convention.md).
>
> **스택·디자인 핀은 여기서 정의하지 않는다.** DS(shadcn 등)·프레임워크·빌드도구·경로 별칭은 `foundation/decisions/tech-stack.md`(단일 출처)와 `foundation/design-system/ds-allowlist.md`(허용집합)를 참조한다. 이 문서는 *기능 요건*만 다룬다.

---

## 0. 전달 방식 (③ Phase 0가 모드 결정)

각 공통 기능은 ③ Phase 0에서 **모드 A(가이드 코드블럭)** 또는 **모드 B(직접 코드 주입)** 로 산출된다.
판정 한 줄: **"프로젝트마다 변형되나?"** → 예면 A(예: 권한 조건부 렌더·감사 로그 삽입 패턴), 아니면 B(예: 로그인/SSO 모듈·JWT 필터·RBAC 엔티티). 결과는 `app_repo/baseline-delivery-manifest.yaml`에 기록.
아래 각 요건의 `delivery(권장)` 열은 기본값 제안이며 최종 결정은 ③ `/speckit.specify`(Phase 0)가 한다.

---

## 1. 인증 (Authentication)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-AUTH-1 | 로그인/로그아웃 | 자격 검증 후 세션/토큰 발급, 로그아웃 시 무효화. green 테스트(성공/실패/만료) | B |
| FEAT-AUTH-2 | 세션·토큰 수명 관리 | 만료·갱신(refresh) 규칙 적용, 만료 시 보호 라우트 접근 차단 | B |
| FEAT-AUTH-3 | SSO 연동 (사내 IdP — tech-stack.md/ops-stack.md 핀) | SSO 로그인 왕복 성공, 미인증 사용자 리다이렉트 | B |
| FEAT-AUTH-4 | 미인증 라우팅 가드 | 보호 화면 직접 진입 시 로그인으로 리다이렉트(딥링크 보존) | A |

## 2. 권한 (RBAC)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-RBAC-1 | 역할 모델 (role/permission) | 역할·권한 엔티티 정의, tech-stack.md의 role 목록과 일치 | B |
| FEAT-RBAC-2 | API 레벨 권한 강제 | 권한 없는 호출 403, 화면별 actor 경계(②의 action.permission)와 정합 | B |
| FEAT-RBAC-3 | 화면 레벨 조건부 렌더 | 권한 없는 컴포넌트는 DOM에 없음(②의 acceptance "DOM에 없다"와 일치) | A |
| FEAT-RBAC-4 | admin 전용 기능 게이트 | admin-only action/화면이 비-admin에게 비노출·비호출 | A |

## 3. 앱 셸 (Application Shell)

> ②의 design-page(DP-*)·DS 허용집합과 정합해야 한다. 셸 컴포넌트는 ds-allowlist의 Header/NavMenu/Breadcrumb/Avatar 등만 사용(DS 폐쇄).

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-SHELL-1 | 공통 레이아웃(헤더·내비·콘텐츠 슬롯) | DP-MAIN 슬롯 구조와 일치, DS 컴포넌트만 사용 | A |
| FEAT-SHELL-2 | 내비게이션·브레드크럼 | 라우트↔NavMenu/Breadcrumb 연동, 현재 위치 표시 | A |
| FEAT-SHELL-3 | 사용자 메뉴(프로필·로그아웃) | Avatar/DropdownMenu로 세션 사용자 표시·로그아웃 동선 | A |

## 4. 감사·공통 동작 (Audit & Cross-cutting)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| FEAT-AUDIT-1 | 감사 로그 삽입 패턴 | mutate 계열 action에 행위자·대상·시각 기록(②의 outcome.type: mutate 대상) | A |
| FEAT-ERR-1 | 전역 에러/빈/로딩 상태 | 네트워크 실패·권한거부·빈목록·로딩의 공통 UI 패턴(②의 error_behavior와 정합) | A |
| FEAT-I18N-1 | (선택) 다국어·로캘 | 텍스트 외부화·로캘 전환(프로젝트 요구 시) | A |

---

## 5. ③ Phase 0 처리 흐름 (참고)

```
foundation/platform-baseline/SPEC-000.md(이 명세) + foundation/decisions/tech-stack.md(스택 핀) 수신
  │
  ▼
/speckit.specify  공통 기능별 전달 모드(A/B) 결정 → app_repo/baseline-delivery-manifest.yaml 작성
  ├─[mode B]→ /plan → /tasks(test-first) → Gate B → /implement → commit  [SPEC-000/T### (baseline)]
  │            (완성 코드: 로그인/SSO 모듈·JWT 필터·RBAC 엔티티 — 테스트 green)
  └─[mode A]→ app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md (예시 코드블럭·패턴)
               → Phase β가 도메인 구현 시 로드해 변형 적용(권한 조건부 렌더·감사 로그 삽입 등)
  ▼
Phase β/γ 가 도메인 팩(PACK-*)·여정(JRN-) 구현 시 위 baseline을 호출/적용
```

---

## 6. 경계 (무엇을 하지 않는가)

- **스택·DS 핀 정의 금지** — `tech-stack.md`·`ds-allowlist.md`가 단일 출처. 이 문서는 기능 요건만.
- **운영 요건 정의 금지** — 배포·CI/CD·관측성은 SPEC-OPS-000.
- **도메인 기능 정의 금지** — 주문·회원 등 도메인 화면/요구사항은 ②의 screen model(SCR-/REQ-)과 PACK-.
- **구현 금지** — 코드·테스트는 ③ Phase 0(B) 또는 baseline-guides(A). ①은 명세까지만.
