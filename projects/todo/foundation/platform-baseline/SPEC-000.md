# SPEC-000 — Todo 앱 플랫폼 Baseline 명세

> ① PREREQUISITE 산출. ③ AI-WEB-DEV Phase 0이 이 명세를 받아 구현한다.
> 구현은 이 문서 밖(app_repo). 이 문서는 "무엇"을 명세하고 "왜"를 기록한다.

---

## 1. 플랫폼 개요

| 항목 | 값 |
|---|---|
| 앱 이름 | TodoFlow |
| 버전 | 0.1.0 (골든패스) |
| 목적 | PO-DEV 3-layer 하네스 골든패스 시연 |
| 접근 주체 | 인증된 사용자(단일 역할 — 골든패스 단순화) |

---

## 2. 공통 기능 목록 (Phase 0 대상)

| 기능 | 전달 모드 | 비고 |
|---|---|---|
| JWT 인증 (로그인/로그아웃/토큰 갱신) | **B** (직접 구현) | D-003, D-007 |
| 인증 미들웨어 (Express route guard) | **B** (직접 구현) | |
| React 인증 컨텍스트 + PrivateRoute | **B** (직접 구현) | |
| RBAC (역할 기반 접근) | **A** (가이드 코드블럭) | 골든패스는 단일 역할 |
| 에러 핸들링 (Express global handler) | **B** (직접 구현) | |
| 응답 포맷 (ApiResponse<T> 표준) | **B** (직접 구현) | |

---

## 3. API 기본 규칙

- Base URL: `/api/v1`
- 인증: `Authorization: Bearer <accessToken>`
- 응답 포맷:
  ```json
  { "success": true, "data": {...}, "message": "OK" }
  { "success": false, "error": { "code": "ERR_CODE", "message": "설명" } }
  ```
- 에러 코드: `AUTH_INVALID`, `AUTH_EXPIRED`, `NOT_FOUND`, `VALIDATION_ERROR`, `INTERNAL_ERROR`

---

## 4. 데이터 모델 개요 (ENT- 계약은 model_repo에)

| 엔티티 | 테이블 | 설명 |
|---|---|---|
| User | users | 인증 주체 |
| Todo | todos | 할 일 항목 |
| ProgressLog | progress_logs | Todo 진행 기록 (히스토리) |

---

## 5. 비기능 요구사항 (NFR)

| NFR | 목표 |
|---|---|
| 응답 속도 | API < 200ms (SQLite 기준) |
| 페이지 로드 | FCP < 1.5s (로컬) |
| 다크모드 | 기본 활성화 (D-006) |
| 접근성 | WCAG 2.1 AA (shadcn 기본 충족) |
