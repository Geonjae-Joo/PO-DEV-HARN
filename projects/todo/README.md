# TODO Web — 할 일 관리 앱

> 개인용 **할 일(todo)** 관리 단일 화면 웹앱. PO-Dev Harness 3-레이어 파이프라인(① PREREQUISITE → ② PO-DEV-CHAT → ③ AI-WEB-DEV)을
> 골드패스부터 SDD·TDD·E2E까지 끝까지 돌려 만든 **엔드투엔드 리허설 산출물**이다.
>
> 실행·수정·CI/CD 방법은 **[QUICK-START.md](QUICK-START.md)** 참조.

---

## 1. 무엇을 하는 앱인가

한 화면에서 할 일을 추가하고, 완료 체크하고, 삭제하고, 상태별로 거른다.

| 기능 | 동작 | 스파인 |
|---|---|---|
| 추가 | 제목 입력 후 "추가" → 목록 최상단에 `ACTIVE`로 | REQ-TODO-LIST.001 |
| 완료 토글 | 행 체크박스 → `ACTIVE ⇄ COMPLETED` | REQ-TODO-LIST.002 |
| 삭제 | 행 "삭제" 버튼 → 영구 제거 | REQ-TODO-LIST.003 |
| 필터 | 전체 / 미완료 / 완료 | REQ-TODO-LIST.004 |

- 제목은 **필수**(공백만 불가), 최대 200자. 정렬은 생성 최신 우선.
- 단일 사용자·로컬 사용 가정 → 인증/권한 없음(모든 권한 `all`).

## 2. 아키텍처

```
[브라우저] ─ React(5173) ──/api 프록시──▶ Express(3001) ─ 인메모리 저장소
             화면(SCR-TODO-LIST)            REST API           ENT-TODO
```

| 영역 | 스택 | 위치 |
|---|---|---|
| 백엔드 | Node + Express + TypeScript, 인메모리 저장소 | `app_repo/backend/` |
| 프론트 | React 18 + Vite + TypeScript | `app_repo/frontend/` |
| 테스트 | Vitest + Supertest(API) / Testing Library(화면) / Playwright(E2E) | 각 패키지 `test/`·`*.test.tsx`·`e2e/` |

### REST API 계약

| Method | Path | 설명 | 응답 |
|---|---|---|---|
| GET | `/api/todos?filter=all\|active\|completed` | 목록 조회 | 200 `Todo[]` |
| POST | `/api/todos` `{title}` | 추가 | 201 `Todo` / 400(빈·200자초과) |
| PATCH | `/api/todos/:id/toggle` | 완료 토글 | 200 `Todo` / 404 |
| DELETE | `/api/todos/:id` | 삭제 | 204 / 404 |

`Todo = { todoId, title, status: "ACTIVE"|"COMPLETED", createdAt }` (= 계약 엔티티 `ENT-TODO`).

## 3. 폴더 구조 (projects/todo)

```
todo/
├── README.md                  # (이 문서)
├── QUICK-START.md             # 실행·수정·CI/CD 가이드
├── foundation/                # ① 산출: tech-stack·SPEC-000·DS 허용집합·design-pages
├── model_repo/                # ② 산출: 계약(단일 진실원)
│   ├── screens/SCR-TODO-LIST.yaml      # 화면 모델 (confirmed)
│   ├── entities/ENT-TODO.yaml          # 데이터 계약
│   ├── journeys/JRN-TODO-MANAGE.yaml   # E2E 여정
│   └── specs/PACK-TODO/spec-pack.yaml       # 발행된 spec 팩 (③ 입력)
├── app_repo/                  # ③ 산출: 실행 코드 (자체 git 레포)
│   ├── backend/  (src/ test/)
│   ├── frontend/ (src/ test/ e2e/)
│   └── specs/PACK-TODO/  (spec·plan·tasks.md)
└── docs/                      # 리허설 보고서·의사결정·결함 로그·E2E 증거
```

## 4. 하네스 맥락 (왜 이렇게 생겼나)

- **단일 진실원**: 화면 계약은 `model_repo/screens/SCR-TODO-LIST.yaml`(YAML). 앱 코드는 그 파생 구현이다.
- **스파인 ID 추적**: `SCR-TODO-LIST → CMP-… → REQ-TODO-LIST.001~004 → PACK-TODO → T### → test → commit` 끝까지 연결.
- **게이트**: `app_repo`는 자체 git 레포로, commit 시 `tdd-gate`(테스트 없음/실패 차단) + `commit-spine-id`(메시지 스파인 ID 필수) 훅이 강제한다.
- **DS 폐쇄**: 화면/구현 컴포넌트는 `foundation/design-system/ds-allowlist.md` 허용집합(Button·Input·FilterBar·DataTable 등) 안에서만.

## 5. 현재 상태

- 백엔드 테스트 **18** + 프론트 테스트 **6** green, E2E 여정(JRN-TODO-MANAGE) 실브라우저 완주.
- **어떻게 만들었나(단계별 상세)**: [`docs/BUILD-PROCESS.md`](docs/BUILD-PROCESS.md)
- 요약 보고서·게이트 검증·발견 결함: [`docs/REHEARSAL-REPORT.md`](docs/REHEARSAL-REPORT.md) · [`docs/DECISION-LOG.md`](docs/DECISION-LOG.md) · [`docs/HARNESS-DEFECTS.md`](docs/HARNESS-DEFECTS.md)
