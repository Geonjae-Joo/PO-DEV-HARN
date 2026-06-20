# TODO 리허설 — 의사결정 로그

> 골드패스 엔드투엔드 리허설 중 작성자(AI)가 내린 모든 판단을 시간순으로 기록한다.
> 각 항목: 결정 / 맥락 / 근거 / 영향.

---

### D-001 — 새 프로젝트 `projects/todo/`로 분리 (example 재사용 아님)
- **결정**: 기존 `projects/example`(PACK-ORDER)을 건드리지 않고 멀티테넌트 패턴대로 `projects/todo/`를 신규 생성.
- **근거**: README §8이 `<customer-id>/`로 증식하는 멀티테넌트 구조를 명시. 도메인 혼합 방지, 골드패스 1회 완주를 깨끗이 관측.
- **영향**: foundation의 DS 자산(ds-allowlist, design-pages)은 범용이므로 복사 재사용. 무거운 `ds-source/node_modules`는 복사 제외(lint는 ds-allowlist.md만 읽음).

### D-002 — 기술 스택: 경량 TypeScript 풀스택 (Node/Express + React/Vite)
- **결정**: 예제의 Java/Spring+React 핀 대신 Node+Express+TS(백) / React+Vite+TS(프론트), 테스트는 Vitest 단일 생태계 + Supertest + Testing Library + Playwright.
- **맥락**: constitution 원칙 8 — 스택은 하네스 고정값이 아니라 ① 프로젝트별 결정. 툴체인 확인 결과 node22/npm11/python3.14/java17 모두 가용.
- **근거**: "간단한 TODO"를 **실제로 실행해 green까지** 보이는 것이 DoD. Java/Gradle은 네트워크 의존 의존성 다운로드·중량으로 리허설에 과함. Node는 빠르고, tdd-policy가 요구하는 2계층(API+화면) 테스트 구조를 그대로 만족.
- **영향**: tdd-gate의 백엔드 러너 자동탐지는 JVM/Maven/pytest/go만 지원 → Node 백엔드 미탐지. `HARNESS_TEST_CMD`로 우회 예정. (관련 결함 후보 → HARNESS-DEFECTS 확인)

### D-003 — 도메인 최소화: 단일 화면 / 단일 엔티티 / 4 액션
- **결정**: `SCR-TODO-LIST` 1개, `ENT-TODO` 1개, 액션 4개(추가/토글/삭제/필터). 상세·생성 별도 화면 및 navigate 분기 없음.
- **근거**: "간단한" 요청 충실 + 모든 게이트를 한 번씩 통과하기 충분. 완료 토글이 ACTIVE↔COMPLETED 상태머신을 제공 → tdd-policy "전이 전수 커버" 요건 충족. 단일 화면이라 navigate dangling-ref 위험 제거.
- **영향**: JRN-는 단일 화면 다단계 여정으로 구성(스키마상 step.screen+action이면 충분).

### D-004 — 인증/RBAC(SPEC-000)는 Phase 0에서 N/A 처리
- **결정**: 단일 사용자 로컬 앱 가정 → 로그인/SSO/RBAC/감사 baseline 기능을 구현하지 않고 `baseline-delivery-manifest.yaml`에 N/A 사유 기록.
- **근거**: SPEC-000은 "무엇이 공통기능인지"까지만 명세하고 모드 A/B 결정은 ③ Phase 0 권한. 본 도메인은 인증 경계가 없으므로 도입은 과설계(R3 over-spec).
- **영향**: 화면/액션 permission은 모두 `all`. sufficiency-check의 permission 일관성 오류 회피.

### D-005 (개정) — ② 게이트는 수동 실행 검증, ③ 게이트는 app_repo 독립 레포 + 실제 훅 설치로 발화
- **맥락 발견**: root `.gitignore`가 `projects/*/app_repo/**`·`model_repo/*`를 의도적으로 무시 → app_repo는 모노레포 일부가 아니라 **자체 git 레포**로 설계됨(훅 설치 대상 `app_repo/.git/hooks`와 정합). Tier-3 산출물은 재생성 가능 출력으로 비추적.
- **결정**:
  - **② 검증**(schema-validate·lint·sufficiency·gate-a·spec-pack-guard·spine_ledger): `projects/todo/`를 cwd로 스크립트 직접 실행해 통과 확인(완료, 모두 green). 이 산출물은 모노레포에서 비추적이므로 별도 커밋 없음.
  - **③ 게이트**(tdd-gate·commit-spine-id·manifest-sync): `projects/todo/app_repo`를 **독립 git 레포로 init**하고 `install-git-hooks.sh`로 실제 설치 → SCAFFOLD/TDD 커밋에서 훅이 **진짜로 발화**. 의도된 설계 그대로.
  - **모노레포 커밋**: 추적 대상(foundation 결정·docs·매니페스트)만 `harn-todo-test`에 커밋.
- **근거**: 실제 설계 구조를 따르는 것이 하네스 테스트로 가장 충실하고, 훅 강제 로직을 코드 그대로 발화시켜 검증한다. 부수적으로 cwd-가정 결함(DEF-001)을 구체적으로 드러낸다.
- **영향**: ③ 훅의 cwd=app_repo 기준에 맞춰 `HARNESS_TEST_CMD`를 app_repo 상대경로(`cd backend && ... && cd ../frontend && ...`)로 설치. tech-stack.md의 `app_repo/` 접두 예시는 프로젝트-루트 cwd 가정이라 부적합(DEF-001).
</content>
