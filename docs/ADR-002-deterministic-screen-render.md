# ADR-002 — Screen Model의 결정론적·반응형 렌더링, DS 카탈로그, Design Page 인스턴스화

- 상태: **채택** (2026-06-21, rev.5) — 전 결정(D1~D7·§6) 구현 완료. **골든 PNG는 결정 4에 따라 의도적 미도입**, **챗봇 카탈로그 패널은 ② 챗봇 앱 빌드(ADR-001 후속)에 의존**해 보류.
- 관련: `docs/ADR-001-3runtime-architecture.md`, `packages/harness-core/rules/screen-model-schema-v2.md`(R1 이후 단일 출처), `packages/plugin-po-define/rules/state-machine.md`, `packages/plugin-po-define/skills/layout-recommend/SKILL.md`, `packages/plugin-prerequisite/skills/design-page-builder/SKILL.md`, `packages/harness-core/rules/spine-ids.md`, `packages/plugin-po-define/skills/spec-generator/spec-pack-schema.md`
- 한 줄 요약: screen model(YAML)을 **순수 Python 엔진**으로 HTML 렌더해 위치를 결정론적으로 확정하되 **여러 창 크기에서 동작하는 반응형**을 유지한다. ① design page·DS 자산을 같은 엔진으로 렌더해 **DS 카탈로그(대시보드)** 를 만들고, ② PO는 이를 보며 AI에게 디자인을 지시한다. PO가 design page를 고르면 그 **screen model을 인스턴스화(복사)** 해 새 화면(이름·SCR- ID)을 시작하며, DP의 고정 구성은 잠기고 **빈 캔버스 안에서만, 경계를 넘지 않게** 작업한다.

> rev.5 변경: 남은 결정 전부 구현 — D4 DS 카탈로그(`render_catalog.py`, DS-불가지론 토큰 추출), D5 해시 핀 배선(② spec-generator 계산·기록 + ③ Phase α 해시 가드), D6 렌더 환경 동결(token-only 치수·행/텍스트 최소 높이·시스템 폰트 스택), §9 미결정(컴포넌트 상태 필드 형식) 확정. 상세 §11.
> rev.4 변경(채택): 키스톤 구현 완료(§10 구현 메모 참조). `from_template` 강제 수준을 §6.4에서 **권장(warn)** 으로 조정(레거시 화면 하위호환; 인스턴스화 산출엔 항상 포함). D4 카탈로그·골든PNG는 후속으로 명시 분리.
> rev.3 변경: (A) 미해결 항목을 **결정된 기본값**으로 확정(§7), (B) **Design Page 인스턴스화(DP→SCR 복사) 시나리오**를 정식화하고 현재 구조의 갭을 메움(§6), (C) 캔버스 봉쇄를 "세로 스크롤 허용" 모델로 정리(D3), (D) 이해 어려웠던 용어(골든 PNG·sugar)를 쉬운 말로 풀어 결정에 포함(§7).
> rev.2: ① DP 렌더·DS 카탈로그 추가, 반응형 그리드+절대값 금지, 캔버스 봉쇄.

---

## 1. 맥락 — 풀어야 할 5가지

`README.md` 하드룰 #1: *screen model(YAML)이 단일 진실원, HTML 렌더·코드는 파생*.

- **P1 비결정성** — 위치가 `slot/order/area/span` 의미 좌표라 픽셀을 브라우저가 런타임 계산. 렌더를 LLM이 생성해 재현 불가.
- **P2 ① 자산 비가시성** — component·token·색상·상태(반응)를 PO가 볼 대시보드가 없음 → "백지 캔버스" 문제.
- **P3 반응형 ↔ 결정론 충돌** — 여러 창 크기 지원과 "위치 확정"을 어떻게 양립?
- **P4 캔버스 봉쇄 부재** — DP 고정 구성을 침범/초과하지 않게 강제할 규칙 없음.
- **P5 Design Page 인스턴스화 부재** — *현 구조는 DP를 복사·상속하지 않는다.* 실제 `SCR-TODO-LIST.yaml`은 `template.page: DP-MAIN`만 이름 참조하고, DP-MAIN의 고정 구성(Header·Breadcrumb·Footer)은 **상속되지 않고 사라진다**. PO가 "DP를 골라 그 구성을 고정한 채 빈 캔버스에서 시작"하는 시나리오가 빠져 있다.

