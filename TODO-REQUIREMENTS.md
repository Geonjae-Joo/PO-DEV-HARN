# TODO Web — 요구사항 정의서 (Gold-Path 리허설용)

> **목적.** PO-Dev Harness 3-레이어 파이프라인(① PREREQUISITE → ② PO-DEV-CHAT → ③ AI-WEB-DEV)을
> **TODO 웹앱**을 소재로 골드패스부터 SDD·TDD까지 끝까지(개발+테스트) 한 바퀴 돌리는 엔드투엔드 리허설(설계 PLAN의 D8)이다.
> 이 문서는 그 출발점인 **요구사항 원천(source of intent)** 이다. 모든 판단은 작성자(AI)가 내렸고, 판단·로그·결함은 다음 산출물에 기록된다.
>
> - 의사결정 로그: `projects/todo/docs/DECISION-LOG.md`
> - 하네스 결함 로그: `projects/todo/docs/HARNESS-DEFECTS.md`
> - 최종 보고서: `projects/todo/docs/REHEARSAL-REPORT.md`
>
> 작성일: 2026-06-20 · 프로젝트 경로: `projects/todo/`

---

## 1. 제품 개요

개인 사용자가 **할 일(todo)** 을 추가하고, 완료 체크하고, 삭제하고, 상태별로 걸러 보는 **단일 화면** 웹앱.
"간단한 TODO"라는 요청에 맞춰 의도적으로 작게 잡되, 하네스의 모든 계약·게이트·TDD 장치를 한 번씩 통과하기에 충분한 최소 도메인을 갖춘다.

- **액터**: 단일 사용자(`user`). 멀티유저·인증·공유 없음(아래 6. 범위 밖).
- **단일 화면**: `SCR-TODO-LIST` — 목록·추가·필터를 한 화면에서. (navigate 분기 없음 → 경계 단순)
- **단일 엔티티**: `ENT-TODO`.

## 2. 사용자 스토리

- US1. 사용자로서, 할 일을 입력해 목록에 **추가**하고 싶다. 그래야 기억할 필요가 없다.
- US2. 사용자로서, 끝낸 할 일을 **완료 체크**하고 싶다. 그래야 남은 일이 보인다.
- US3. 사용자로서, 불필요한 할 일을 **삭제**하고 싶다. 그래야 목록이 깔끔하다.
- US4. 사용자로서, **전체 / 미완료 / 완료**로 **필터**해서 보고 싶다. 그래야 집중할 수 있다.

## 3. 기능 요구사항 (→ ②에서 REQ- 스파인 ID로 채번)

| # | 기능 | 트리거 | 결과(outcome) | 수용 기준(요지) |
|---|---|---|---|---|
| FR-1 | 할 일 추가 | 추가 버튼 클릭 | ENT-TODO 생성(mutate) | 제목 입력 후 추가 → 목록 맨 위에 ACTIVE로 추가, 입력창 비워짐 |
| FR-2 | 완료 토글 | 행 체크박스 변경 | ENT-TODO 상태 변경(mutate) | 체크 시 ACTIVE→COMPLETED, 해제 시 COMPLETED→ACTIVE |
| FR-3 | 할 일 삭제 | 행 삭제 버튼 클릭 | ENT-TODO 삭제(mutate) | 삭제 시 목록에서 사라지고 영구 제거 |
| FR-4 | 상태 필터 | 필터 변경 | ENT-TODO 조회(query) | 전체/미완료/완료 선택 시 해당 조건 목록만 표시 |

### 입력 검증 (FR-1)
- 제목은 **필수**(빈 문자열·공백만 입력 금지). 최대 200자. 위반 시 추가 차단 + 인라인 안내.

### 상태 전이 (ENT-TODO.status) — TDD 전수 커버 대상
```
ACTIVE ──(완료 토글)──▶ COMPLETED
COMPLETED ──(완료 토글)──▶ ACTIVE
```
(state machine 모든 전이 ≥1 테스트 — tdd-policy.md)

