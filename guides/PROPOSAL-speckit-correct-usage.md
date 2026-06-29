<!-- proposal: speckit 을 시스템적으로 "정확히" 사용하기 위한 변경 제안 -->
<!-- status: draft v1 | date: 2026-06-22 | scope: 설계 제안(문서). 실제 코드/훅 변경은 별도 승인 후 -->

# speckit 정확 사용 — 시스템 변경 제안서

> 배경: 골든패스 v2에서 `/speckit-specify`·`/speckit-plan`·`/speckit-tasks` 를 거치지 않고
> `model_repo`의 `spec-pack.yaml` 을 직접 읽어 `plan.md`·`tasks.md` 를 **수작업** 작성하고
> `[spec-kit/plan]` 커밋 마커만 붙였다. 즉 "산출물은 비슷하지만 프로세스는 단락"된 상태였다.
> 이 문서는 **왜 스킵이 가능했는지(근본 원인)** 와 **무엇을 고쳐야 시스템적으로 막히는지** 를 정리한다.
>
> **구현 상태 (2026-06-22 갱신):** 사용자 승인으로 C1·C2·C4·C5 를 구현했다(아래 표의 "상태" 참조).
> C1 은 메커니즘/상태 경계에 맞춰 정련되고 C1b(speckit-sync)가 추가됐다. C3 은 셸 미실행 환경이라
> 코드 변경 대신 **문서 정합**으로 처리했다(가드 코드 강화는 테스트 환경 확보 후 후속). 영향도·검증은
> `IMPACT-speckit-fix.md`, 사용절차·레트로핏은 `GUIDE-speckit-usage.md` 참조.

---

## 0. 결론 요약

스킵이 가능했던 이유는 의지의 문제가 아니라 **구조의 문제**다. 세 가지가 동시에 비어 있었다.

1. **실행 불가** — `app_repo` 에 `.specify/` 가 설치되지 않아 speckit 명령이 애초에 돌 수 없었다. (그래서 "스킵"이 아니라 사실상 "실행 불가" 상태에서 우회했다)
2. **입력 브리지 부재** — `spec-pack.yaml` → `spec.md` 로 옮기는 **기계적 단계가 없다.** SKILL.md에 "pack에서 파생하라"는 산문 지시만 있어, 사람이 직접 plan.md를 쓰는 것과 결과가 구분되지 않았다.
3. **게이트 공백** — `commit-spine-id.py` 는 `[spec-kit/plan]` **머리말 문자열만** 검사한다. `spec.md`/`plan.md`/`tasks.md`/`feature.json` 의 실재 여부는 보지 않는다. 그래서 프로세스 없이 마커만으로 통과됐다.

아래 §1에서 근본 원인 5개(G1~G5)를 근거 파일과 함께 짚고, §2에서 대응 변경 5개(C1~C5)를 제안한다.

---

## 1. 근본 원인 (근거 파일 포함)

### G1 — `app_repo` 에 `.specify/` 부트스트랩이 없다 🔴 (최우선)

speckit의 모든 스크립트는 cwd에서 위로 올라가며 `.specify/` 를 찾아 프로젝트 루트를 정한다.

- 근거: `packages/plugin-ai-web-dev/.specify/scripts/bash/common.sh` 의 `find_specify_root()` / `get_repo_root()` — `.specify/` 가 없으면 상위 git( = `PO-DEV-HARN` 루트) 또는 스크립트 위치로 fallback 한다.
- 근거: `create-new-feature.sh` 가 `resolve_template "spec-template"` 로 `.specify/templates/spec-template.md` 를 복사하는데, `app_repo` 에 `.specify/templates` 가 없으면 빈 spec 파일만 생긴다.
- 실태: `.specify/` 는 **플러그인 소스(`packages/plugin-ai-web-dev/.specify/`)에만** 존재한다. 골든패스는 `app_repo` 를 `git init` 만 했고, 이 구조를 복사/설치하는 단계가 없다. → `projects/todo/app_repo` 에 `.specify/` 부재.