---

## 2. 결정 (제안)

### D1. 단일 렌더 엔진(순수 Python) — screen·design page·카탈로그 모두 렌더

LLM은 **YAML만 쓴다.** HTML은 항상 결정론적 스크립트가 생성한다.

```
packages/harness-core/render/
  engine.py            # 토큰→CSS, 컴포넌트→HTML, 그리드 배치 (공용 코어)
  render_screen.py     # SCR-*.yaml → renders/SCR-*.render.html        (②③)
  render_designpage.py # DP-*.yaml  → design-pages/renders/DP-*.html    (①)
  render_catalog.py    # tokens+ds-allowlist+component meta → catalog/  (①)
  instantiate_screen.py# DP-* + 이름 → 새 SCR-*.yaml (초기 골격)         (②)  ← 신규(P5)
```

계약: **같은 입력 → 바이트 동일 HTML**(키 정렬·고정 들여쓰기·timestamp는 해시 제외·인라인 스타일 금지·외부 CDN/폰트 금지·token 컴파일 CSS 인라인). 결정성 CI 가드 `render×2 → diff 0`. `harness-core`에 둬 ①②③이 동일 엔진 공유(ADR-001 단일 출처).

### D2. 위치 모델: 절대 픽셀 금지, 반응형 그리드 + 정수 좌표 (P1·P3)

**원칙: 위치는 (그리드 정의, 브레이크포인트, 정수 좌표)의 결정론적 함수다. 절대 픽셀이 아니다.** (근거·이유는 §4)

DP가 반응형 그리드를 선언, 컴포넌트는 정수 좌표(+브레이크포인트 오버라이드)로 배치:

```yaml
# SCR-*.yaml — position
position:
  slot: content
  base: { col_start: 1, col_span: 6, row: 2, row_span: 1 }   # lg 기준
  at:
    md: { col_start: 1, col_span: 8, row: 2 }
    sm: { col_start: 1, col_span: 4, row: 3 }
```

- `col_span: full|half|third|quarter`는 **shorthand** — 렌더러가 컬럼 수에 맞춰 정수로 resolve, **저장·핀 값은 항상 정수**(§7 결정 5).
- 픽셀 좌표·`auto` 흐름 **금지**(lint 차단). 모든 컴포넌트는 명시 `row`.
- 오버라이드 미지정 시 **결정론적 자동 강등**(§7 결정 2) 적용.

### D3. 캔버스 봉쇄 — 고정 영역 vs 편집 캔버스 + 경계 강제 (P4·P5)

DP는 두 종류 슬롯을 가진다.

```yaml
# DP-MAIN.yaml — slots
canvas:
  grid: { columns: 12, gap: space-4, max_width: 1440 }
  breakpoints: [ {name: lg,min:1280,columns:12}, {name: md,min:768,columns:8}, {name: sm,min:0,columns:4} ]
slots:
  - { id: header,  editable: false, locks: [Header, Breadcrumb] }   # 고정 구성
  - { id: header-actions, editable: false, locks: [Button] }
  - { id: content, editable: true,  grid_columns: 12, overflow: scroll-y }  # 빈 캔버스
  - { id: footer,  editable: false, locks: [Separator] }
```

