# TODO 골드패스 엔드투엔드 리허설 — 최종 보고서

> **목적**: PO-Dev Harness 3-레이어 파이프라인(① PREREQUISITE → ② PO-DEV-CHAT → ③ AI-WEB-DEV)을
> **TODO 웹앱**으로 골드패스부터 SDD·TDD·개발·테스트까지 한 바퀴 완주(설계 PLAN의 D8 엔드투엔드 리허설).
> **결론: 전 구간 완주 성공 (green).** 모든 게이트·훅이 의도대로 발화했고, 하네스 결함 2건(+관찰 3건)을 발견·기록했다.
> 작성: 2026-06-20 · 프로젝트: `projects/todo/` · 브랜치: `harn-todo-test`

---

## 1. 한눈에 보기

| 레이어 | 산출물 | 게이트 | 결과 |
|---|---|---|---|
| ① PREREQUISITE | tech-stack·SPEC-000/OPS·DS 재사용·design-pages·link-manifest | (디자인 자산 정합) | ✅ |
| ② PO-DEV-CHAT | SCR-TODO-LIST·ENT-TODO·JRN-TODO-MANAGE·PACK-TODO | schema/lint L1–L4/sufficiency/**Gate A**/spec-pack-guard/spine_ledger | ✅ 전부 green |
| ③ AI-WEB-DEV | app_repo(Node+Express / React+Vite) + 테스트 | **tdd-gate·commit-spine-id** 실발화·Gate B·code-review | ✅ green |
| 테스트 | 백엔드 18 + 프론트 6 + E2E 여정 4스텝 | RED→GREEN 증명·실브라우저 완주 | ✅ |

**스파인 추적 무결**: `SCR-TODO-LIST → CMP-TODO-LIST.* → REQ-TODO-LIST.001~004 → PACK-TODO → T001/T002 → test → commit` 끊김 0.

---

## 2. 단계별 실행 로그 (요지)

### ① PREREQUISITE
- 기술 스택을 **경량 TypeScript 풀스택**으로 핀(constitution 원칙 8: 스택은 프로젝트별 결정). 근거 D-002.
- 인증/RBAC(SPEC-000)는 단일 사용자라 **N/A** 처리(D-004). DS 자산은 example foundation 재사용(D-001).

### ② PO-DEV-CHAT (계약 정의)
- `SCR-TODO-LIST`(단일 화면, 4 액션) 작성 → **저장 검증 체인 전부 green**:
  - schema-validate ✅ · lint L1–L4 ✅(경고 0) · sufficiency ✅(error 0/warn 0) · spine_ledger ✅(15 IDs 유일)
- **Gate A 6조건 전부 통과** → `status: confirmed` (v2):
  `lint·sufficiency·전 action user_confirmed·open_question 0·PO 승인·전역 ID 유일성`.
- `spec-pack-guard` ✅ → **PACK-TODO** 발행(confirmed + 참조 무결 + 여정 커버).
- 핵심 학습: sufficiency-check가 입력 컴포넌트엔 validation 노트, 비동기 액션엔 error_behavior, 테이블엔 initial_state를 **ERROR로 강제** → 계약 작성 시 선반영해 1패스 통과.

### ③ AI-WEB-DEV (구현)
- **Phase 0**: `baseline-delivery-manifest.yaml` — mode B 0건, mode A 2건(셸·에러상태), N/A 11건.
- **Phase α (scaffold)**: TodoList shell + DS 컴포넌트 → `[SCAFFOLD]` 커밋. **tdd-gate가 SCAFFOLD 마커로 skip** 확인.
- **Phase β (TDD, app_repo 독립 git + 실제 훅 설치)**:
  - 백엔드: 테스트 먼저 작성 → **RED 증명**(모듈 부재로 실패 로그) → 최소 구현 → **GREEN(18 passed)**.
  - 프론트: 화면 테스트 → **RED 증명** → API 클라이언트+wiring → **GREEN(6 passed)**.
  - 커밋 시 `commit-msg` 훅이 **전체 스위트(18+6)를 실제 실행** → `tdd-gate PASS` + `commit-spine-id PASS`.
- **Phase γ (E2E)**: `JRN-TODO-MANAGE`를 **실제 브라우저(Playwright)로 4스텝 완주** + 재현용 spec 커밋(`[E2E/JRN-TODO-MANAGE]`).
- **code-review(독립 서브에이전트)**: **APPROVE-WITH-NITS**(블로킹 0). LOW 1건(화면 역토글 미검증) **즉시 보강 커밋**.

### 게이트 강제력 음성 테스트 (하네스가 나쁜 커밋을 막는지)
- 테스트 없는 구현 커밋 → `tdd-gate BLOCK` ✅
- 스파인 ID 없는 커밋 메시지 → `commit-spine-id BLOCK` ✅

