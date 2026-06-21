# Spine IDs — 스파인 ID 채번 규칙

전 레이어 공통 적용. 모든 아티팩트는 스파인 ID를 가진다.
추적 그래프: `DP → SCR → CMP → REQ → acceptance → PACK → task → test → commit`
- 인스턴스화 분기: `DP- → SCR- (② instantiate_screen.py가 DP를 SCR로 인스턴스화, provenance 엣지)`
- 데이터 분기: `REQ/action → ENT-/EXT- (② 계약) → data-model·ERD (③ 파생) → migration`
- 여정 분기: `JRN- (② navigate 집계) → SCR/action → Playwright e2e-test (③ Phase γ)`

### DP- → SCR- 인스턴스화 엣지 (ADR-002 §6)
DP가 SCR로 **인스턴스화**될 때, 그 출처(provenance) 엣지가 `link-manifest.yaml`에 기록된다.
- `instantiate_screen.py`가 PO가 고른 design page로부터 새 화면 골격을 만들며 `SCR-{DOMAIN}-{TYPE}`를 채번한다.
- 채번은 `spine_ledger.py`의 `mint_scr_id`가 수행 — model_repo 전체를 스캔해 **전역 유일**을 검증(충돌 시 에러).
- 산출된 SCR에는 `screen.from_template: { page, version }` 핀이 박히고, `link-manifest.yaml`의 `screens[]`에 `template` + `from_template` 엣지가 기록되어 DP→SCR 추적이 성립한다.
- DP 원본 YAML은 절대 수정되지 않는다(고정 구성은 참조 상속, 빈 캔버스만 SCR이 소유).

---

## ID 접두사 체계

| 접두사 | 대상 | 예시 | 채번 주체 |
|---|---|---|---|
| `DP-` | design page 템플릿 | `DP-MAIN`, `DP-POPUP` | ① |
| `SCR-` | 화면(screen model) | `SCR-ORDER-LIST` | ② |
| `CMP-` | 컴포넌트 인스턴스 | `CMP-ORDER-LIST.exportBtn` | ② |
| `REQ-` | 요구사항(action) | `REQ-ORDER-LIST.001` | ② |
| `ENT-` | 개념 데이터 엔티티 계약 | `ENT-ORDER` | ② |
| `EXT-` | 외부 연동 시스템 계약 | `EXT-PAYMENT` | ② |
| `NOTE-` | 노트 | `NOTE-ORDER-LIST.001` | ② |
| `NFR-` | 비기능 요구사항 | `NFR-ORDER-LIST.001` | ② |
| `JRN-` | 화면 간 사용자 여정(=E2E 시나리오) | `JRN-ORDER-REFUND` | ② |
| `Q-` | HITL 질문 | `Q-001` | ② |
| `PRM-` | prompt log 항목 | `PRM-0001` | ② |
| `PACK-` | 도메인 spec 팩(도메인 모듈) | `PACK-ORDER`, `PACK-AUTH` | ② |
| `SPEC-` | 플랫폼/baseline spec | `SPEC-000`, `SPEC-OPS-000` | ① |
| `T` | 태스크(3자리) | `T001`, `T012` | ③ |

> **PACK- vs SPEC- 구분:** 도메인 화면·기능을 묶은 ②의 계약 팩은 `PACK-`(예: `PACK-ORDER`). 로그인·SSO·RBAC 등 공통 baseline은 ①이 명세하는 `SPEC-`(현재 `SPEC-000` 1개). 커밋 머리말은 `[PACK-…/T###]` 또는 `[SPEC-000/T###]`을 쓴다 (③ commit-convention.md).

---

## 형식 규칙

### SCR-
```
SCR-{도메인}-{화면타입}
예: SCR-ORDER-LIST / SCR-ORDER-DETAIL / SCR-ADMIN-ORDER / SCR-LOGIN
```
화면타입: LIST | DETAIL | CREATE | EDIT | ADMIN | DASHBOARD | POPUP | WIZARD

