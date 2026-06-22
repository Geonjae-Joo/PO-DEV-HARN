<!-- impact: speckit 정확 사용 개선의 영향도 분석 -->
<!-- status: v1 | date: 2026-06-22 | 짝 문서: PROPOSAL-speckit-correct-usage.md, GUIDE-speckit-usage.md -->

# 영향도 분석 — speckit 정확 사용 개선

> 구현 전 영향도 파악. 변경 대상·파급·리스크·롤백을 정리한다.
> 제약: 본 작업 환경에서 셸 실행이 불가(HYPERVISOR_VIRT_DISABLED)하여 스크립트는 **작성만** 하고
> 정적 검토로 검증한다. 실제 스모크 테스트는 사용자 환경(Git Bash/PowerShell)에서 1회 필요.

---

## 1. 설계 원칙 (영향 최소화)

1. **메커니즘/상태 경계 준수.** speckit 업스트림 코어(`.specify/scripts/*.sh`, `templates/*` 코어)는 **편집하지 않는다.** 신규는 추가(additive)로만.
2. **기존 패턴 재사용.** 훅은 이미 `$CLAUDE_PLUGIN_ROOT/hooks/` 에서 실행되고 `install-git-hooks.sh` 가 `.git/hooks` 래퍼를 생성한다 — 신규 훅도 같은 방식으로 배선.
3. **임계 파일 비편집.** `commit-spine-id.py`·`tdd-gate.py` 는 공유 핵심이라 손대지 않고, **별도 가드**를 체인에 추가.
4. **graceful degradation.** 신규 가드는 판정 불가 시 PASS(경고)로 동작 — 오차단 방지.

---

## 2. 변경 대상 (파일 단위)

### A. 신규 (additive, 리스크 낮음)

| 파일 | 역할 | 대응 갭 |
|---|---|---|
| `hooks/install-speckit.sh` / `.ps1` | app_repo에 `.specify` 메커니즘 vendoring + 상태 초기화 + `.source` 기록 + git hook 설치 호출 | G1 |
| `hooks/speckit-sync.sh` / `.ps1` | 플러그인 업그레이드 시 **메커니즘 디렉터리만** 재복사(상태 보존) | G1(drift) |
| `.specify/scripts/bash/pack-to-spec.py` | `spec-pack.yaml` + screen/entity/journey → `spec.md` 초안 생성 | G2 |
| `hooks/speckit-artifact-guard.py` | `[spec-kit/plan|tasks]` 커밋 시 `spec.md`/`plan.md`/`tasks.md` 실재 검사 | G4, G5 |

### B. 편집 (기존 파일, 리스크 중)

| 파일 | 변경 | 파급 |
|---|---|---|
| `hooks/install-git-hooks.sh` / `.ps1` | commit-msg 체인에 `speckit-artifact-guard.py` 추가 | 재설치 필요. 기존 app_repo는 재실행해야 적용 |
| `hooks/git-hooks.manifest.json` | artifact-guard 선언 추가(문서용) | 없음(설치기가 파싱 안 함) |
| `skills/speckit-specify/SKILL.md` | 오버레이에 "pack-to-spec 먼저 실행" + 부트스트랩 선행조건 명시 | specify 절차 강화. 원본 로직 불변(오버레이만) |

### C. 문서만 (리스크 낮음, 명시 요청)

| 파일 | 변경 |
|---|---|
| `README.md`(루트) | ③ 자산·§7·§8 에 install-speckit/speckit-sync, 메커니즘/상태 경계 반영 |
| `packages/plugin-ai-web-dev/README.md` | Commands/Hooks 표에 신규 추가 + "speckit 메커니즘/상태" 절 |
| `packages/po-dev-chat/skills/spec-generator/spec-pack-schema.md` | **권위 정합**: screen model=내용 권위, pack=묶음+ref 로 명문화 |
| `guides/SPECKIT-HARNESS-INTEGRATION.md` | §6 에 step 0(install-speckit), 메커니즘/상태·레이어 경계 절 |
| `guides/GUIDE-speckit-usage.md` | step 0 을 install-speckit 로 갱신, 레이어 경계(Q2/Q3) 추가 |
| `guides/PROPOSAL-speckit-correct-usage.md` | C1 을 "메커니즘 vendoring + sync" 로 정련, 상태 표기 |

### D. 의도적 비변경 (이유 명시)

| 파일 | 왜 안 건드리나 |
|---|---|
| `.specify/scripts/*.sh`(common·setup-plan·create-new-feature 등) | speckit 업스트림 코어 — 편집 시 업그레이드 안전성 파괴. C5 순서 강제는 코어 편집 대신 artifact-guard(커밋 경계)로 달성 |
| `commit-spine-id.py`, `tdd-gate.py` | 공유 임계 훅 — 별도 가드로 분리해 회귀 위험 차단 |
| `spec-pack-guard.py`(코드) | 셸 미실행으로 테스트 불가 → 코드 변경은 보류. C3 는 **문서 정합**으로 처리하고, 가드 강화는 테스트 환경 확보 후 후속 |
| `projects/todo/*` | 레트로핏은 대화형 `/speckit-*` 실행이 필요 → GUIDE 의 runbook 으로 사용자 실행. 본 작업에서 데이터 비변경 |

---

## 3. 파급(런타임) 분석

- **새 app_repo**: `install-speckit` → `.specify` 생성 → speckit 명령 정상 동작. 신규 경로라 회귀 없음.
- **기존 app_repo(todo 등)**: 변화 없음(스크립트 미실행 시). 적용하려면 GUIDE 레트로핏 runbook 실행.
- **커밋 체인**: artifact-guard 가 추가되지만 graceful PASS 라, `feature.json` 미해석/단계 불명 시 기존과 동일하게 통과. plan/tasks 마커인데 산출물이 없을 때만 신규 차단.
- **manifest-sync**: 변경 없음. `app_repo/specs/` 에 PACK-* 사본과 speckit `<NNN>-slug/` feature 디렉터리가 공존(하위 디렉터리 분리, 충돌 없음).

## 4. 리스크 & 완화

| 리스크 | 완화 |
|---|---|
| 셸 미실행 → 스크립트 오류 잠재 | 기존 스크립트 스타일 그대로 모사, graceful 분기, **사용자 1회 스모크 테스트 안내** |
| artifact-guard 오차단 | 판정 불가 시 PASS, plan/tasks 마커+산출물 부재일 때만 block |
| vendoring 후 drift | `speckit-sync` + `.source` 버전 기록으로 재동기화 경로 제공 |
| Windows 경로/인코딩 | `.ps1` 동반 제공, `PYTHONUTF8` 설정(기존 훅과 동일) |

## 5. 롤백

- 신규 파일 삭제 + `install-git-hooks` 원복(체인에서 artifact-guard 줄 제거 후 재설치)으로 완전 롤백. 코어/임계 훅 비편집이라 롤백 표면이 작다.

## 6. 검증 계획 (사용자 환경)

1. 빈 app_repo에서 `bash install-speckit.sh` → `.specify` 생성·`check-prerequisites.sh` 인식 확인.
2. `python pack-to-spec.py PACK-TODO` → `specs/<NNN>-*/spec.md` 초안 생성 확인.
3. `spec.md` 없이 `[spec-kit/plan]` 커밋 시도 → artifact-guard 차단 확인.
4. 정상 플로우(specify→plan→tasks) 후 동일 커밋 → 통과 확인.
