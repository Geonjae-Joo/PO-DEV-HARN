# Ops Stack — 배포·CI/CD·형상관리·관측성 결정 (프로젝트별)

> **이 파일이 운영 스택의 단일 출처(single source of truth)다.**
> 형상관리(SCM)·CI/CD·배포 타깃·관측성은 **고정값이 아니다.** ① PREREQUISITE 단계에서 프로젝트마다 이 파일을 채워 확정하고, ③ Phase 0(구현)·Phase γ(검증)와 관련 훅·가이드는 여기에 적힌 결정을 따른다.
> `tech-stack.md`가 **앱 스택**(언어·프레임워크·빌드·앱 테스트)을 정한다면, 이 파일은 **운영 스택**(배포·파이프라인·관측성)을 정한다. 둘은 상호 보완이며 중복 시 ops-stack.md가 운영 영역의 우선이다.
> 무엇을(scope) 운영 요건으로 둘지의 *명세*는 `SPEC-OPS-000.md`에 있고, 이 파일은 그 명세를 *어떤 도구로* 구현할지의 **결정**이다.
> 변경 시 반드시 `DECISIONS.md`에 이유를 기록하고 이 파일을 갱신한다 (그러면 하류가 자동으로 따른다).

---

## 형상관리 (SCM)

| 항목 | 결정 | 비고 |
|---|---|---|
| 호스팅 | **GitHub** \| GitLab | 프로젝트별 선택 (택1) |
| 브랜치 전략 | trunk-based (main + 단기 feature 브랜치) | PR 필수 |
| 커밋 규칙 | `[<PACK\|SPEC\|MOD>/<task>] 요약 (REQ-...)` | ③ `commit-spine-id.py`가 강제 (commit-convention.md) |
| 보호 규칙 | main 직접 push 금지, PR 리뷰 1+ 승인 | |

## CI/CD

| 항목 | 결정 | 비고 |
|---|---|---|
| CI/CD 엔진 | **GitHub Actions** \| GitLab CI | SCM 선택에 종속 |
| CI 게이트 | build → lint → unit/통합 test → tdd-gate 통과 | PR 필수 체크 |
| E2E 게이트 | Playwright(+BDD) — JRN-* 여정 (③ Phase γ) | 머지 전 또는 nightly |
| CD 트리거 | main 머지 시 dev 자동 배포, tag 시 stg/prod | 환경별 승인 게이트 |

## 배포 타깃

> 다중 선택 가능 — 환경마다 다를 수 있음 (예: 로컬 Docker / 운영 k8s).

| 타깃 | 사용 | 산출물 |
|---|---|---|
| **Kubernetes** | (선택) 운영/스테이징 | Helm chart \| Kustomize manifests |
| **Docker 단독** | (선택) 로컬·소규모 | Dockerfile + docker-compose.yml |
| **온프렘** | (선택) 사내망/폐쇄망 | 배포 스크립트 + manifests (사내 레지스트리) |

| 항목 | 결정 | 비고 |
|---|---|---|
| 환경 | dev / stg / prod | 환경별 config 분리 |
| 시크릿 | K8s Secret \| Vault \| .env(로컬) | 평문 커밋 금지 |
| 레지스트리 | (프로젝트별: GHCR / GitLab Registry / 사내) | |

## 관측성 (Observability — LLM 트레이싱 중심)

> 대상 앱이 **LLM 기반**(예: Samsung Fabrix LLM, `langchain-fabrix`)인 경우의 트레이싱이 1차 범위다. 앱 메트릭/인프라 관측은 현 범위 밖(필요 시 SPEC-OPS-000에서 확장).

| 항목 | 결정 | 비고 |
|---|---|---|
| LLM 트레이싱 | **Arize Phoenix** \| **Langfuse** | 프로젝트별 선택 (택1) |
| 계측 지점 | 프롬프트·응답·토큰·체인/에이전트 step·지연·비용 | SPEC-OPS-000 §관측성 명세 |
| 평가/피드백 | eval run + 사용자 feedback 캡처 | (선택) |
| 대시보드 | Phoenix UI \| Langfuse UI | self-host 여부 결정 |
| 연동 방식 | LangChain/LangGraph callback handler 또는 OTel exporter | `langchain-fabrix` 스킬 참조 |

## 변경 이력

| 날짜 | 변경 | 이유 |
|---|---|---|
| 2026-06-16 | 초안 골격 생성 | ops 명세화 도입 (배포/CI·CD/관측성) |
