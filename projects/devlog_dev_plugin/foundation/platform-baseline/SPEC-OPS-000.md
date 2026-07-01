<!-- spec: SPEC-OPS-000 — 운영 baseline 명세 (배포·CI/CD·형상관리) -->
<!-- 작성: ① PREREQUISITE / 구현: ③ Phase 0(전달 모드 A·B) + Phase γ(검증) -->

# SPEC-OPS-000 — 운영 Baseline 명세 (DevLog)

> SPEC-000(인증·앱 셸 등 공통 *기능* baseline)과 형제 명세. 이 문서는 **배포·CI/CD·형상관리·관측성 = 공통 *운영* 요건**을 정의한다.
> **명세까지만** 한다 — *무엇이* 운영 요건인지(scope)는 여기서, *어떤 도구로*는 `ops-stack.md`, *실제 코드/파이프라인*은 ③ Phase 0가 만든다.
> 스파인: `SPEC-OPS-000`. 커밋 머리말 `[SPEC-OPS-000/T###]`.
> 본 요건은 DevLog SRS COR-003·COR-004·COR-005 · SER-002 · PER-001에서 도출했다.

---

## 0. 전달 방식 (③ Phase 0가 모드 결정)

각 운영 요건은 모드 A(가이드) 또는 모드 B(직접 코드 주입)로 산출. 판정: "프로젝트마다 변형되나?". 결과는 `baseline-delivery-manifest.yaml`.

---

## 1. 형상관리 (SCM)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-SCM-1 | 사내 Git 원격에 app_repo 형상관리 | 원격 연결·초기 push, main 보호 규칙 | B |
| OPS-SCM-2 | 커밋 규칙에 스파인 ID 강제 | `commit-spine-id.py` 훅 설치·동작 (③ install-git-hooks) | B |
| OPS-SCM-3 | `.env` git 제외 + `.env.example` 포함 (SER-002) | `.gitignore`에 `.env`, `.env.example`는 키만 정의 | B |

## 2. CI (지속 통합) — QAR-001

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-CI-1 | PR마다 build·lint·test 자동 실행 | `npm run build`·`npm run lint`(에러 0)·`vitest` 파이프라인 + PR 필수 체크 | B |
| OPS-CI-2 | TDD 게이트와 정합 | 테스트 실패 시 머지 차단 (tdd-gate.py 정책 일치) | B |
| OPS-CI-3 | E2E(JRN-*) 실행 단계 | Playwright 잡 정의 (머지 전 또는 nightly) | B |

## 3. CD (지속 배포) — COR-003 · COR-004

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-CD-1 | Standalone 빌드 산출 | `output:"standalone"`, `.next/standalone/` 생성, 200MB 이내 권장 (COR-003) | B |
| OPS-CD-2 | PM2 프로세스 운영 | `ecosystem.config.js`, 무중단 재시작, 로그 회전 (COR-004) | A |
| OPS-CD-3 | DB 스키마 동기화·시드 | `npm run db:push` + `npm run seed`(글 6+개) 배포 절차 문서화 (COR-005·DAR-003) | A |
| OPS-CD-4 | 환경 분리 (dev/stg/prod) | 환경별 `.env` 분리, 평문 시크릿 0 (SER-002) | A |

## 4. 관측성 (Observability) — 최소 범위

> **DevLog는 LLM 기반 앱이 아니므로 LLM 트레이싱은 범위 밖.** PM2 로그 + 콘솔 에러 0 수준으로 한정한다.

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-OBS-1 | 앱 로그 수집 | PM2 stdout/stderr 로그 회전 설정 | A |
| OPS-OBS-2 | 에러 가시성 | 브라우저·서버 콘솔 비정상 에러 0건 (QAR-005) | A |
| OPS-OBS-3 | 성능 확인 | 메인 LCP 로컬 1초 이내 (Lighthouse/수동) (PER-001) | A |

---

## 5. ③ 처리 흐름 (참고)

```
SPEC-OPS-000.md(이 명세) + ops-stack.md(결정) 수신
  │
  ▼
/speckit.specify  요건별 전달 모드(A/B) 결정 → baseline-delivery-manifest.yaml 에 OPS-* 추가
  ├─[mode B]→ /plan → /tasks → Gate B → /implement → commit (CI 파이프라인·next.config standalone·gitignore)
  └─[mode A]→ baseline-guides/<ops-feature>/SKILL.md (PM2 ecosystem·배포 절차 패턴)
  ▼
Phase γ  배포·E2E(JRN-*)·성능(LCP) NFR 검증
```

> **①과의 경계:** *무엇이 운영 요건인지(scope)*는 이 명세가, *도구 선택*은 ops-stack.md가 정한다. *A/B 결정·실제 파이프라인*은 ③ Phase 0가 만든다.