### app_repo 커밋 이력 (스파인 ID 종점)
```
[spec-kit/plan]            PACK-TODO SDD 문서(Data Model·ERD·API·tasks·Gate B)
[E2E/JRN-TODO-MANAGE]      여정 Playwright + vite 프록시
[PACK-TODO/T002]           화면 wiring + API 클라이언트 (+ 역토글 보강)
[PACK-TODO/T001]           백엔드 API+저장소
[SCAFFOLD]                 Phase α 화면 shell + DS
```

---

## 3. 산출물 위치

| 항목 | 경로 |
|---|---|
| 요구사항 | `TODO-REQUIREMENTS.md` (repo root) |
| ② 계약 | `projects/todo/model_repo/{screens,entities,journeys,specs}/` |
| ③ 앱 | `projects/todo/app_repo/{backend,frontend}/` (자체 git 레포) |
| SDD 문서 | `projects/todo/app_repo/specs/PACK-TODO/{plan,tasks}.md` |
| 의사결정 로그 | `projects/todo/docs/DECISION-LOG.md` (D-001~005) |
| 결함 로그 | `projects/todo/docs/HARNESS-DEFECTS.md` (DEF-001/002 + OBS-003~005) |
| E2E 증거 | `projects/todo/docs/jrn-todo-manage-evidence.png` |

---

## 4. 발견한 하네스 결함 (상세는 HARNESS-DEFECTS.md)

| ID | 분류 | 요약 | 조치 |
|---|---|---|---|
| **DEF-001** | batch | tdd-gate/manifest-sync의 cwd 가정(`app_repo/` 접두)이 실제 훅 실행 cwd(=app_repo)와 모순. manifest-sync가 `model_repo/specs` 못 찾고 SKIP(라이브 실증) | ✅ **수정 완료** (cwd 견고 해석) |
| **DEF-002** | batch | tdd-gate 러너 자동탐지가 Node **백엔드** 미인식 → Node 풀스택 백엔드 테스트 게이트 누락 위험 | ✅ **수정 완료** (Node 백엔드 탐지 추가) |
| OBS-003 | 설계 | root .gitignore가 model_repo/app_repo 비추적 → app_repo는 **자체 레포가 정석**(훅 설치 대상과 정합). 결함 아님 | 기록(설계 의도) |
| OBS-004 | 사소 | manifest-sync 콘솔 출력 한글 mojibake | ✅ **수정 완료** (훅에 PYTHONIOENCODING) |
| OBS-005 | 환경 | 무관 파일이 첫 모노레포 커밋에 포함(`git add -A`) | 기록(브랜치라 main 무영향) |

> **하네스 개선 적용 완료(프로젝트 비의존적).** `packages/plugin-ai-web-dev/hooks/`의 `tdd-gate.py`·`manifest-sync.py`·`install-git-hooks.{sh,ps1}`를 **다음 어떤 스택/실행 위치의 프로젝트에도** 동작하도록 일반화 수정.
> **검증**: `HARNESS_TEST_CMD` 없이 자동탐지만으로 TODO(Node 풀스택)가 백엔드 18 + 프론트 6 모두 실행·green, manifest-sync 정상 동기화·한글 출력 정상, 회귀(프로젝트루트/app_repo/빈예제 3 cwd) 통과. 상세는 HARNESS-DEFECTS.md "수정 완료 요약".

---

## 5. 의사결정 요약 (상세 DECISION-LOG.md)
- **D-001** 새 프로젝트 분리 · **D-002** 경량 TS 풀스택(실행·green 우선) · **D-003** 단일 화면/엔티티/4액션 최소화 · **D-004** 인증 N/A · **D-005** app_repo 독립 레포 + 실제 훅 설치.

## 6. 결론
하네스의 **계약 정의(②)→게이트(Gate A)→발행(PACK)→SDD(plan/tasks)→TDD(RED→GREEN)→커밋 게이트→E2E→리뷰** 전 구간이
TODO 도메인에서 의도대로 작동함을 **양성(통과)·음성(차단) 모두로 확인**했다.
발견된 결함(DEF-001 cwd 정합성, DEF-002 Node 백엔드 탐지, OBS-004 한글 출력)은 **모두 프로젝트 비의존적으로 일반화 수정·검증 완료**했다.
이제 다음 프로젝트는 스택이 Node든 JVM든 Python든, 훅을 app_repo에 설치만 하면 **HARNESS_TEST_CMD 핀 없이** TDD 게이트가 자동 동작한다. 기능 결함·스파인 추적 단절은 없었다.