### CMP-
```
CMP-{SCR도메인+타입}.{컴포넌트역할camelCase}
예: CMP-ORDER-LIST.exportBtn / CMP-ORDER-LIST.filterbar / CMP-ORDER-LIST.table
```
동일 DS 컴포넌트를 같은 화면에서 여러 번 사용 시 숫자 접미사: `.filterbar1`, `.filterbar2`

### REQ- / NOTE- / NFR-
```
REQ-{SCR도메인+타입}.{3자리 순번}
예: REQ-ORDER-LIST.001 / NOTE-ORDER-LIST.001 / NFR-ORDER-LIST.001
```
삭제 시 결번 유지(재사용 금지).

### PACK-
```
PACK-{도메인}[-{액터}]
예: PACK-ORDER / PACK-ORDER-ADMIN / PACK-MEMBER / PACK-AUTH / PACK-DASHBOARD
```
Actor가 달라 API 권한 구조가 다를 때만 접미사 추가.

### SPEC-
```
SPEC-{3자리} 또는 SPEC-{영역}-{3자리}
예: SPEC-000 (공통 기능 baseline — 로그인/SSO/RBAC/admin)
    SPEC-OPS-000 (운영 baseline — 배포/CI·CD/형상관리/관측성)
```
SPEC-은 ①이 명세하고 ③ Phase 0가 구현하는 플랫폼 baseline 전용. 도메인 계약은 PACK-을 쓴다.

### ENT- / EXT-
```
ENT-{도메인명}            예: ENT-ORDER / ENT-MEMBER / ENT-PRODUCT
EXT-{시스템명}            예: EXT-PAYMENT / EXT-SSO / EXT-FABRIX
```
ENT-은 개념 데이터 엔티티(의미 + 핵심 속성 + 관계)의 단일 진실원 계약, EXT-은 외부 연동(엔드포인트·인증·실패정책) 계약.
②가 *계약*까지만(타입·테이블 등 물리 설계 없음), ③ Phase β가 ERD·data-model로 *파생*한다. action의 `outcome.target`이 이 ID를 참조한다(sufficiency-check가 ENT-/EXT- 형식 검증).

### JRN-
```
JRN-{도메인}-{시나리오}    예: JRN-ORDER-REFUND / JRN-MEMBER-SIGNUP
```
화면 간 사용자 여정(=E2E 시나리오). ②가 navigate action을 집계해 정의, ③ Phase γ가 Playwright(+BDD) E2E로 구현. step은 각 화면 action의 acceptance(Gherkin) 재사용.

### T (Task)
```
T{3자리 순번} — 팩 내 순번
T001: [TEST] ExportService 단위 테스트
T002: [IMPL] ExportService 구현
```
테스트 태스크(T###)와 구현 태스크(T###)는 같은 번호 체계. 접두사 [TEST]/[IMPL]로 구분.

### DP-
```
DP-{페이지타입}[-{변형}]
DP-MAIN / DP-POPUP / DP-LIST / DP-DETAIL / DP-FORM / DP-WIZARD
```

---

## 불변 원칙

1. **결번 유지**: 삭제된 ID는 재사용하지 않는다.
2. **전역 유일**: 같은 접두사 내에서 중복 금지. **기계 강제**: `harness-core/lib/spine_ledger.py` 가 model_repo 전체를 스캔해 파일을 가로지르는 중복을 탐지하며, Gate A(`gate-a-check.py` 조건 6)에서 중복 시 차단한다.
3. **자동 채번 금지**: AI가 임의로 ID를 발명하지 않는다. link-manifest.yaml의 다음 번호를 참조한다. `spine_ledger.py --reconcile` 로 관측 ID 기준 카운터를 원장에 반영하며, `check` 모드가 카운터 드리프트를 경고한다.
4. **커밋에 포함**: 모든 커밋 메시지에 관련 스파인 ID가 포함되어야 한다. (③ `commit-spine-id.py` 가 강제)
5. **해시 제외 필드**: prompt_log, provenance, intake는 해시 계산에서 제외. 해시는 semantic 필드만(layout·actions·notes body).