**효과:** `/speckit-specify` 가 올바른 루트도, 템플릿도 찾지 못한다. 명령이 실질적으로 동작 불가 → 우회.

### G2 — `spec-pack.yaml` → `spec.md` 기계적 브리지가 없다 🔴

- 근거: `create-new-feature.sh` 는 **자유 서술 인자**를 받아 빈 템플릿을 복사할 뿐이다.
- 근거: `skills/speckit-specify/SKILL.md` 의 "🔗 Harness Integration" 은 *"`model_repo/specs/PACK-*/spec-pack.yaml` 에서 파생한다"* 고 **산문으로만** 지시한다. pack(+screen/entity/journey)을 읽어 spec.md 슬롯을 채우는 스크립트가 없다.

**효과:** "specify를 한다"가 모호한 수작업이 되어, plan.md를 직접 쓰는 것과 산출물이 비슷해 보인다 → 스킵 유인.

### G3 — 입력 계약 불일치: `spec-pack.yaml` 이 스키마를 안 따른다 🟡

- 근거(스키마): `packages/plugin-po-define/skills/spec-generator/spec-pack-schema.md` 는 `meta`, `actions[].acceptance`(Gherkin 원문), `notes`(verbatim·complexity), `open_items`, `pinned_contract`(version·hash·layout_hash·render_hash·git_ref) 를 요구한다.
- 근거(실제): `projects/todo/model_repo/specs/PACK-TODO/spec-pack.yaml` 은 축약형이다 — `meta`·`actions`·`acceptance`·`notes`·`open_items`·`pinned_contract` 가 전부 없다. 진짜 acceptance/notes 는 `model_repo/screens/SCR-TODO-LIST.yaml` 에 들어 있다.

**효과:** specify가 "pack에서 파생"하려 해도 pack에 파생할 권위 원천(acceptance/notes/pinned_contract)이 없다. 입력 경계가 pack과 screen으로 쪼개져 있어, pack만 보면 specify를 건너뛸 명분이 생긴다.

### G4 — `[spec-kit/plan]` 마커가 프로세스와 분리돼 있다 🔴 (직접 원인)

- 근거: `packages/plugin-ai-web-dev/hooks/commit-spine-id.py` —
  `SPECKIT_RE = ^\[spec-kit/(constitution|specify|clarify|plan|tasks|analyze|checklist|taskstoissues)\]` 에 매칭되면 **무조건 `PASS (spec-kit artifact)`** 를 반환한다.
- 검사하지 않는 것: 해당 feature 디렉터리에 `spec.md`/`plan.md`/`tasks.md` 가 실재하는지, 템플릿 placeholder 가 해소됐는지, `feature.json` 이 단계를 추적하는지.

**효과:** 워크플로를 한 줄도 안 거쳐도 `[spec-kit/plan]` 머리말만 쓰면 게이트를 통과한다. v2에서 실제로 이렇게 됐다.

### G5 — 단계 순서/선행조건 강제가 없다 🟡

- 근거: `setup-plan.sh` 는 `feature.json` 이 없으면 branch-prefix fallback 으로도 `plan.md` 를 만들어 준다(`common.sh: get_feature_paths`). 빈/템플릿 상태의 `spec.md` 위에서도 plan 단계가 조용히 진행된다.
- `analyze`(= 하니스의 Gate B 일관성 검사)는 정책 문서엔 "구현 전 필수"로 적혀 있으나, 이를 **물리적으로 강제**하는 지점이 없다.

**효과:** specify→plan→tasks 의 누락이 어느 지점에서도 막히지 않는다.

---

## 2. 제안 변경 (C1~C5)

> 원칙: speckit 원본 로직은 보존하고(이디오매틱 오버레이), **빠진 실행부와 강제 지점만** 채운다.
> 우선순위: C1(실행 가능) → C4(게이트로 단락 차단) → C2(브리지) → C3(입력 정합) → C5(순서 강제).

### C1 — `app_repo` speckit 부트스트랩 (메커니즘 vendoring + 상태) 🔴 ✅구현

플러그인 `.specify/` 의 **메커니즘**을 `app_repo` 에 vendoring 하고 **상태**는 app_repo 가 소유한다(메커니즘/상태 경계, 통합가이드 §7).

