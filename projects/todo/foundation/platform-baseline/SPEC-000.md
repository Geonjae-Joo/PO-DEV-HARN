<!-- spec: SPEC-000 — 공통 기능 baseline 명세 (projects/todo) -->
<!-- 작성: ① PREREQUISITE / 구현: ③ Phase 0(전달 모드 A·B 또는 N/A) -->

# SPEC-000 — 공통 기능 Baseline 명세 (TODO)

> 로그인·SSO·RBAC·앱 셸·감사 등 공통 *기능* 요건을 명세한다. *무엇이* 공통기능인지까지만 — 모드 A/B 결정과 구현은 ③ Phase 0.
> 스택·DS 핀은 `tech-stack.md`·`ds-allowlist.md`가 단일 출처.

---

## 본 프로젝트의 baseline 판정 (요약)

본 앱은 **단일 사용자 로컬 TODO**다. 인증 경계·역할·다중 사용자가 없으므로 대부분의 공통기능이 **N/A**다.
최종 전달 결정은 ③ Phase 0 `baseline-delivery-manifest.yaml`에 기록한다.

## 1. 인증 (Authentication)
| ID | 요건 | 본 프로젝트 판정 |
|---|---|---|
| FEAT-AUTH-1~4 | 로그인/세션/SSO/라우팅 가드 | **N/A** — 단일 사용자, 인증 없음 |

## 2. 권한 (RBAC)
| ID | 요건 | 본 프로젝트 판정 |
|---|---|---|
| FEAT-RBAC-1~4 | 역할/권한/조건부 렌더 | **N/A** — 모든 화면·액션 permission=all |

## 3. 앱 셸 (Application Shell)
| ID | 요건 | 본 프로젝트 판정 |
|---|---|---|
| FEAT-SHELL-1 | 공통 레이아웃(헤더·콘텐츠 슬롯) | **모드 A(경량)** — DP-MAIN 슬롯 구조를 따르는 단순 셸. Header/Breadcrumb 등 DS 컴포넌트 사용 |
| FEAT-SHELL-2~3 | 내비/브레드크럼/사용자 메뉴 | **N/A** — 단일 화면, 전역 내비 불필요 |

## 4. 감사·공통 동작 (Audit & Cross-cutting)
| ID | 요건 | 본 프로젝트 판정 |
|---|---|---|
| FEAT-AUDIT-1 | 감사 로그 | **N/A** — 단일 사용자 |
| FEAT-ERR-1 | 전역 에러/빈/로딩 상태 | **모드 A** — 변경 실패 토스트·빈 목록 안내·로딩 표시. ②의 error_behavior와 정합 |
| FEAT-I18N-1 | 다국어 | **N/A** |

---

## 5. 경계
- 스택·DS·운영(SPEC-OPS-000) 요건은 여기서 정의하지 않는다.
- 도메인 기능(할 일 추가/토글/삭제/필터)은 ②의 screen model(SCR-/REQ-)·PACK-TODO 소관.
</content>