- **locked region**(`editable:false`): ①이 컴포넌트·토큰까지 확정. screen model은 **참조(읽기전용)만**, 편집 불가. 렌더 시 실제 컴포넌트로 그려져 맥락 제공.
- **editable canvas**(`editable:true`): PO/AI 작업 영역. 자체 `grid_columns` + `overflow` 정책.
- **신규 lint L5 — canvas-bounds**:
  - 가로: `col_start + col_span - 1 ≤ slot.grid_columns` (초과 → error, 강제 봉쇄).
  - 세로: 행은 위에서 아래로 누적, 캔버스 할당 영역을 넘으면 **캔버스 내부 세로 스크롤**(`overflow: scroll-y` 기본). 즉 *세로는 막지 않고 스크롤*, locked 영역을 밀어내거나 겹치지 않음(§7 결정 6).
  - `editable:false` 슬롯에 컴포넌트 추가/수정 → error.
  - ds-closure(컴포넌트 발명 금지)의 공간판 = **canvas-closure**.

### D4. DS 카탈로그(대시보드) — PO의 디자인 지시 근거 (P2)

`render_catalog.py`가 ① 자산으로 시각 카탈로그를 결정론적 생성 → `foundation/design-system/catalog/index.html`.

- **컴포넌트 갤러리**: 각 컴포넌트 variant + **표준 상태 세트**(§7 결정 3) 시각 렌더 + 참조 ID 표기(= screen model `source.ref`).
- **색상 토큰**: 스와치 + 토큰명 + hex + 용도.
- **타이포/스페이싱**: 토큰명·px·견본.
- **사용 가이드**: 의도·금지 사례(ds-allowlist 연동).

카탈로그의 이름 = screen model이 참조하는 ref·token과 **동일** → PO가 이름으로 지목("`Card`를 상단, 강조 `color-primary-600`") → AI가 곧장 model 매핑. ②에서 챗봇 **읽기전용 패널**로 상시 노출.

### D5. 다중 창 크기 렌더 + 해시 핀(freeze) (P1·P3)

- 브레이크포인트별 미리보기 프레임(`SCR-*.lg/md/sm.html` 또는 단일 HTML+반응형 CSS) → PO가 모든 창 크기 확인.
- `pinned_contract` 확장:

```yaml
pinned_contract:
  version: 12
  hash: "sha256:..."          # 모델 전체
  layout_hash: "sha256:..."   # 전 브레이크포인트 resolve 좌표 집합 (위치 계약 정규형)
  render_hash: "sha256:..."   # 렌더 HTML(타임스탬프 제외)
  from_template: "DP-MAIN@v2" # 인스턴스화 출처 (신규, P5)
```

- `layout_hash`는 모든 브레이크포인트 정수 좌표 + 그리드 정의로 계산 → 반응형이어도 위치 계약은 하나의 정규형으로 동결.
- ③ Phase α는 동일 엔진 재렌더로 `layout_hash` 재현, 불일치 → 빌드 실패. "②확정 위치 ③변경 금지"의 기계적 강제. 변경은 ② Gate A 재확정 → re-pin.

### D6. 렌더 환경 동결

token-only 치수(magic number 금지), 웹폰트 repo 번들 + `@font-face` 임베드, 텍스트 영역 명시 높이로 줄바꿈 변동 격리.

### D7. 워크플로우 연결

- **①**: `render_designpage.py`로 DP 렌더(locked=실제 컴포넌트, editable=그리드 오버레이+슬롯명+경계 점선). `render_catalog.py`로 DS 카탈로그.
- **②**: PO가 DP 선택 → **인스턴스화**(§6) → DP 렌더를 바탕으로 깔고 editable 캔버스에만 작업. 저장 시 `on-save-schema-validate → lint L1~L5` 통과 후 `render_screen.py` 자동 실행. `--watch`로 모든 브레이크포인트 실시간 갱신. DS 카탈로그 패널 상시.

---

## 3. (불변) 결정론의 범위

| 수준 | 결정론 | 방법 |
|---|---|---|
| DOM 구조·순서 | 완전 | slot + 정수 좌표 정렬 |
| 컬럼 배치·상대 위치(구간 내) | 완전 | 반응형 그리드 + 정수 좌표(콘텐츠 비의존) |
| 브레이크포인트 전환 배치 | 완전 | 명시 오버라이드 또는 자동 강등 규칙 |
| 캔버스 경계 준수 | 완전(강제) | lint L5 canvas-bounds |
| 절대 px 폭/높이 | 구간 내 가변(의도) | fluid 그리드 — 비율 고정, px는 창 폭 함수 |
| 텍스트 줄바꿈 높이 | 조건부 | 폰트 동결 + 명시 높이/scroll 격리 |
| OS별 서브픽셀 폰트 | 불가(원천) | §7 결정 4 참조 |

