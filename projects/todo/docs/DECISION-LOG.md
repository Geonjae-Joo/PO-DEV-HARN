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

### D-005 — 게이트/훅은 main 레포 .git/hooks 설치 대신 "수동 실행"으로 강제 재현
- **결정**: `install-git-hooks`로 main 모노레포 `.git/hooks`를 덮어쓰지 않고, 각 게이트·커밋 시점에 해당 스크립트(tdd-gate.py·commit-spine-id.py·gate-a-check.py·spec-pack-guard.py·spine_ledger.py)를 `projects/todo/`를 cwd로 **직접 실행**해 결과를 로그.
- **근거**: ① 훅 설치 대상이 `app_repo/.git/hooks`인데 tdd-gate는 cwd 기준 `app_repo/frontend`를 탐지 → app_repo가 독립 git repo라는 가정과 모노레포 현실의 충돌. ② main 레포 전역 훅 설치는 무관한 커밋까지 영향. 수동 실행은 훅 본문 코드를 그대로 호출하므로 강제 로직 검증에 충실.
- **영향**: 실제 git 커밋은 `harn-todo-test` 브랜치에 스파인 ID 메시지로 수행하되, 커밋 전 게이트를 수동 통과 검증. (관련 결함 → HARNESS-DEFECTS)
</content>
