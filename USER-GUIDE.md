# USER GUIDE — PO·개발자 웹앱 개발 워크플로우

> 이 문서는 **무엇을 누가 어떤 순서로** 하는지에 대한 실전 가이드다. 개념·아키텍처는 [`README.md`](README.md)·[`docs/ADR-001`](docs/ADR-001-3runtime-architecture.md)·[`docs/ADR-002`](docs/ADR-002-deterministic-screen-render.md), 각 레이어 상세는 패키지 README를 참조한다.
>
> 한 줄 원칙: **①이 틀을 깔고 → ②(PO)가 화면을 계약으로 확정하고 → ③(개발자)가 계약을 코드로 구현한다.** 어느 단계도 하류의 책임을 침범하지 않으며, 모든 산출물은 스파인 ID로 끝까지 추적된다.

---

## 0. 등장 인물과 도구

| 역할 | 담당 레이어 | 도구 | 작업 위치 |
|---|---|---|---|
| **개발 리드/운영자** | ① PREREQUISITE | Claude Code (IDE) + `prerequisite` 플러그인 | `projects/<id>/foundation/` |
| **PO (도메인 전문가)** | ② PO-DEFINE | 챗봇 po-def-chat(빌드 예정) / 현재는 Claude Code + `po-define` 플러그인 스킬 | `projects/<id>/model_repo/` |
| **개발자** | ③ AI-WEB-DEV | Claude Code (IDE) + `ai-web-dev` 플러그인 | `projects/<id>/app_repo/` |

세 역할은 **같은 `projects/<id>/` 워크스페이스를 참조**한다(복사 아님). `foundation/VERSION`으로 핀해 재현성을 보장한다.

---

## 1. 프로젝트 시작 — 워크스페이스 + 플러그인 준비 (1회)

```bash
# 1) 마켓플레이스 등록 (저장소 루트에서, 1회)
#    Claude Code 안에서:
/plugin marketplace add .
/plugin install prerequisite        # ① 개발 리드용
/plugin install ai-web-dev          # ③ 개발자용

# 2) 새 프로젝트 워크스페이스 생성
#    projects/<customer-id>/ 를 만들고 .claude/settings.json 에 PROJECT_ROOT + 활성 플러그인 지정
```

- `projects/<id>/.claude/settings.json` — 이 프로젝트에서 활성화할 플러그인과 `PROJECT_ROOT`를 지정한다.
- 이후 ①·③ 개발자는 **`projects/<id>/`를 IDE로 열어** 작업한다(루트가 아님). 그래야 스크립트의 상대경로(`foundation/…`)가 맞는다.

---

## 2. ① 준비 — 개발 리드 (프로젝트당 1회)

목표: PO가 백지에서 시작하지 않도록 **디자인 자산·규칙·골격**을 못 박는다.

1~2. **DS 투입 + 허용집합 작성** — 두 진입 경로 중 하나를 고른다. 결과는 같다: `ds-source/` + `ds-allowlist.md`.
   - **[경로 A — 수동]** 기존 사내/맞춤 DS가 있을 때. 디자인 시스템(컴포넌트 + `:root` CSS 토큰)을 `foundation/design-system/ds-source/`에 그대로 저장하고(새로 만들지 않음), `foundation/design-system/ds-allowlist.md`에 컴포넌트 목록(이름·props·용도·states)을 손으로 적는다.
   - **[경로 B — 자동, `ds-bootstrap` 스킬]** 오픈소스 DS를 이름으로 도입할 때. *"Vuetify로 ds-source 세팅해줘"* 처럼 DS 이름만 주면 — 웹서치로 설치법·컴포넌트·토큰 API를 조사해 `ds-source/`에 설치하고, `src/tokens.css`(CSS 변수 단일 소스)와 `ds-allowlist.md`(≥25개 컴포넌트)를 자동 생성하며 plugin↔allowlist 일치까지 맞춘다. 실행 앱 파일(main/App/index.html)은 만들지 않는다(참조 라이브러리만).
   - 어느 경로든 `ds-allowlist.md` 저장 시 `ds-guide-validate` 훅이 형식을 검증한다. → 이후 ②의 모든 화면은 이 목록 안에서만 컴포넌트를 쓴다(DS 폐쇄).
   - **[경로 B 이후] DS 자산 빌드** — `ds-bootstrap`이 Phase 9에서 `node harness-core/render/build_ds_assets.mjs --root projects/<id>`로 `ds-compiled.css`(DS 실제 CSS) + `ds-fixtures.json`(컴포넌트 마크업)을 1회 컴파일·커밋한다(ADR-002 D8). 이 둘이 있어야 카탈로그·DP·화면이 **실제 DS 모양**으로 렌더된다 — 없으면 라벨박스 와이어프레임. 경로 A(수동 DS)도 DS가 Vue/Tailwind면 같은 명령으로 생성한다.