핵심: **레이아웃 계약(구조+상대 좌표+브레이크포인트 배치+캔버스 경계)** 은 100% 동결 가능. 절대 px는 의도적으로 창 폭의 함수(반응형).

---

## 4. "위치 절대값을 넣어도 되나?" — 답: 아니오

절대 픽셀(예 `x:320px`)은 단일 창에서만 맞고 다른 해상도·모바일·확대에서 깨지며 캔버스 봉쇄와도 충돌한다. smart하게 확정하는 4장치: ① 상대 단위(분수 컬럼: `1–6 of 12`=왼쪽 절반) ② 소수 고정 브레이크포인트(구간 내 fluid, 경계에서만 좌표 변경) ③ 결정론적 자동 강등 ④ 절대값은 DP 토큰(gap·max-width·경계 px)만 ①이 1회 고정. **결정론 = "픽셀 고정"이 아니라 "관계(좌표)를 순수 함수로 고정".** 그래서 반응형·결정론 양립.

---

## 5. (참고) 기존 자산 영향 목록

`harness-core/render/*` 신설 · `screen-model-schema-v2.md`(position 반응형화·픽셀 금지·`from_template`) · `design-page-builder` + DP 스키마(canvas·breakpoints·slots locked/editable) · DS 카탈로그 자산(component states·token 설명) · `layout-recommend`(렌더 위임·인스턴스화 흐름) · `on-save-lint`(L5 추가·render·watch) · `spec-pack-schema.md`(layout/render_hash·from_template) · ③ Phase α(해시 가드) · 챗봇 UI(카탈로그 패널·DP 바탕·프레임).

---

## 6. Design Page 인스턴스화 (DP → SCR 복사 시나리오) — 신규 정식화 (P5)

### 6.1 현재 구조 갭 분석 (실측)

| 시나리오 요구 | 현재 상태(실측) | 갭 |
|---|---|---|
| DP가 **고정 기본 구성**(header/nav/footer 등)을 담는다 | `DP-MAIN.yaml`에 `components` 있으나 locked/editable 구분 없음 | ❌ 고정/편집 미구분 |
| DP에 **캔버스(빈 영역)·그리드·경계** 정의 | `slots`는 평면 이름 목록만 | ❌ canvas/grid/breakpoints 없음 |
| PO가 DP 고르면 **screen model 복사**로 시작 | `layout-recommend`가 `template.page` 이름만 참조, 화면을 새로 작성 | ❌ 인스턴스화(복사) 동작 없음 |
| 고정 부분이 SCR로 **이어지고 잠김** | `SCR-TODO-LIST`에 Header·Breadcrumb·Footer **누락(드롭)** | ❌ locked region 미상속 |
| 새 화면 **이름 + SCR- 채번** | `screen.name`/`id` 필드는 존재 | △ 인스턴스화 플로우와 미연결 |
| **DP 원본 불변 + 버전 핀** | `template.version` 선택적(todo SCR엔 누락) | ❌ DP 핀 미강제 |
| **DP→SCR 추적**(provenance) | 스파인 그래프가 SCR부터 시작 | ❌ DP- 출처 엣지 없음 |

결론: 현재는 "DP 복사·상속"이 아니라 "DP 이름 참조 + 화면 새로 작성"이다. 요청 시나리오를 만족하려면 **인스턴스화**를 정식 단계로 추가해야 한다.

### 6.2 인스턴스화 동작 (제안)

`instantiate_screen.py`(또는 `layout-recommend`의 init 단계)가 수행:

