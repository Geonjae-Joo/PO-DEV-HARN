<!-- 분석 리포트: screen-model-schema-v2 §7(DP 변종)과 공통 action 정의 위치 -->
<!-- 작성 기준: packages/harness-core/rules/screen-model-schema-v2.md, docs/ADR-001, docs/ADR-002, 인스턴스화/린트 구현체 실측 -->

# 리포트 — DP를 "변종"으로 만든 이유와 공통 기능 action의 정의 위치

## 0. 요약 (TL;DR)

질문은 두 가지였다. (1) **왜 DP를 screen model의 변종으로 따로 만들어 복사·인스턴스화하는가?** (2) **그러면 공통 기능의 action은 어디에 정의하는가? 모든 screen model에 다 넣는 건 아닐 것 같은데, 그래서 이런 구조인가?**

핵심 답:

- DP를 "같은 스키마의 부분집합(변종)"으로 만든 이유는 **②가 화면을 `복사해서 시작`하기 위해서**다. 복사가 무손실로 자연스러우려면 DP의 `layout`이 SCR의 `layout`과 동일한 형태여야 한다. 동시에 DP는 여러 화면이 재사용하는 **재사용 템플릿**이므로, 화면 고유 정보(`actions`/`notes`/`prompt_log`/`intake`/`screen`)는 의도적으로 **뺐다**. 그래서 "같은 스키마, 부분집합" = 변종이 됐다.
- 당신의 직관은 정확하다. 공통 action을 **모든 screen model에 복제하는 것은 이 아키텍처가 명시적으로 금지**한다(드리프트·이중관리 회피). 그리고 **DP에도 action을 넣지 않는다**(DP는 "데이터·이벤트 없는 빈 골격").
- 그렇다면 공통 action의 실제 집은 **`SPEC-000`**(`foundation/platform-baseline/SPEC-000.md`, 공통 기능 baseline)이다. 헤더·내비·로그아웃 같은 셸 동작은 §3 앱 셸(FEAT-SHELL-*), 감사·전역 에러/빈/로딩 상태는 §4(FEAT-AUDIT/ERR-*)에 **한 번** 명세하고 ③ Phase 0가 구현한다. ②의 `SCR.actions`는 **편집 캔버스(도메인) 동작만** 담는다.
- 즉 메커니즘 자체는 일관적이고 의도적이다. 다만 **DP(잠긴 골격)와 SPEC-000(셸 동작 명세) 사이의 연결이 산문(prose)일 뿐 기계적으로 강제되지 않는 간극**이 있고, **"부분적으로만 공통"인 action(준공통)의 집이 없는** 실질적 공백이 있다. 개선점은 §6에 정리했다.

---

## 1. DP는 왜 별도 "변종"인가 — 설계 의도

### 1.1 직접적 이유: "복사해서 시작"을 무손실로 만들기 위함

`screen-model-schema-v2.md` §7은 DP를 화면 스키마의 **부분집합 변종**으로 규정한다. DP가 갖는 것은 *식별/캔버스 메타 + `layout`(SCR과 동일 형태)*뿐이고, `screen` 블록·`actions`·`notes`·`prompt_log`·`intake`는 갖지 않는다. 근거가 §7에 직접 적혀 있다:

> "②가 화면을 시작할 때 **DP를 복사해서 시작**하므로 … 이 스키마의 `layout` 부분을 그대로 공유한다. 같은 스키마여야 복사가 자연스럽다. DP는 화면(SCR)의 *부분집합*이다."

`design-page-builder` 스킬도 같은 말을 한다: "DP는 ②의 화면 모델과 **같은 스키마**로 작성한다. 이유는 ②가 화면을 시작할 때 DP를 복사해서 시작하기 때문이다."

### 1.2 이 구조가 메우는 갭 (ADR-002 P5)

원래 구조에는 인스턴스화가 없었다. ADR-002 §1 P5와 §6.1이 실측 갭을 기록한다:

> "현 구조는 DP를 복사·상속하지 않는다. 실제 `SCR-TODO-LIST.yaml`은 `template.page: DP-MAIN`만 이름 참조하고, DP-MAIN의 고정 구성(Header·Breadcrumb·Footer)은 **상속되지 않고 사라진다.**"