- 신규: `hooks/install-speckit.sh` / `.ps1`
  - `app_repo/.specify/` 에 메커니즘(`scripts/`·`templates/`·`workflows/`·`extensions/`) + 초기 상태(`memory/constitution.md`) vendoring. **기존 파일 보존**(멱등). `.specify/.source` 에 `plugin@version`·speckit 버전 기록. 이어 `install-git-hooks.sh` 호출.
  - `.git` 없으면 `git init` 후 진행.
- DoD: `bash .specify/scripts/bash/check-prerequisites.sh --paths-only` 가 `.specify` 인식.

### C1b — `speckit-sync` (메커니즘 재동기화) 🟡 ✅구현

플러그인 업그레이드 시 drift 차단. `hooks/speckit-sync.sh` / `.ps1` 가 **메커니즘만** 재복사하고 상태(`memory/`·`feature.json`·`templates/overrides/`·`extensions/git/git-config.yml`)는 **보존**한다. `.source` 갱신.

### C2 — `spec-pack.yaml` → `spec.md` 브리지 스크립트 신설 🔴 ✅구현

specify의 "파생"을 산문에서 **기계 단계**로 승격한다. (구현: `.specify/scripts/bash/pack-to-spec.py`)

- 신규: `.specify/scripts/bash/pack-to-spec.py PACK-<ID> --feature-dir specs/<NNN>-<slug>`
  - 입력: `model_repo/specs/PACK-<ID>/spec-pack.yaml` + 거기서 ref 하는 `screens/SCR-*.yaml`·`entities/ENT-*.yaml`·`journeys/JRN-*.yaml`.
  - 출력: 하니스판 `spec-template.md` 슬롯을 채운 `spec.md` **초안** — Pack Scope(SCR-/CMP-/REQ-), acceptance(원문 verbatim), entities/journeys, notes(verbatim·complexity), open_items, pinned_contract.
  - specify는 이 초안을 **검토·범위확정·sub-pack 분할**만 담당(새 SCR-/REQ- 발명 금지 원칙 유지).
- 연동: `skills/speckit-specify/SKILL.md` 절차에 "① `pack-to-spec.py` 실행 → ② 초안 검토" 를 명시.

### C3 — `spec-pack` 스키마/권위 정합 🟡 ◐문서로 처리

입력 권위의 위치를 한 곳으로 고정한다. 두 안 중 택1.
**채택(이번):** 현 파이프라인 실태(최소형 pack + screen model 권위)에 맞춰 **안 B 를 문서로 명문화**했다 — `spec-pack-schema.md` 에 "권위 경계: screen model=내용, pack=묶음+ref" 와 최소형 예시를 추가. 가드 코드 강화(안 A)는 셸 미실행으로 보류(후속).

- **안 A (권장)** — pack을 스키마대로 풍부화. `packages/plugin-po-define/skills/spec-generator/scripts/spec-pack-guard.py` 를 강화해 `meta`·`actions[].acceptance`·`notes`·`pinned_contract` 필수 필드를 검증, 축약형 pack을 거부. `spec-generator` 가 screen model에서 이 필드들을 채워 발행하도록 한다. (추적성·`pinned_contract` freeze 때문에 권장)
- **안 B** — 입력 권위를 screen model로 일원화하고 pack은 "묶음 + ref" 만 담당하도록 `spec-pack-schema.md` 를 개정(현 todo가 사실상 이 형태). 단 `pinned_contract`·acceptance verbatim 의 단일 소스는 screen으로 명문화해야 함.

### C4 — plan/tasks 커밋 게이트를 "산출물 존재"로 강화 🔴 ✅구현 (단락 차단의 핵심)

마커만으로 통과하지 못하게 한다. **구현: 별도 훅 `speckit-artifact-guard.py` 신설**(commit-spine-id 비편집 — 임계 훅 회귀 방지). commit-msg 체인에 배선(install-git-hooks .sh/.ps1 + manifest).