1. PO가 카탈로그/DP 미리보기에서 **design page 선택**.
2. PO가 **화면 이름·도메인·타입** 입력 → `harness-core/lib/spine_ledger.py`가 **SCR- ID 채번**(전역 유일).
3. 새 `SCR-*.yaml` 생성(`status: draft`)에:
   - `screen.from_template: { page: DP-MAIN, version: N }` **핀(불변)**.
   - DP의 **locked region을 참조로 상속** — SCR에 복제하지 않고 렌더 시 DP에서 읽어 그림, `editable:false` 표시로 편집 차단. **DP 파일은 절대 수정되지 않는다**(요청: "design page screen model 실제로 수정 안 함").
   - **editable 캔버스를 빈 상태로** 시작, 컬럼·경계·브레이크포인트는 DP에서 상속.
4. 이후 PO 작업은 캔버스 안에서만(D2 좌표 + D3 L5 봉쇄). 상태 머신은 기존대로 `draft → … → confirmed`.
5. `model_repo/link-manifest.yaml`에 **DP- → SCR- 엣지** 기록(추적).

### 6.3 "복사"의 정확한 의미 — 참조 상속 + 캔버스 소유

요청은 "DP를 복사해와 시작(원본 불변)"이다. 두 부분을 다르게 다룬다:

- **고정 구성(locked)**: 물리 복제가 아니라 **참조 상속**. 단일 출처(DP)를 유지해 드리프트 0, DP 수정 시 re-pin으로 전파(ADR-001 "복사 대신 참조"와 정합). SCR은 이를 못 고친다.
- **빈 캔버스(editable)**: SCR이 **온전히 소유**. 여기서부터가 새 화면의 고유 작업물.
- 어느 쪽이든 **DP 원본 YAML은 불변** → 요청 충족. (PO가 "복사된 내 화면"으로 체감하는 것은 렌더 결과: 고정부 + 내 캔버스가 한 화면으로 보임.)

### 6.4 스파인 ID·상태 영향

- `spine-ids.md`에 **DP- → SCR- 인스턴스화 엣지** 명문화(추적 그래프 앞에 `DP → SCR` 추가).
- `state-machine.md`에 인스턴스화 진입을 명시: 인스턴스화 산출 = `draft` SCR(고정부 상속 + 빈 캔버스). 첫 저장부터 기존 save 파이프라인(schema→lint L1~L5→render).
- `from_template` 핀: **인스턴스화 산출(`instantiate_screen.py`)엔 항상 포함**. schema-validate는 **권장(warn)** 수준으로 검증한다 — 레거시 화면(예: 기존 todo SCR, 인스턴스화 이전 생성)을 깨지 않기 위해 **필수(error)로 올리지 않는다**(rev.4 조정). 신규 화면은 인스턴스화를 거치므로 자연히 채워진다.

---

## 7. 결정된 기본값 (이전 rev의 미해결 항목 확정)

**결정 1 — 브레이크포인트·기본 행·overflow.**
3개로 고정: `lg ≥1280px(12컬럼)`, `md 768–1279px(8컬럼)`, `sm <768px(4컬럼)`. gap = `space-4`(token), content max-width 1440px. editable 캔버스의 행 높이는 **auto(min = `space` 토큰 기반)**, 세로는 **캔버스 내부 스크롤 기본**(`overflow: scroll-y`). 가로는 컬럼 수로 하드 봉쇄. (근거: 단순·업계 통용·구간 내 fluid로 충분.)

**결정 2 — 자동 강등 규칙(충돌 없고 PO가 예측 가능).**
좁은 브레이크포인트에서 오버라이드가 없으면: 컴포넌트를 `(base.row 오름차순, 그다음 base.col_start 오름차순)`로 정렬 → 각자 **전체 폭(full)** 으로 펼쳐 그 순서대로 **세로 스택**. 겹침 0, 숨김 없음(숨기려면 PO가 `at: { hidden: true }` 명시). 한 줄 규칙이라 PO가 결과를 머릿속에 그릴 수 있고 결정론적.