3. **design page 생성** — `design-page-builder` 스킬로 페이지 템플릿(DP-MAIN, DP-POPUP 등)을 만든다. 각 DP는 **캔버스 모델**(고정 영역 `locked` + 편집 캔버스 `editable` + grid·breakpoints)을 가진다. 스킬이 생성 직후 `design-page-lint`로 DS 폐쇄·캔버스 모델을 검증한다.
4. **DS 카탈로그 렌더** — 렌더 엔진이 `foundation/design-system/catalog/index.html`을 생성한다(색상 스와치·타이포·컴포넌트 갤러리 — D8 자산이 있으면 **실제 DS 모양**). **PO가 "이 컴포넌트를 여기에"라고 이름으로 지시하는 근거**가 된다.
5. **결정·명세 확정** —
   - `foundation/decisions/tech-stack.md`(백엔드·프론트엔드 스택) · `ops-stack.md`(형상관리·CI/CD·배포·관측성)
   - `foundation/platform-baseline/SPEC-000.md`(공통 기능: 로그인/SSO/RBAC) · `SPEC-OPS-000.md`(운영) — **명세까지만, 코드는 ③ Phase 0.**
6. **app_repo 골격 스캐폴드** + `foundation/VERSION` 핀.

✅ **완료 기준(DoD)**: ds-allowlist 존재 / DS 자산(ds-compiled.css·ds-fixtures.json, D8) 생성 / DP 최소 1세트 + 카탈로그 / SPEC-000·OPS 명세 / tech·ops-stack 결정 / VERSION 핀. (상세: [plugin-prerequisite README](packages/plugin-prerequisite/README.md))

---

## 3. ② 화면·요구사항 정의 — PO (화면마다 반복)

목표: 코드를 한 줄도 쓰지 않고, **개발자가 화면 하나만 보고 spec을 만들 수 있을 만큼** 계약(screen model)을 모은다.

| 단계 | PO가 하는 일 | 결과 |
|---|---|---|
| **Stage 0 — 인스턴스화** | DS 카탈로그/DP 미리보기에서 design page를 고르고 화면 이름·도메인·타입을 입력 | `SCR-` 채번, 고정 영역 상속 + 빈 캔버스로 새 `SCR-*.yaml`(draft) |
| **Stage 1 — 레이아웃** | "주문 테이블, 기간 필터, 엑셀 버튼…"처럼 자연어로 지시 → AI가 DS 컴포넌트를 캔버스에 배치 | 저장 시마다 schema 검증 → L1~L5 lint → HTML 렌더 자동. L1·L5 통과 → `layout_confirmed` |
| **Stage 2 — 액션 인터뷰** | interactive 컴포넌트별 "이 버튼을 누르면?" 순회 질문에 답 | `actions[]`(trigger/outcome/permission) + Gherkin acceptance |
| **Stage 2.5 — 데이터 계약** | action이 데이터를 읽고/쓰면 그 출처를 정의 | 개념 엔티티 `ENT-` / 외부 연동 `EXT-` (의미·속성·관계까지만, 물리 설계는 ③) |
| **Stage 3 — 노트** | 비즈니스 규칙·예외를 자유롭게 구술 | verbatim 노트(AI가 본문 수정 안 함, 복잡도 태그만 제안) |
| **Stage 4 — 충분성** | AI가 누락을 찾아 다시 질문 → 답하거나 사유와 함께 보류 | gap 0 또는 deferred(사유) |
| **Gate A** | "확정해줘" 명시 요청 | 6조건(lint 0·충분성·전 action 확정·전역 ID 유일·PO 승인) 통과 → `confirmed` |
| **발행** | "팩 발행해줘" | confirmed 화면 → 도메인 단위 **PACK-* 팩** + layout/render 핀 → ③ 인계 |
| **여정(횡단)** | 여러 화면 confirmed 후 | navigate 집계 → `JRN-*` 여정 (③ E2E 출처) + 고립 화면 탐지 |

**PO를 위한 원칙**
- 화면 model(YAML)이 **단일 진실원**이다. 렌더된 HTML은 보기용이며 직접 고치지 않는다 — 고치고 싶으면 model을 바꾼다.
- ①이 준 DS·design page 밖으로 나갈 수 없다(컴포넌트 발명 금지, 고정 영역 침범 금지). 새 컴포넌트가 꼭 필요하면 ①에 요청한다.
- 막히면 AI가 HITL로 다시 묻는다. **충분히 답해야** Gate A를 통과한다 — 여기서 모은 정보가 곧 개발 품질이다.

(상세: [po-define README](packages/plugin-po-define/README.md))

---

## 4. ③ 구현 — 개발자 (4 Phase)

목표: ②의 확정 계약을 **test-first로 `app_repo` 하나에** 구현한다. 새 계약은 만들지 않는다.

### 부트스트랩 (1회)
```bash
# app_repo 에서 speckit 메커니즘 vendoring + git 훅 설치
bash packages/plugin-ai-web-dev/hooks/install-speckit.sh   # (Windows: install-speckit.ps1)
```