결과적으로 PO는 "DP를 골랐는데 화면은 백지"인 문제를 겪었다. 이를 해결하려고 **인스턴스화(instantiation)**를 정식 단계로 추가하면서, 복사 대상인 DP가 SCR과 동일 `layout` 스키마를 갖도록 통일한 것이 "변종"의 출발점이다.

### 1.3 왜 DP에는 action을 안 넣는가 (재사용성 보존)

DP는 `DP-MAIN`·`DP-POPUP`처럼 **여러 화면이 공유하는 템플릿**이다. 만약 DP에 특정 화면의 행위를 박아 넣으면 재사용이 깨진다. 그래서 §7과 design-page-builder가 공통으로 "**빈 골격 — 데이터·이벤트·비즈니스 로직 금지**"를 강제한다. 이 "행위 없음" 원칙이 곧 당신이 짚은 질문("그럼 공통 action은 어디에?")의 출발점이다.

---

## 2. 인스턴스화 메커니즘 — locked 참조 + editable 복사

`instantiate_screen.py`(`harness-core/render/`)가 DP→SCR 시작 시 두 갈래로 동작한다. 이건 단순 복사가 아니라 **두 종류 슬롯을 다르게 처리**하는 것이 핵심이다.

| DP slot | 동작 | SCR에서의 결과 | 근거 |
|---|---|---|---|
| **locked** (`editable: false`) | 복제하지 않고 **DP 참조 상속** | `SCR.layout`에 **없음**. 렌더 시 DP에서 읽어 그림. SCR이 편집 불가 | `seed_layout()`이 locked 슬롯 아이템을 `continue`로 건너뜀 |
| **editable** (`editable: true`) | DP 아이템을 **`SCR.layout`으로 복사 시딩** | `CMP-<SCR>.<name>`으로 재채번, `source/position/props` 보존, `meta.seeded_from` 기록 | `seed_layout()`이 시드 아이템 생성 |

설계상의 이점(ADR-002 §6.3, ADR-001 D3 "복사 대신 참조"와 정합):

- **locked = 참조** → 단일 출처 유지, 드리프트 0. DP 1개만 고치면 전 화면에 전파.
- **editable = 복사** → PO가 온전히 소유·편집하는 캔버스. 첫 렌더가 DP와 동일(이름·메타 제외).
- **결정성 계약 무손상**: `layout_hash`는 `SCR.layout`(= editable 복사분)만 해시한다. locked는 `SCR.layout`에 없으므로 기존 결정론 계약과 호환(§7, ADR-002 D8).

여기서 **중요한 귀결**: locked 컴포넌트(Header, Footer, 팝업의 닫기 버튼 등)는 **어떤 SCR의 `layout`에도 CMP-id로 존재하지 않는다.** 이 사실이 §3의 핵심이다.

---

## 3. 핵심 질문 — 공통 기능의 action은 어디에 정의하는가

### 3.1 먼저, 당신의 직관이 맞다 (두 가지 모두)

1. **"모든 screen model에 다 넣으면 안 될 것 같다"** → 맞다. ADR-001 전체가 "복사 핸드오프는 드리프트·이중관리를 낳는다"는 문제의식에서 출발한다. 공통 action을 화면마다 복제하면 정확히 그 문제가 재발한다.
2. **"그래서 이런 구조인가"** → 부분적으로 맞다. DP를 "행위 없는 빈 골격"으로 둔 것은 공통 동작을 화면/템플릿에 분산시키지 않으려는 의도와 일치한다. 다만 **공통 action이 DP에 사는 것은 아니다.**

### 3.2 현재 설계의 실제 답: `SPEC-000` (공통 기능 baseline)

공통 동작은 screen model 레이어 **밖**, ①이 작성하는 `SPEC-000`(`foundation/platform-baseline/SPEC-000.md`)에 정의된다. 이 문서의 헤더가 명시한다: "**로그인·SSO·RBAC·앱 셸·감사 로그 등 공통 기능 요건**을 정의한다."

당신이 떠올렸을 법한 공통 동작들이 여기에 매핑된다:

| 공통 동작 (예) | SPEC-000 항목 | 전달 모드 |
|---|---|---|
| 공통 레이아웃(헤더·내비·콘텐츠 슬롯) | §3 FEAT-SHELL-1 | A(가이드 코드) |
| 내비게이션·브레드크럼, 현재 위치 표시 | §3 FEAT-SHELL-2 | A |
| 사용자 메뉴(프로필·**로그아웃**) | §3 FEAT-SHELL-3 | A |
| mutate 동작의 감사 로그 삽입 | §4 FEAT-AUDIT-1 | A |
| 전역 에러/빈/로딩 상태 UI | §4 FEAT-ERR-1 | A |
| 미인증 라우팅 가드 | §1 FEAT-AUTH-4 | A |
| 화면 레벨 조건부 렌더(권한) | §2 FEAT-RBAC-3 | A |

즉 셸 컴포넌트(Header/NavMenu/Breadcrumb/Avatar)의 **행위**는 `SPEC-000`에 한 번 명세하고 ③ Phase 0가 모드 A/B로 구현한다. SPEC-000 §3 헤더가 "②의 design-page(DP-*)·DS 허용집합과 정합해야 한다"고 못 박아, DP의 잠긴 셸과 짝을 이루도록 의도돼 있다.

### 3.3 책임 분담 (의도된 3분할)

```
① DP (foundation/design-pages/DP-*.yaml)
     = 공통 크롬의 "시각적 잠금 구조"        (행위 없음)

① SPEC-000 (foundation/platform-baseline/)
     = 공통 기능의 "행위·요구사항·수용기준"  (셸/인증/RBAC/감사/전역상태)
       → ③ Phase 0가 mode A(가이드)·B(코드)로 구현

② SCR.actions (model_repo/screens/SCR-*.yaml)
     = 편집 캔버스(도메인) 컴포넌트의 행위만   (REQ-… 채번·Gherkin·provenance)
```

### 3.4 이 분할이 기계적으로 강제되는 증거

스키마가 "공통 action을 화면에 넣지 마라"를 단순 권고가 아니라 **두 겹의 검사로 강제**한다 — locked 컴포넌트에는 action을 붙일 길이 아예 없다:

- **`on-save-schema-validate.py`** `validate_actions()`: `action.component`가 `SCR.layout`의 id 집합에 없으면 **저장 차단 error** — "layout에 존재하지 않는 CMP 참조".
- **`on-save-lint-L1-L4.py`** `lint_L4_coverage()` L4-1: 동일하게 `component`가 layout에 없으면 error("실존하지 않는 CMP 참조").
- **L5 canvas-bounds** L5-3: `editable:false`(locked) 슬롯에 컴포넌트를 **추가**하면 error("locked 슬롯에 컴포넌트 추가 불가").
- `layout-recommend` 스킬: locked 슬롯은 "DP 컴포넌트로 그려 맥락 제공"이고 `meta.interactive`는 "**시각 구분만 (실제 동작 구현 아님)**".

종합하면: locked 셸 컴포넌트는 `SCR.layout`에 CMP-id가 없으므로(§2) → 거기에 action을 붙이려 해도 schema-validate와 L4가 동시에 막는다. **이는 버그가 아니라 의도다.** 공통 동작을 화면 모델로 끌어들이지 못하게 하는 봉쇄장치다.

---

## 4. 현재 설계가 잘하는 점 (균형)

개선점만 보면 오해하기 쉬워 먼저 정리한다. 이 구조는 다음을 제대로 달성한다:

- **무손실 복사 + 결정성 양립**: 변종/부분집합 선택 덕에 복사가 자연스럽고, `layout_hash`가 editable 복사분만 해시해 결정론 계약이 깨지지 않는다.
- **드리프트 0**: locked = 참조 상속이라 공통 크롬의 단일 출처가 유지된다(ADR-001 D3와 정합).
- **관심사 분리가 운영자 분리와 일치**: ①(개발리드: DP·SPEC-000) / ②(기획자: 도메인 화면). 도구·역할 경계와 깔끔히 맞는다.
- **하위호환 보존**: 레거시 평면 `slots`, `position:{slot,order}`를 전부 계속 파싱·렌더·통과시킨다.

---

## 5. 발견된 간극(Gap)

핵심 메커니즘은 일관적이지만, "공통 action"을 끝까지 추적하면 다음 공백이 드러난다.