**결정 3 — DS 카탈로그 표준 상태(반응) 세트.**
컴포넌트마다 해당되는 것만 렌더: `default · hover · focus · active · disabled · loading · error(invalid) · selected · read-only · empty(컨테이너류)`. 목적은 PO가 "이 버튼은 비활성일 때 이렇게 보이는구나"를 **시각적으로 이해하고 AI에게 지시**하는 것. 컴포넌트가 지원하지 않는 상태는 생략.

**결정 4 — 골든 PNG: 도입 보류(지금은 layout_hash로 충분).**
용어 풀이: "골든 PNG"란 *확정된 화면을 한 번 스크린샷으로 찍어 '정답 그림'으로 저장*해 두고, 이후 렌더가 그 그림과 픽셀이 다르면 경고하는 회귀 검사다. "headless Chromium 버전 핀"은 *그 스크린샷을 찍는 브라우저 버전을 고정*해 브라우저 업데이트만으로 그림이 달라지지 않게 하는 것, "허용오차 임계값"은 *몇 % 픽셀 차이까지 같다고 볼지*의 기준이다. → **결정: 지금은 도입하지 않는다.** 위치 계약은 이미 `layout_hash`(좌표 해시)로 100% 결정론적으로 잡히고, 골든 PNG는 OS·폰트 렌더 차이 때문에 운영이 까다롭다. 픽셀 회귀까지 필요해지면 그때 ③ 스택의 Playwright로 *CI 단일 환경에서만* 옵션 도입.

**결정 5 — `col_span` shorthand: 유지하되 항상 정수로 확정.**
용어 풀이: "sugar(shorthand)"란 사람이 쓰기 편한 *축약 표기*다. `col_span: half`는 사람이 쓰는 축약이고, 렌더러가 이를 그리드에 맞춰 정확한 정수(12컬럼이면 6)로 **변환(resolve)** 한다. "정수 좌표 완전 전환"은 축약을 없애고 항상 숫자만 쓰게 하자는 뜻. → **결정: 축약(full/half/third/quarter)은 PO 편의를 위해 유지**하되, 저장·핀되는 계약값은 **언제나 resolve된 정수**. 사람은 쉽게 쓰고, 계약은 엄격하게 — 둘 다 취함.

**결정 6 — 캔버스 세로 초과: 분할 강제 아님, 내부 스크롤 허용.**
캔버스는 *DP가 정한 고정 구성을 제외한 나머지 빈 영역*이다. 그 안에 테이블이 올지 텍스트가 올지, 행이 얼마나 늘지는 **PO 프롬프트로 결정**된다. 따라서 세로로 늘어나면 **캔버스 영역 내부에서 스크롤**(고정 구성은 그대로, 캔버스만 스크롤). 가로(컬럼)만 하드 봉쇄. 별도 화면 분할을 강제하지 않는다(PO가 원하면 새 SCR로 분리).

---

## 8. 결과 / 트레이드오프

**얻는 것**: YAML→HTML 순수 함수(재현성), 반응형 유지하며 `layout_hash`로 위치 동결(③ 변경 즉시 검출), DS 카탈로그로 PO가 이름 기반 지시("백지 캔버스" 제거), 캔버스 봉쇄로 DP 골격 보존, DP→SCR 인스턴스화로 고정 구성 상속·DP 불변·추적 확보, ①②③ 단일 엔진 픽셀 일치.

**치르는 것**: 자유 흐름 대신 명시 그리드 좌표(축약·자동 강등으로 완화), 카탈로그·DP 렌더·토큰 컴파일 파이프라인 유지 비용, 컴포넌트 상태 메타를 ① 자산으로 정식 관리, 인스턴스화/L5/`from_template` 강제 등 스키마·훅 변경 필요.

---

## 9. 잔여 후속(설계 아닌 구현 시 확정)

