<!-- spec: SPEC-OPS-000 — 운영 baseline 명세 (배포·CI/CD·형상관리·관측성) -->
<!-- 작성: ① PREREQUISITE / 구현: ③ Phase 0(전달 모드 A·B) + Phase γ(검증) -->

# SPEC-OPS-000 — 운영 Baseline 명세

> SPEC-000(인증·RBAC 등 공통 *기능* baseline)과 형제 명세. 이 문서는 **배포·CI/CD·형상관리·관측성 = 공통 *운영* 요건**을 정의한다.
> **명세까지만** 한다 — *무엇이* 운영 요건인지(scope·요구사항)는 여기서, *어떤 도구로*는 `rules/ops-stack.md`, *실제 코드/파이프라인*은 ③ Phase 0가 만든다. ①은 운영 코드를 구현하지 않는다.
> 스파인: `SPEC-OPS-000`. 커밋 머리말 `[SPEC-OPS-000/T###]` (SPEC- 계열 — REQ- 면제, commit-convention.md).

---

## 0. 전달 방식 (③ Phase 0가 모드 결정)

각 운영 요건은 ③ Phase 0에서 **모드 A(가이드 코드블럭)** 또는 **모드 B(직접 코드 주입)** 로 산출된다.
판정 한 줄: "프로젝트마다 변형되나?" → 예면 A, 아니면 B. 결과는 `baseline-delivery-manifest.yaml`에 기록.
권장 기본값은 아래 각 요건의 `delivery(권장)` 열 참고.

---

## 1. 형상관리 (SCM)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-SCM-1 | 원격 저장소(GitHub \| GitLab — ops-stack.md)에 app_repo 형상관리 | 원격 연결·초기 push 완료, main 보호 규칙 설정 | B |
| OPS-SCM-2 | 커밋 규칙에 스파인 ID 강제 | `commit-spine-id.py` 훅 설치·동작 (③ install-git-hooks) | B |
| OPS-SCM-3 | 브랜치 전략·PR 규칙 문서화 | trunk-based + PR 1+ 승인 규칙 적용 | A |

## 2. CI (지속 통합)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-CI-1 | PR마다 build·lint·test 자동 실행 | 파이프라인 정의 + PR 필수 체크로 등록 | B |
| OPS-CI-2 | TDD 게이트와 정합 | 테스트 실패 시 머지 차단 (tdd-gate.py 정책 일치) | B |
| OPS-CI-3 | E2E(JRN-*) 실행 단계 | Playwright(+BDD) 잡 정의 (머지 전 또는 nightly) | B |

## 3. CD (지속 배포)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-CD-1 | 환경 분리 (dev/stg/prod) | 환경별 config·시크릿 분리, 평문 시크릿 0 | A |
| OPS-CD-2 | 배포 타깃별 산출물 (ops-stack.md) | k8s=Helm/Kustomize · Docker=compose · 온프렘=스크립트+manifests | A |
| OPS-CD-3 | 배포 트리거·롤백 | main→dev 자동, tag→stg/prod 승인 게이트, 롤백 경로 존재 | A |

## 4. 관측성 (Observability — LLM 트레이싱 중심)

> 대상 앱이 LLM 기반일 때의 트레이싱이 1차 범위. (앱 메트릭/인프라 관측은 범위 밖 — 필요 시 확장)

| ID | 요건 | 수용 기준 | delivery(권장) |
|---|---|---|---|
| OPS-OBS-1 | LLM 호출 트레이싱 (Phoenix \| Langfuse — ops-stack.md) | 프롬프트·응답·토큰·지연·비용이 트레이스로 수집 | B |
| OPS-OBS-2 | 체인/에이전트 step 가시화 | LangChain/LangGraph callback 또는 OTel exporter 연동 (langchain-fabrix 참조) | B |
| OPS-OBS-3 | 평가·피드백 캡처 | (선택) eval run + 사용자 feedback 기록 경로 | A |
| OPS-OBS-4 | 민감정보 보호 | 트레이스에서 PII·시크릿 마스킹 정책 적용 | A |

---

## 5. ③에서의 처리 흐름 (참고)

```
input/harness/ 에서 SPEC-OPS-000.md(①이 작성한 명세) + ops-stack.md(결정) 수신
  │
  ▼
/speckit.specify  요건별 전달 모드(A/B) 결정 → baseline-delivery-manifest.yaml 에 OPS-* 추가
  ├─[mode B]→ /plan → /tasks(test-first) → Gate B → /implement → commit (실제 코드: 파이프라인·트레이싱 SDK)
  └─[mode A]→ baseline-guides/<ops-feature>/SKILL.md (예시 코드블럭·패턴) → Phase β/γ가 로드
  ▼
Phase γ  배포·관측성·E2E(JRN-*) NFR 검증
```

> **①과의 경계:** *무엇이 운영 요건인지(scope)*는 이 SPEC-OPS-000이, *도구 선택*은 ops-stack.md가 정한다. *그것을 A로 줄지 B로 줄지, 실제 파이프라인/코드*는 ③ Phase 0가 만든다.