- `[spec-kit/specify]` → `feature_dir/spec.md` 존재 (미수정 템플릿이면 경고).
- `[spec-kit/plan]` → `spec.md` **와** `plan.md` 존재 요구.
- `[spec-kit/tasks]` → `plan.md` **와** `tasks.md` 존재 요구.
- feature_dir 은 `.specify/feature.json` 에서 해석. 해석 불가 시 graceful PASS(오차단 방지).
- 효과: 프로세스 없이 마커만 붙인 커밋 거부 → v2 단락 재발 불가.

### C5 — 순서 강제 + analyze(Gate B) 🟡 ◐부분(커밋 경계)

- **채택:** 코어(`setup-plan.sh`)는 편집하지 않는다(업그레이드 안전). 대신 순서 강제를 **커밋 경계**에서 artifact-guard 로 달성(plan 마커인데 spec.md 없으면 차단 = specify 선행 강제). 참고로 `check-prerequisites.sh`(코어)가 이미 plan.md→tasks 순서를 검사한다.
- analyze(Gate B) CRITICAL=0 의 물리적 강제는 후속(코어 비편집 원칙상 별도 가드로 추가 예정).

---

## 3. 변경 요약 표

| ID | 무엇을 | 대상 파일 | 막는 원인 | 상태 |
|---|---|---|---|---|
| C1 | `.specify/` 부트스트랩(vendoring+상태) | `hooks/install-speckit.sh`/`.ps1`(신규) + 통합가이드 §6 | G1 | ✅ |
| C1b | 메커니즘 재동기화 | `hooks/speckit-sync.sh`/`.ps1`(신규) | G1(drift) | ✅ |
| C2 | pack→spec 브리지 | `.specify/scripts/bash/pack-to-spec.py`(신규) + specify SKILL | G2 | ✅ |
| C3 | pack 스키마/권위 정합 | `spec-pack-schema.md` 명문화(가드 강화는 후속) | G3 | ◐문서 |
| C4 | plan/tasks 커밋 산출물 검사 | `speckit-artifact-guard.py`(신규) + install-git-hooks/manifest | G4 | ✅ |
| C5 | 순서·Gate B 강제 | artifact-guard(커밋 경계) — 코어 비편집 | G5 | ◐부분 |

---

## 4. 검증(Definition of Done)

이 제안이 구현되면 다음이 **기계적으로** 성립해야 한다.

1. `.specify/` 미설치 `app_repo` 에서 `/speckit-specify` 실행 시 명확한 "부트스트랩 먼저" 안내(또는 자동 설치).
2. `spec.md` 없이 `[spec-kit/plan]` 커밋 시도 → `commit-spine-id`/`artifact-guard` 가 **차단**.
3. 축약형 `spec-pack.yaml` → `spec-pack-guard` 가 **차단**.
4. `projects/todo` 를 §사용자 가이드의 레트로핏 runbook 으로 재실행 시 specify→plan→tasks→analyze 가 모두 산출물을 남기고, `feature.json` 으로 추적이 이어진다.

> 사용 절차와 todo 레트로핏 runbook 은 `guides/GUIDE-speckit-usage.md` 참조.

## 참고 (Sources)

- `guides/SPECKIT-HARNESS-INTEGRATION.md`, `guides/PLAN-speckit-tdd-fusion.md`
- `packages/plugin-ai-web-dev/.specify/scripts/bash/{common.sh,create-new-feature.sh,setup-plan.sh}`
- `packages/plugin-ai-web-dev/.specify/extensions/git/{git-config.yml,scripts/bash/create-new-feature.sh,initialize-repo.sh}`, `.specify/extensions.yml`
- `packages/plugin-ai-web-dev/skills/speckit-specify/SKILL.md`, `.specify/workflows/speckit/workflow.yml`
- `packages/plugin-ai-web-dev/hooks/commit-spine-id.py`
- `packages/plugin-po-define/skills/spec-generator/spec-pack-schema.md`
- `projects/todo/model_repo/specs/PACK-TODO/spec-pack.yaml`, `projects/todo/model_repo/screens/SCR-TODO-LIST.yaml`, `entities/ENT-TODO.yaml`