- ✅ **해소** `space` 토큰 기반 캔버스 행 최소 높이 → `space-8`(48px)로 `grid-auto-rows: minmax(48px,auto)` 고정(D6). content max-width(1440)은 DP `canvas.grid.max_width`로 프로젝트별 조정 가능.
- ⏸ **보류(챗봇 의존)** locked region 참조 상속 시 DP 버전 업데이트의 re-pin 트리거 UX(② 알림) — ② 챗봇 앱 빌드(ADR-001 후속) 후 구현.
- ✅ **해소** 카탈로그 컴포넌트별 지원 상태 매핑 → `ds-allowlist.md`의 선택 `- **states**: ...` 필드(없으면 종류 기반 기본 상태셋 추정). §11 참조.

---

## 10. 구현 메모 (rev.4, 2026-06-21 — 키스톤 채택)

**구현 범위**: D1(엔진)·D2(반응형 위치)·D3(캔버스 봉쇄+L5)·D5(해시 핀)·§6(인스턴스화). **D4 DS 카탈로그·골든PNG(결정 4)는 후속**(미구현).

**신설/변경 자산**:
- 렌더 엔진 — `packages/harness-core/render/`: `engine.py`(공용 코어: canvas 정규화·position resolve·토큰→CSS·컴포넌트→HTML·layout_hash/render_hash), `render_screen.py`(SCR→render.html, `--check` 결정성 검사), `render_designpage.py`(DP→미리보기), `instantiate_screen.py`(DP→SCR 인스턴스화), `__init__.py`.
- 채번 — `harness-core/lib/spine_ledger.py`에 `mint_scr_id(root, domain, type)` 추가(`SCR-{DOMAIN}-{TYPE}` 전역 유일 채번).
- 스키마·룰 — `screen-model-schema-v2.md`(position 반응형·`from_template`), `harness-core/rules/spine-ids.md`(DP→SCR 엣지), `state-machine.md`(인스턴스화 진입·L1~L5·엔진 렌더), `spec-pack-schema.md`(`pinned_contract`에 layout_hash·render_hash·from_template).
- 훅·린터 — `on-save-schema-validate.py`(반응형 position·px/auto 금지·from_template), `on-save-lint-L1-L4.py`(**L5 canvas-bounds** 추가: 가로 봉쇄·locked 슬롯 보호), `design-page-lint.py`(canvas 모델 검증).
- 스킬 — `layout-recommend/SKILL.md`(인스턴스화 0단계·엔진 위임 렌더), `design-page-builder/SKILL.md`(캔버스 모델 산출·DP 렌더).
- 데이터(example만) — `DP-MAIN`·`DP-POPUP`을 캔버스 모델로 업그레이드, `SCR-PRODUCT-LIST`를 인스턴스화로 생성(반응형 레이아웃 시연), 렌더 산출·link-manifest DP→SCR 엣지.

**하위호환(불변 원칙)**: 레거시 포맷(평면 `slots`, `position: {slot, order}`)은 전부 계속 파싱·렌더·통과. **`projects/todo`(confirmed)는 데이터·DP 무수정**(L1~L5·schema·dp-lint 회귀 0 확인). 신규/canvas 필드는 존재할 때만 검증.

**결정성 검증(실측)**: example 3개 화면 `render_screen.py --check` 통과(타임스탬프 무관 render_hash 동일). L5 음성 테스트로 가로 초과(col_start+col_span-1 > grid_columns)·locked 슬롯 침입 차단 확인.

**자동 강등 구현 정밀화**: ADR 결정 2(자동 강등)는 "오버라이드 없는 항목을 순서대로 세로 스택"이다. 구현은 브레이크포인트마다 2-pass로 처리한다 — (1)명시 좌표(base/at)가 점유한 행을 수집, (2)자동 강등 항목을 **점유 행을 건너뛰며 연속 스택**한다. 순수 자동(오버라이드 0)이면 1,2,3… 연속이 되어 결정 2와 일치하고, 명시·자동이 섞여도 **겹침 0**을 보장한다(명시 항목이 자신의 행을 차지하고 자동 항목이 그 사이를 메운다).

