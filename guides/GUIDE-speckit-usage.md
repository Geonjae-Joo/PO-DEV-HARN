<!-- guide: speckit 사용자 가이드 — 올바른 명령 순서 + projects/todo 레트로핏 runbook -->
<!-- status: v1 | date: 2026-06-22 | 짝 문서: guides/PROPOSAL-speckit-correct-usage.md -->

# speckit 사용자 가이드

> 대상: `spec-pack.yaml` + screen model 을 입력으로 ③ AI-WEB-DEV 레이어에서 화면을 구현하는 사용자.
> 목표: **specify→plan→tasks→implement 를 빠짐없이** 거쳐, 커밋 추적(spine ID)이 끊기지 않게 한다.
> 시스템 변경(왜 이렇게 고쳤는가)은 `guides/PROPOSAL-speckit-correct-usage.md` 참조.

---

## 1. 한눈에 보는 전체 흐름

```
[1회 셋업: app_repo 당]
  0) install-speckit.sh      .specify/ 설치 + git hook 설치      ← 빠지면 아무 speckit 명령도 못 돈다
  1) /speckit-constitution   ① tech-stack·하드룰 동기화
                                                                  
[팩마다 반복: PACK-* 당]
  2) /speckit-specify PACK-X  pack+screen → spec.md (범위확정)    ┐
  3) /speckit-clarify         open_items·모호점 HITL              │ 설계
  4) /speckit-plan            Data Model·ERD·API·wiring           │
  5) /speckit-tasks           T### test-first 분해                ┘
  6) /speckit-analyze         ★ Gate B 일관성 검사 (CRITICAL=0)
  7) /speckit-checklist       Gate B 체크리스트 → 개발자 approve
  8) /speckit-implement       T### 1개씩 RED→GREEN→REFACTOR→COMMIT
  9) code-reviewer → PR → Phase γ(통합·E2E)
```

핵심 규칙 세 가지:

- **0번을 건너뛰지 않는다.** `app_repo` 에 `.specify/` 가 없으면 speckit 명령은 루트도 템플릿도 못 찾는다. 이게 v2에서 specify를 못 돌린 진짜 이유다.
- **2~5번을 직접 손으로 쓰지 않는다.** `plan.md`·`tasks.md` 를 수작업으로 만들고 `[spec-kit/plan]` 커밋 마커만 붙이는 것은 **프로세스 단락**이다. 반드시 명령으로 생성해 `feature.json` 추적을 남긴다.
- **커밋 머리말은 산출물이 실재할 때만 쓴다.** `[spec-kit/plan]` 은 `spec.md`+`plan.md` 가 있을 때, 코드 커밋 `[PACK-X/T###] … (REQ-…)` 은 대응 테스트가 통과할 때만.

---

## 2. 단계별 사용법

### 0) 1회 셋업 (`app_repo` 루트에서)

```bash
# .specify 메커니즘 vendoring + .source 기록 + git hook 설치 (멱등)
bash "$CLAUDE_PLUGIN_ROOT/hooks/install-speckit.sh"
#   Windows(PowerShell): powershell -File "$env:CLAUDE_PLUGIN_ROOT\hooks\install-speckit.ps1"
#   → app_repo/.specify/ (templates·scripts·workflows·memory·extensions) vendoring
#   → app_repo/.specify/.source (plugin@version 핀)
#   → .git/hooks/commit-msg (tdd-gate + commit-spine-id + speckit-artifact-guard), post-commit (manifest-sync)

# 확인
bash .specify/scripts/bash/check-prerequisites.sh --paths-only   # .specify 인식되면 OK
```

> 플러그인 업그레이드 후에는 `speckit-sync.sh/.ps1` 로 메커니즘만 재동기화한다(상태 보존). `.specify/` 의 메커니즘(scripts·templates 코어·workflows)은 플러그인이 원본, `memory/constitution.md`·`feature.json`·`templates/overrides/` 는 app_repo 상태다.