### Phase 0 — Baseline (프로젝트 1회)
`SPEC-000`·`SPEC-OPS-000`을 받아 **각 공통 기능의 전달 모드**를 정한다.
- **모드 A(가이드)** — 프로젝트마다 변형되는 기능(권한 조건부 렌더 등) → `baseline-guides/` 예시 코드·패턴으로.
- **모드 B(직접 주입)** — 변형 불필요한 기능(로그인/SSO/JWT/RBAC) → 완성 코드 + 테스트로.
- 판정: *"프로젝트마다 변형되나?"* → 예면 A, 아니면 B. 결과는 `baseline-delivery-manifest.yaml`.

### Phase α — Layout Scaffold (전체 화면 확정 후 1회)
```
/speckit-scaffold     # 전체 confirmed screen model → 프론트엔드 shell 일괄 생성 (layout만)
```
- `layout-hash-guard`가 각 화면을 ②와 동일 엔진으로 재렌더해 `layout_hash` 일치를 강제한다. **②확정 위치를 ③이 바꿀 수 없다** — 불일치면 빌드 차단.

### Phase β — Spec Pack Iteration (팩마다 반복)
```
/speckit-specify   # 팩 scope 확인 (pack-to-spec.py 로 spec.md 초안)
/speckit-plan      # ENT-/EXT- 계약 → Data Model·ERD·API 파생 (발명 금지). complexity:high → bl-analyst
/speckit-tasks     # T### 태스크, test-first 정렬
   ── Gate B (개발자 소유): Data Model·ERD·BL·Task 확정, bl 미해결 0, approve 전 구현 금지 ──
/speckit-implement # test-author → red → green → refactor → commit (tdd-gate·commit-spine-id 강제)
   → code-reviewer subagent 검토
```

### Phase γ — Integration & NFR (배포 전)
- ②의 `JRN-*` 여정 1개 → Playwright(+BDD) E2E 1개(새 시나리오 발명 금지, acceptance 재사용).
- NFR(성능·동시성·보안·감사) + 관측성(Phoenix/Langfuse) + 배포(ops-stack.md).

(상세: [plugin-ai-web-dev README](packages/plugin-ai-web-dev/README.md))

---

## 5. 계약이 바뀌면 — Change Order 루프

구현 중 PO가 화면을 고치고 싶을 때, 자동 재생성하지 않는다.

```
PO가 confirmed 화면 수정 요청
  → ③: 스파인 ID 단위 diff + blast radius 계산 → 변경 지시서
  → ③ 개발자 판정:
      dismiss    (외관/무관)  → re-pin
      amend      (경미)       → 제자리 수정 후 re-pin
      regenerate (중대)       → ② PO가 기존 Gate A 흐름으로 재확정
                                → ② spec-generator가 해당 팩만 버전 +1 재발행
                                → ③ 새 Gate B 후 재구현
```

핵심: **재정의는 항상 ②로 돌아간다.** ③는 판정과 blast radius까지만 — 새 계약을 만들지 않는다. acceptance가 바뀌면 기존 테스트가 깨져(breaking) TDD가 백스톱이 된다.

---

## 6. 자주 막히는 지점 (FAQ)

- **"PO가 원하는 컴포넌트가 DS에 없다"** → ②에서 발명 금지. ①에 추가 요청 → ds-allowlist·DP·카탈로그 갱신 후 ②가 사용.
- **"렌더된 HTML을 직접 고치고 싶다"** → 금지(다음 렌더에 덮어쓰임). screen model(YAML)을 고친다.
- **"Phase α 빌드가 layout_hash 불일치로 막힌다"** → ②확정 위치를 ③이 바꾼 것. 위치 변경은 ② Gate A 재확정 → re-pin으로만.
- **"tdd-gate가 commit을 막는다"** → 테스트가 없거나 실패한 것. 테스트 먼저(test-author) 작성. 러너 미설정이면 `HARNESS_TEST_CMD` 지정.
- **"spec.md를 직접 쓰면 되나?"** → 아니다. `pack-to-spec.py`로 PACK + screen model에서 초안을 생성한 뒤 검토한다(권위는 screen model).
- **"커밋이 거부된다"** → 메시지에 스파인 ID가 빠진 것. `[PACK-ORDER/T001] 요약 (REQ-...)` 형식.

---

## 7. 한눈에 — 추적 그래프

```
①  DP- (design page)  ─ 인스턴스화 →
②  SCR- → CMP- → REQ- → acceptance(Gherkin)        ┐
                  └ ENT-/EXT- (데이터 계약)            ├→  PACK-* (도메인 팩)
   JRN- (여정, navigate 집계)                          ┘
                                                         │
③  PACK- → spec.md/plan.md → T### (task) → test → commit  → app_repo
   JRN- → Playwright e2e-test → commit
```

모든 화살표는 스파인 ID로 연결되어, 한 줄의 코드도 어느 화면·요구사항에서 왔는지 끝까지 역추적된다.
