<!-- supporting-file: skills/sufficiency-check -->
<!-- loaded-by: sufficiency-check 스킬(AI gap 분석) + skills/sufficiency-check/scripts/sufficiency-check.py(기계 체크) 공통 기준 -->

# Spec-Readiness Checklist — 충분성 기준

Stage 4 sufficiency-check의 판정 기준. 스크립트(결정론)와 AI gap 분석이 동일 목록을 사용한다.
"개발자가 spec을 만들 수 있을 만큼"의 정의.

---

## 컴포넌트 레벨 (interactive: true인 모든 CMP)

| 항목 | 질문 | 미충족 심각도 | Gate A |
|---|---|---|---|
| `action` | 이 컴포넌트는 무엇을 하는가? (또는 명시적 no-op) | **error** | 차단 |
| `data_source` | 보여주거나 다루는 데이터는 어디서 오는가? (ENT-/EXT- 식별) | **error** | 차단 |
| `permission` | 누가 이 컴포넌트를 사용할 수 있는가? (기본 all) | warn | 질문 생성 |
| `empty_state` | 데이터가 0건/없음일 때 무엇을 보여주는가? | warn | 질문 생성 |
| `error_state` | 작업이 실패하면 어떻게 되는가? (export 실패, 저장 실패 등) | warn | 질문 생성 |
| `validation` | 입력 컴포넌트라면 검증 규칙은 무엇인가? | **error** (form 계열) | 차단 |
| `default_value` | 필터/입력의 초기값은 무엇인가? | warn | 질문 생성 |
| `loading_state` | 비동기 작업 중 어떤 상태를 보여주는가? | warn | 질문 생성 |

## 화면 레벨 (각 SCR- 전체)

| 항목 | 질문 | 심각도 |
|---|---|---|
| `entry` | 이 화면에는 어디서 진입하는가? (메뉴 클릭 / 타 화면 navigate / 직접 URL) | warn |
| `initial_state` | list/DataTable이 있는 화면에 `screen.initial_state`가 정의되어 있는가? (auto_query, default_filter 등) | **error** |
| `navigation_out` | 모든 navigate target(SCR-)이 실존하거나 계획에 있는가? | **error** |
| `screen_permission` | `screen.permission`이 정의되어 있는가? | warn |
| `reactive` | FilterBar와 DataTable이 같은 화면에 있는데 `reactive`가 정의되어 있는가? | warn |
| `nfr` | 성능·동시성·감사·보안 등 특이 요구가 있는가? (notes 유도) | warn |
| `nfr_detail` | `kind: nfr`인 note가 있는데 `nfr_detail`이 채워져 있는가? | warn |

## Action 레벨 (각 REQ-)

| 항목 | 질문 | 심각도 |
|---|---|---|
| `acceptance` | Gherkin 형식 acceptance criteria가 있는가? | **error** |
| `outcome_target` | navigate/mutate/export의 대상(SCR-/ENT-/EXT-)이 명확한가? | **error** |
| `user_confirmed` | PO가 acceptance를 확인했는가? | **error** |
| `error_behavior` | mutate/export/query action에 `error_behavior`가 정의되어 있는가? | **error** |
| `permission_consistency` | `action.permission`이 `screen.permission`보다 더 넓지 않은가? | **error** |
| `permission_denied_ux` | `action.permission != all`인데 `error_behavior.permission_denied`가 정의되어 있는가? | warn |

---

## 판정 규칙

```
error 항목 미충족 → sufficiency: fail → Gate A 차단
warn  항목 미충족 → open_question 생성 → HITL 재질문

open_question 처리:
  answered  → 해당 항목 충족으로 간주
  deferred  → 사유(defer_reason) 필수 → sufficiency: pass_with_deferred
              deferred 항목은 spec 팩에 그대로 포함되어 ③으로 전달

sufficiency 결과:
  pass               → Gate A 통과 가능
  pass_with_deferred → Gate A 통과 가능 (deferred 항목 팩에 포함)
  fail               → Gate A 차단 (error 항목 미해결)
```

---

## 스크립트 vs AI 역할 구분

| 방법 | 담당 | 예시 |
|---|---|---|
| 스크립트(결정론) | 기계적 존재 여부 | "CMP-X에 action이 있는가?", "acceptance가 있는가?" |
| AI gap 분석 | 의미적 누락 | "목록이 있는데 페이징/정렬 언급 없음", "삭제 action에 확인 절차 미정의" |