### 1) `/speckit-constitution`

① PREREQUISITE 의 하드룰과 tech-stack(프론트/백엔드/테스트 러너)을 `.specify/memory/constitution.md` 로 동기화한다. 이후 모든 명령이 이 파일을 권위로 읽는다.

### 2) `/speckit-specify PACK-<ID>`

`model_repo/specs/PACK-<ID>/spec-pack.yaml` 과 거기서 ref 하는 screen/entity/journey YAML에서 `spec.md` 를 파생한다. 파생은 기계 단계로 시작한다:

```bash
python "$CLAUDE_PLUGIN_ROOT/.specify/scripts/bash/pack-to-spec.py" PACK-<ID> --feature-dir specs/<NNN>-<slug>
```

이 초안을 specify 가 검토·범위확정·sub-pack 분할한다. **새 SCR-/REQ- 발명 금지.** acceptance 본문의 권위는 screen model(`SCR-*.yaml`), 데이터 계약은 `ENT-`, 여정은 `JRN-` — pack 은 묶음+ref 다. 결과로 `specs/<NNN>-<slug>/spec.md` 와 `.specify/feature.json` 이 생긴다(이 feature.json 이 이후 단계·artifact-guard 의 추적 기준).

### 3) `/speckit-clarify`

pack의 `open_items`(deferred `Q-`)와 acceptance 모호점을 최대 5문항 HITL로 좁혀 `spec.md` 에 반영. ②의 verbatim 노트 본문은 수정하지 않는다.

### 4) `/speckit-plan`

도메인 Data Model·ERD·API·frontend wiring 설계(`plan.md`, `data-model.md`, `contracts/`). `complexity:high` 노트는 `bl-analyst` 로 위임. layout(②의 계약)은 건드리지 않는다.

### 5) `/speckit-tasks`

T### test-first 분해(`tasks.md`). API+화면 2계층, `[P]` 병렬 마커, 각 task에 REQ-/T### 스파인 ID 연결.

### 6) `/speckit-analyze` (= Gate B)

`spec`+`plan`+`tasks`+`constitution` 일관성 검사(read-only). constitution 위반은 CRITICAL. **CRITICAL=0 이 되기 전 `/speckit-implement` 금지.**

### 7) `/speckit-checklist` → approve

Gate B 체크리스트로 개발자가 명시적으로 approve.

### 8) `/speckit-implement`

T### 1개씩 RED(실패 테스트 + 실패 로그 증빙) → GREEN(최소 구현) → REFACTOR → COMMIT. 커밋은 `[PACK-X/T###] 요약 (REQ-…)`. `tdd-gate.py` + `commit-spine-id.py` 가 강제한다.

---

## 3. `projects/todo` 레트로핏 runbook

> v2의 `projects/todo` 는 (a) `app_repo` 에 `.specify/` 가 없고, (b) `spec-pack.yaml` 이 축약형이며, (c) `plan.md`/`tasks.md` 가 수작업이라 `feature.json` 추적이 없다.
> 아래는 이를 **정상 speckit 흐름으로 재실행**하는 절차다. (본 문서 작성 시점에는 실행하지 않고 절차만 기술 — 실행은 사용자 승인 후)

### 사전 진단

```bash
ls projects/todo/app_repo/.specify        # 없음 → G1 확인
cat projects/todo/model_repo/specs/PACK-TODO/spec-pack.yaml   # meta/actions/acceptance/pinned_contract 없음 → G3 확인
git -C projects/todo/app_repo log --oneline | grep spec-kit   # [spec-kit/plan] 수동 커밋 확인
```

### 단계

1. **부트스트랩(C1).** `app_repo` 에 `.specify/` 설치 + git hook 설치.
   ```bash
   cd projects/todo/app_repo
   bash <플러그인경로>/hooks/install-speckit.sh
   bash .specify/scripts/bash/check-prerequisites.sh
   ```