### G1. locked 컴포넌트 ↔ SPEC-000 연결이 산문일 뿐, 스파인으로 추적 불가
DP의 `locks: [Header]`와 SPEC-000의 FEAT-SHELL-*는 **자연어로만** 연결돼 있다("DP-MAIN 슬롯 구조와 일치"). 스파인 추적 그래프(`DP → SCR → CMP → REQ → … `)에 셸 동작이 없다 — SPEC-000은 `SPEC-` 계열로 **REQ- 채번이 면제**되고 그래프에서 분리돼 있다(spine-ids.md). 그래서 "헤더 로그아웃은 무슨 동작이고 그 수용기준·테스트는 어디 있나?"를 스파인으로 답할 수 없다.

### G2. "준공통(semi-common)" action의 집이 없다
SPEC-000은 **전역** 동작을, SCR은 **화면 고유** 동작을 담는다. 그 사이, *일부 화면군에만 공통*인 동작은 갈 곳이 없다. 예: "모든 LIST 화면의 엑셀 내보내기 버튼은 동일하게 동작한다", 특정 archetype 공통 툴바 동작 등. 현재는 이런 동작을 **화면마다 손으로 다시 작성**해야 한다 — 정확히 당신이 우려한 중복이, 준공통 계층에서 실제로 발생한다. (editable 슬롯은 시딩으로 복사되지만, action에는 시딩/템플릿 메커니즘이 없다.)

### G3. locked 컴포넌트의 동작이 모델 레이어에 표현되지 않는다
`DP-POPUP.yaml`의 **닫기 버튼(Button)**은 `dialog-header`(locked) 안에 있다. 시각적으로는 렌더되지만 그 "닫기" 동작은 DP에도(이벤트 금지), SCR에도(layout에 없음) 없다. 제네릭 닫기는 DS 컴포넌트/앱 셸이 알아서 처리한다는 암묵 가정인데, **수용기준·provenance가 필요한 locked 컴포넌트**(예: "로그아웃은 확인 후 실행")는 모델 상 표현 수단이 전혀 없다.

### G4. `reactive`(컴포넌트 간 연동)가 locked 경계를 못 넘는다
편집 캔버스 안의 filterbar→table 재조회는 표현 가능하다(둘 다 editable). 그러나 **헤더의 전역 검색(locked)**이 캔버스 컴포넌트를 구동해야 한다면, locked 컴포넌트에 CMP-id가 없어 `requery_on: [<locked>]`를 쓸 수 없다.

### G5. 스키마 §7이 "그럼 동작은 어디에 두나"를 말하지 않는다 (문서 간극)
§7과 design-page-builder는 "데이터·이벤트 금지"만 반복하고, **공통 동작이 SPEC-000으로 간다는 사실을 한 줄도 안 적었다.** 당신이 이 질문에 도달한 것 자체가 문서 간극의 증거다. SPEC-000을 읽기 전에는 "행위가 증발한다"처럼 보인다.

---

## 6. 개선 권고 (우선순위 순)

낮은 비용·높은 효과부터 배치했다. A·B는 거의 문서/규칙 수준, C~E는 스키마·훅 확장이다.

### A. (즉시·저비용) 스키마 §7에 "공통 동작은 SPEC-000" 한 단락 추가 — G5 해소
§7 "DP가 갖지 않는 것" 바로 아래에, *locked 셸 컴포넌트의 행위는 `SPEC-000`(§3 앱 셸·§4 감사/전역상태)에 정의되고 ③ Phase 0가 구현한다*는 포인터를 명시한다. 이 리포트가 답한 내용을 스키마 자체에 박아 재질문을 차단한다.

### B. (저비용) DP slot/locks에 `spec_ref` 핀 도입 — G1 해소
DP의 locked 슬롯에 선택 필드 `spec_ref: [SPEC-000/FEAT-SHELL-2]`를 허용하고, `design-page-lint.py`가 *모든 `locks:` 셸 컴포넌트가 SPEC-000 FEAT로 해소되는지*(혹은 "DS 내부 동작 — 명세 불요"로 명시 표시됐는지) 검사한다. DP↔SPEC-000 정합이 기계 강제되고, 스파인 추적에 셸 동작이 들어온다.