## 4. 데이터 모델 (→ ② ENT-TODO)

| 속성 | 의미 | 종류 | 비고 |
|---|---|---|---|
| todoId | 할 일 식별자 | identifier | 필수, 서버 발급 |
| title | 할 일 내용 | value | 필수, 1–200자 |
| status | 완료 여부 | value(enum) | `ACTIVE` \| `COMPLETED`, 기본 ACTIVE |
| createdAt | 생성 시각 | value | 필수, 서버 발급, 정렬 기준(최신 우선) |

## 5. 비기능 요구사항 (NFR)
- 단일 사용자·로컬 사용 가정. 동시성·대규모 부하 범위 밖.
- 목록 조회·변경 응답은 체감 즉시(<300ms, 인메모리 저장소 기준).
- 모든 변경 액션은 실패 시 사용자에게 안내(network_fail) — 단일 사용자라 permission_denied는 형식상만.

## 6. 범위 밖 (Out of Scope) — 의도적 제외
- 인증/로그인/SSO/RBAC (SPEC-000 공통기능). 단일 사용자 가정으로 **Phase 0에서 N/A 처리**.
- 멀티 디바이스 동기화, 영속 DB(인메모리 저장소로 충분), 마감일·우선순위·태그·정렬 옵션.
- 다중 화면 내비게이션(상세/생성 별도 화면) — 단일 화면 인라인으로 충분.

## 7. 디자인 시스템 매핑 (DS 폐쇄 — ds-allowlist.md 안에서만)

| 컴포넌트(CMP) | DS ref | 용도 |
|---|---|---|
| 추가 버튼 | `Button` | header-actions, 할 일 추가 |
| 제목 입력 | `Input` | content, 새 할 일 제목 |
| 상태 필터 | `FilterBar` | content, 전체/미완료/완료 |
| 할 일 목록 | `DataTable` | content, 체크박스+제목+삭제 행 |

(템플릿 페이지: `DP-MAIN`. 팝업 불필요 → `DP-POPUP` 미사용.)

## 8. 수용 시나리오 (E2E 여정 → ② JRN-, ③ Phase γ Playwright)
> 단일 화면 다단계 여정으로 구성(navigate 없음).
1. 빈 목록에서 "우유 사기" 추가 → 목록에 ACTIVE로 표시
2. "우유 사기" 완료 체크 → COMPLETED로 표시
3. 필터를 "완료"로 변경 → "우유 사기"만 표시
4. 필터를 "미완료"로 변경 → 빈 목록 안내 표시

## 9. 기술 스택 결정 (① PREREQUISITE 권한 — 상세는 tech-stack.md)
하네스는 스택을 고정하지 않는다(constitution 원칙 8). 본 리허설은 **이 머신에서 실제 실행·green 테스트가 가능한** 경량 풀스택 TypeScript로 핀한다:
- 백엔드: Node.js + Express + TypeScript, 인메모리 저장소. 테스트: Vitest + Supertest (API 레벨).
- 프론트엔드: React + Vite + TypeScript. 테스트: Vitest + Testing Library (화면 레벨).
- E2E: Playwright (Phase γ).
- 근거: Java/Gradle 부트스트랩은 네트워크 의존·중량이라 "간단한 TODO" 리허설에 과함. 2계층(API+화면) 테스트 구조는 그대로 보존. (DECISION-LOG D-002)

## 10. 완료 정의 (DoD)
- ② Gate A 통과(`SCR-TODO-LIST` status: confirmed) + `PACK-TODO` 발행(spec-pack-guard green).
- ③ Phase α scaffold → Phase β TDD(모든 T### red→green→refactor, 커밋 게이트 통과) → Phase γ E2E.
- 백엔드·프론트 테스트 스위트 green, FR-1~4 + 상태 전이 전수 커버.
- 스파인 추적 끊김 0 (SCR→CMP→REQ→PACK→T###→test→commit).
</content>