**레거시 confirmed 화면의 렌더 핀(주의)**: `projects/todo`처럼 **신규 엔진 이전에 생성된 confirmed 화면의 커밋된 `*.render.html`은 구 생성기 산출물**이라 신규 엔진의 `render_hash`와 일치하지 않을 수 있다(정상). todo는 데이터·DP·커밋된 렌더 모두 무수정으로 보존되며, 신규 엔진을 그 위에 재실행하지 않는다(D5 핀의 재현 검증은 신규/재인스턴스화 화면부터 적용). 또한 todo SCR은 `props`/`meta.label`/`props.columns`가 없는 레거시 데이터라 신규 엔진으로 렌더 시 라벨이 ref명으로 폴백된다 — 엔진 회귀가 아니라 레거시 데이터 한계이며, 재핀이 필요하면 인스턴스화·재작성 시 자연 해소된다.

---

## 11. 구현 메모 (rev.5, 2026-06-21 — 남은 결정 전부 완료)

**D4 — DS 카탈로그.** `harness-core/render/tokens.py`(DS-불가지론 토큰·allowlist 로더) + `engine.render_catalog` + `render_catalog.py`. 토큰은 **현재 design-system 폴더**(`ds-source/**/*.css`의 `:root` CSS 변수)에서 추출·분류(색상/타이포/치수/기타)하고, 컴포넌트는 `ds-allowlist.md`에서 description·props·usage·states까지 파싱. 산출 `foundation/design-system/catalog/index.html` = 색상 스와치 + 타이포 + 치수(+엔진 기본 spacing) + 컴포넌트 갤러리(표준 상태 세트) + 사용 가이드. 인라인 style·외부 CDN/폰트 0(색상 칩도 `[data-token]` 셀렉터로 칠함). 결정론적(`--check`).

**컴포넌트 상태 세트(결정 3·§9).** 표준 집합 `default·hover·focus·active·disabled·loading·error·selected·read-only·empty`. 컴포넌트별 표시 상태는 `ds-allowlist.md`의 선택 필드 `- **states**: ...` 선언을 따르고, 없으면 `engine.STATES_BY_REF` 종류 기반 추정. → §9 "상태 필드 형식" 미결정 해소.

**D5 — 해시 핀 배선(②③ 단일 출처).** `harness-core/render/pins.py`(`compute_pins`/`--verify`)를 ②③가 공유. **②** `spec-pack-guard.py`가 pack 발행 시 `pinned_contract.layout_hash`/`render_hash`를 `compute_pins`로 계산·기록(`--write-pins`)하고 재검증(불일치=stale→error). **③** `plugin-ai-web-dev/hooks/layout-hash-guard.py`가 Phase α에서 재렌더로 `layout_hash` 일치를 강제(불일치→빌드 실패; render_hash는 warn). "②확정 위치 ③변경 금지"의 기계적 강제.

**D6 — 렌더 환경 동결.** token-only 치수(magic number 금지; gap·padding·행/텍스트 높이 모두 `space` 토큰). editable 캔버스 행 `grid-auto-rows: minmax(space-8=48px, auto)`(결정 1), 텍스트 영역(테이블) `min-height` 고정으로 줄바꿈 변동 격리. 폰트는 **시스템 폰트 스택 동결**(외부 웹폰트·CDN 0) — 골든 PNG(픽셀 회귀, 결정 4)를 도입하지 않는 한 OS별 서브픽셀 차이는 수용(layout_hash 계약과 무관).

**의도적 미구현.** 골든 PNG(결정 4: layout_hash로 충분, 보류) · 챗봇 카탈로그 읽기전용 패널(② 챗봇 앱 미빌드, ADR-001 후속) · locked re-pin 알림 UX(동일).

**검증(실측).** 카탈로그 `--check` 결정성 OK(색상 10·컴포넌트 29) · ② `--write-pins`→재검증 통과·stale 차단(exit 1) · ③ 가드 layout_hash 일치 통과/불일치 빌드 실패 · ds-closure는 `states` 필드 무영향 · **todo 무수정**.