### C. (중간) "준공통 action 템플릿" 계층 추가 — G2 해소 (가장 실질적 효과)
editable `layout` 시딩과 대칭으로, **action 시딩**을 도입한다. 두 가지 형태 중 택1:
- DP/archetype 수준의 `action_templates`를 두고 `instantiate_screen.py`가 SCR.actions로 복사 시딩(각 시드에 `provenance.seeded_from`을 남겨 출처 추적).
- 또는 공유 action 라이브러리(`PACK-`/`SPEC-` 수준)를 SCR이 **참조**(복사 아님)하도록 허용.
전자는 "편집 가능한 시작점"(레이아웃 시딩 철학과 동일), 후자는 "단일 출처 유지"(locked 철학과 동일). 트레이드오프를 ADR로 결정할 사안.

### D. (중간) locked 컴포넌트에 read-only 동작 참조 허용 — G3·G4 해소
SCR에 *편집 불가·재명세 아님*인 얇은 "셸 동작 참조"를 허용한다 — 예: `shell_actions: [{ ref: DPC-POPUP.close-btn, spec: SPEC-000/FEAT-SHELL-3 }]`. 이는 새 동작을 정의하는 게 아니라 SPEC-000 FEAT를 가리키는 포인터라 결정성·DS 폐쇄를 깨지 않으면서, (a) locked 컴포넌트의 동작을 스파인에 노출하고 (b) `reactive`가 이 ref를 트리거 소스로 쓸 길을 연다.

### E. (검증) DP↔SPEC-000 교차 정합을 CI 가드로
B의 `spec_ref` 검사를 ① 준비단계 lint 또는 Gate에 묶어, 잠긴 셸이 추가됐는데 대응 FEAT가 없거나(미명세), FEAT가 사라졌는데 DP가 여전히 잠그고 있는(고아) 경우를 빌드 단계에서 잡는다.

---

## 7. 결론

- DP를 변종으로 만든 것은 **"복사해서 시작"을 무손실로 만들기 위한 의도적 설계**이며, 그 부분집합 선택(행위 제거)은 재사용성과 결정성을 동시에 지킨다.
- 공통 action을 모든 화면에 넣으면 안 된다는 당신의 직관은 정확하고, 아키텍처도 그것을 **기계적으로 금지**한다. 공통 동작의 실제 집은 **`SPEC-000`**(셸·인증·감사·전역상태)이고, ②의 SCR.actions는 도메인 동작만 담는다.
- 다만 (1) DP↔SPEC-000 연결이 산문뿐이고, (2) "준공통" action의 집이 없으며, (3) locked 컴포넌트 동작이 모델·스파인에 노출되지 않는 **실질적 간극**이 있다. 가장 효과 큰 개선은 **§6-C(준공통 action 시딩/참조 계층)**와 **§6-B(spec_ref로 DP↔SPEC-000 기계 정합)**이며, 둘 다 ADR로 트레이드오프를 결정한 뒤 스키마·훅을 확장하는 사안이다.

---

## 부록 — 근거 파일

- `packages/harness-core/rules/screen-model-schema-v2.md` — §7 DP 변종, 필드 규칙표, `actions[].component` 계약
- `docs/ADR-001-3runtime-architecture.md` — D3 복사 대신 참조, 드리프트 문제의식, 교차 계약 단일출처
- `docs/ADR-002-deterministic-screen-render.md` — §1 P5 갭, §6 인스턴스화(locked 참조/editable 복사), §6.3 "복사의 정확한 의미"
- `packages/harness-core/render/instantiate_screen.py` — `seed_layout()`(locked 건너뜀 / editable 시딩), `build_scr()`
- `packages/plugin-po-define/hooks/on-save-schema-validate.py` — `validate_actions()` `action.component ∈ SCR.layout` 강제
- `packages/plugin-po-define/hooks/on-save-lint-L1-L4.py` — L4-1(component 참조), L5-3(locked 슬롯 추가 금지)
- `packages/plugin-po-define/skills/layout-recommend/SKILL.md` — 인스턴스화 0단계, locked=맥락 렌더·interactive=시각 구분만
- `packages/plugin-prerequisite/skills/design-page-builder/SKILL.md` — DP=빈 골격(데이터·이벤트 금지), 스키마 통일 근거
- `projects/example/foundation/platform-baseline/SPEC-000.md` — §3 앱 셸·§4 감사/전역상태(공통 action의 실제 정의처)
- `packages/harness-core/rules/spine-ids.md` — 추적 그래프, SPEC- 계열 REQ- 면제(셸 동작이 스파인 밖)
- `projects/devlog/foundation/design-pages/DP-POPUP.yaml` — locked 닫기 버튼 사례(G3)