2. **입력 정합(C3).** `PACK-TODO` 를 스키마대로 재발행하거나(권장: spec-generator 재실행), 최소한 screen model(`SCR-TODO-LIST.yaml`)의 acceptance/notes 가 pack에서 ref 되도록 보정. 현 `spec-pack.yaml` 의 `requirements`/`api_contracts` 와 screen의 `requirements[].api`·`validation`·`error_behavior`·`notes` 가 일치하는지 확인.
   - 참고 매핑(이미 존재): REQ-TODO-LIST.001(추가/POST), .002(토글/PATCH), .003(삭제/DELETE), .004(필터/GET) · ENT-TODO(v2: priority+createdAt) · JRN-TODO-MANAGE.

3. **정식 워크플로 재실행.**
   ```
   /speckit-specify PACK-TODO 할 일 목록 — 추가/토글/삭제/필터, priority, dark mode
   /speckit-clarify
   /speckit-plan
   /speckit-tasks
   /speckit-analyze      # CRITICAL=0 확인
   /speckit-checklist    # approve
   ```
   → `specs/001-todo-list/` 아래 `spec.md`·`plan.md`·`tasks.md` 와 `.specify/feature.json` 이 생성되어 추적이 이어진다.

4. **기존 수동 커밋 정리.** v2의 `[spec-kit/plan]` 수동 문서 커밋은 위 명령이 생성한 정식 산출물 커밋으로 대체된다(자동 커밋 메시지는 `git-config.yml` 의 `[spec-kit/specify|plan|tasks]` 규약을 그대로 사용).

5. **구현 정합 확인.** 코드는 이미 있으므로(테스트 26개 통과), `tasks.md` 의 각 T### 가 실제 테스트/구현과 1:1 추적되는지 `code-reviewer` 로 사후 검증. 끊긴 추적이 있으면 해당 T### 만 보정.

### 레트로핏 완료 기준

- `app_repo/.specify/feature.json` 이 `specs/001-todo-list` 를 가리킨다.
- `spec.md`(acceptance verbatim)·`plan.md`(Data Model/ERD/API)·`tasks.md`(T### + REQ- 연결) 가 모두 존재.
- `git log` 의 `[spec-kit/*]` 커밋이 실제 산출물 추가와 1:1 대응한다(마커만 있는 커밋 0건).
- `/speckit-analyze` CRITICAL=0.

---

## 4. 자주 하는 실수 (안티패턴)

| 안티패턴 | 왜 문제 | 올바른 방법 |
|---|---|---|
| `app_repo` 에 `.specify/` 없이 시작 | speckit 명령이 루트·템플릿을 못 찾음 | 0번 부트스트랩 먼저 |
| `plan.md`·`tasks.md` 수작업 작성 | `feature.json` 추적 없음, 프로세스 단락 | `/speckit-plan`·`/speckit-tasks` 로 생성 |
| `[spec-kit/plan]` 마커만 붙이기 | 산출물 없이 게이트 통과 | spec.md+plan.md 실재 후 커밋 |
| pack 축약형으로 작성 | specify가 파생할 acceptance 원천 부재 | 스키마(`spec-pack-schema.md`) 준수 |
| analyze 건너뛰고 implement | constitution 위반 미검출 | Gate B(CRITICAL=0) 후 구현 |

## 참고 (Sources)

- `guides/PROPOSAL-speckit-correct-usage.md` (시스템 변경 근거)
- `guides/SPECKIT-HARNESS-INTEGRATION.md` §1·§6, `guides/PLAN-speckit-tdd-fusion.md` §3
- `packages/plugin-ai-web-dev/skills/speckit-*/SKILL.md`, `.specify/workflows/speckit/workflow.yml`
- `projects/todo/model_repo/specs/PACK-TODO/spec-pack.yaml`, `screens/SCR-TODO-LIST.yaml`, `entities/ENT-TODO.yaml`, `journeys/JRN-TODO-MANAGE.yaml`
