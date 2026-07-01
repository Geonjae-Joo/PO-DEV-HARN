# ① PREREQUISITE — 준비 레이어

> Claude Code 플러그인 (`prerequisite`). 고객사/프로젝트당 **1회** 수행. 주체: 개발 리드/운영자.
> PO 작업(②)과 개발(③)이 시작되기 전에 **디자인 자산·규칙·앱 골격을 준비**한다.
> 산출물은 프로젝트 워크스페이스의 `projects/<id>/foundation/`에 작성되어 ②·③ 양쪽이 참조하고, **빈 `app_repo` 골격**을 스캐폴드한다 (baseline 실제 구현은 ③ Phase 0의 몫).

> 패키지 경로: `packages/plugin-prerequisite/`. 플러그인은 `marketplace.json`에 `prerequisite`로 등록(`/plugin marketplace add .` 후 활성화). 작업 대상은 IDE로 연 `projects/<id>/` 워크스페이스의 `foundation/`. 불변 규칙·공용 lib·렌더 엔진은 `packages/harness-core/`를 단일 출처로 공유한다.

---

## Workflow

```
1~2. DS 투입 + 허용집합 작성 — 두 진입 경로 중 하나 (둘 다 같은 DoD: ds-source/ + ds-allowlist.md)

   [경로 A — 수동] 기존 사내/맞춤 DS를 직접 투입할 때
     · design component를 projects/<id>/foundation/design-system/ds-source/ 에 직접 저장
       (새로 만들지 않음 — 기존 DS 그대로 투입, design token(:root CSS 변수) 포함)
     · ds-allowlist.md를 손으로 작성 — DS 컴포넌트 목록(이름·props·용도·states) + 사용 가이드

   [경로 B — 자동] 오픈소스 DS를 이름으로 도입할 때
     · skill: ds-bootstrap 실행 — DS 이름(예: "Vuetify", "Ant Design Vue", "shadcn-vue")만 주면
       웹서치로 설치법·컴포넌트·토큰 API를 조사 → ds-source/ 설치 + src/tokens.css(CSS 변수) 생성
       + ds-allowlist.md(≥25개 컴포넌트) 자동 작성 + plugin↔allowlist sync. 실행 앱 파일은 만들지 않음.

   → 두 경로 모두: ds-allowlist.md 저장 시 hook ds-guide-validate.py 자동 실행 (목록·필수 필드 검증)
   → 이 ds-allowlist.md가 ②의 layout-recommend skill과 lint L1의 허용 집합 원본이 된다 (DS 폐쇄)

2b. DS 자산 빌드 (시각 충실도 — ADR-002 D8, ds-bootstrap Phase 9)
   node harness-core/render/build_ds_assets.mjs --root projects/<id>
     · ds-compiled.css   — DS의 실제 CSS(토큰 + 컴파일된 유틸리티). Tailwind 컴파일(비-Tailwind는 raw 병합 폴백).
     · ds-fixtures.json  — allowlist 컴포넌트의 기본상태 마크업(Vue SSR). 렌더 엔진이 실제 DS 모양으로 그리는 근거.
   → 컴파일은 렌더 시점이 아니라 여기서 1회 + 커밋(결정성). 두 자산이 없으면 렌더는 와이어프레임으로 폴백.
   → 자산은 ds-source에서 파생 — DS를 바꾸면 재실행. (현재 생성기는 Vue SSR 지원, React SSR은 후속.)

3. skill: design-page-builder 실행
   DS를 조합해 캔버스 모델(canvas·grid·breakpoints·slots[locked/editable]) + layout(②와 통일된 screen-model-schema-v2 형태)으로 페이지 템플릿 생성 (DP-MAIN, DP-POPUP 등)
     · ②가 화면을 DP **복사**로 시작하므로 DP와 SCR은 같은 layout 스키마를 쓴다. locked=참조 상속, editable=복사 시딩(첫 렌더=DP 동일).
     └ 스킬이 생성 직후 scripts/design-page-lint.py 직접 호출 (DS 폐쇄 + 캔버스 모델 + layout 슬롯 참조 검증)
     └ harness-core/render/render_designpage.py 로 DP 미리보기, render_catalog.py 로 DS 카탈로그 생성
       (2b의 자산이 있으면 실제 DS 모양으로, 없으면 와이어프레임으로 렌더)

4. rules(불변 규칙) 확정 + 프로젝트 결정 핀
   rules: harness-core/rules/{constitution,spine-ids,ds-closure}.md   (전 프로젝트 공통 — 단일 원본)
   decisions: tech-stack.md / ops-stack.md                            (foundation/decisions/ — 프로젝트별 결정)
   + platform-baseline 명세: SPEC-000.md(공통 기능) / SPEC-OPS-000.md(배포·CI/CD·관측성)

5. 빈 app_repo 스캐폴드
   기술스택 골격 + design-system 투입 + SPEC-000·SPEC-OPS-000 명세 배치 + foundation/VERSION 핀
   (★ baseline·ops 코드를 여기서 구현하지 않는다 — ③ Phase 0가 전달 모드 A/B를 정해 구현/가이드 산출)
```

**DoD**: ds-allowlist.md 존재(lint·카탈로그 참조 가능) / **DS 자산(ds-compiled.css·ds-fixtures.json) 생성**(D8 — 미생성 시 와이어프레임 폴백) / design page 최소 1세트(DP-MAIN + DP-POPUP, 캔버스 모델) / DS 카탈로그 렌더 / constitution에 하드 룰 명시 / SPEC-000·SPEC-OPS-000 **명세**가 스파인 편입 / tech-stack·ops-stack 결정 확정(foundation/decisions/) / 불변 rules가 harness-core 단일 원본으로 존재 / foundation/VERSION 핀 / 스파인 ID 규칙 고정.

---

## Harness 자산

> **배치 원칙:** 단일 스킬이 직접 호출하거나 그 스킬 전용인 스크립트·파일은 **해당 스킬 폴더 아래에 공존**시킨다(예: `design-page-lint.py`). 저장 이벤트로 자동 실행되는 훅(스크립트는 `hooks/`, 선언은 `settings.json`)은 플러그인 최상위에 둔다. 여러 레이어가 공유하는 규칙·lib·렌더 엔진은 `harness-core/`에 둔다.

### Skills — 모델이 필요 시 로드하는 상세 가이드

| 파일 | 설명 |
|---|---|
| `skills/ds-bootstrap/SKILL.md` | **[경로 B 자동]** 오픈소스 DS 이름 하나로 ds-source/ 부트스트랩. 웹서치 조사 → 설치(`package.json`·`vite.config`)·`src/tokens.css`(CSS 변수 단일 소스, `tokens.py`가 소비)·`src/plugins/<ds>` 진입점 생성 + **`ds-allowlist.md` 자동 작성**(≥25개, lint L1 계약) + plugin↔allowlist sync 검증. 실행 앱 파일(main/App/index.html) 미생성. design-page-builder의 **선행 단계**(allowlist를 만들어 줌). |
| `skills/design-page-builder/SKILL.md` | DS 컴포넌트를 조합해 캔버스 모델(canvas·grid·breakpoints·locked/editable slots) 기반 빈 페이지 템플릿(DP-MAIN, DP-POPUP 등)을 생성하는 방법. 허용 집합(ds-allowlist.md) 참조, DS 밖 컴포넌트 발명 금지. 각 템플릿에 스파인 ID(DP-*) 부여. DP 렌더·DS 카탈로그 산출 (ADR-002 D7). |
| `skills/design-page-builder/scripts/design-page-lint.py` | **design-page-builder 전용.** 스킬이 템플릿 생성 직후 직접 호출하는 출력 검증기. 템플릿이 DS 허용 집합 안의 컴포넌트만 쓰는지 + 캔버스 모델(slots locked/editable·grid·breakpoints) 형식 + 스파인 ID(DP-*) 존재 검증. `harness-core/lib/ds_closure.py`를 import(실패 시 동치 폴백). |

### Hooks — 저장 이벤트 자동 실행 (AI 없는 결정론)

hooks는 플러그인 `settings.json`의 `hooks` 키에 Claude Code hook 이벤트(PostToolUse matcher + command)로 정의된다. 스크립트 경로: `${CLAUDE_PLUGIN_ROOT}/hooks/`. payload는 stdin JSON, 차단은 exit 2.

| 스크립트 | 이벤트 | 트리거 | 설명 |
|---|---|---|---|
| `hooks/ds-guide-validate.py` | `PostToolUse(Write\|Edit)` | ds-allowlist.md 저장 직후 | 컴포넌트 목록 형식, 필수 필드(이름·props·용도) 존재 여부 검증. 훅 payload(JSON)를 **stdin**으로 받아 파일 경로를 자기필터(ds-allowlist.md만 검증, 그 외 조용히 통과), 실패 시 **exit 2**로 모델에 피드백. |

### 공유 자산 — harness-core (전 레이어 공통)

규칙·렌더 엔진·lib는 ①만의 것이 아니라 ②③과 공유하므로 `packages/harness-core/`에 단일 원본으로 둔다.

| 파일 | 설명 |
|---|---|
| `harness-core/rules/constitution.md` | **전 레이어 공통 하드 룰.** screen model 단일 원본 / HTML 파생 뷰 / DS 폐쇄 / 캔버스 봉쇄 / 스파인 ID / optimistic locking / TDD / 커밋 규칙. |
| `harness-core/rules/spine-ids.md` | DP-/SCR-/CMP-/REQ-/ENT-/EXT-/NOTE-/NFR-/JRN-/SPEC-/T### 채번 규칙 + DP→SCR 인스턴스화 엣지. 전 레이어 공통 적용. |
| `harness-core/rules/ds-closure.md` | DS 집합 밖 컴포넌트를 screen model·design page에 추가하는 것을 금지하는 규칙 상세. ①의 design-page-lint + ②의 lint L1이 함께 강제. |
| `harness-core/lib/ds_closure.py` | DS 폐쇄 검증 단일 출처. ① design-page-lint + ② on-save-lint가 import. |
| `harness-core/render/render_designpage.py` | DP-*.yaml → 미리보기 HTML (locked=실제 컴포넌트, editable=그리드 오버레이). ① 전용 진입. |
| `harness-core/render/render_catalog.py` | tokens(ds-source CSS 변수) + ds-allowlist + 컴포넌트 메타 → `foundation/design-system/catalog/index.html` (색상 스와치·타이포·치수·컴포넌트 갤러리+상태 세트). 자산(D8) 있으면 갤러리를 실제 DS 모양으로 렌더. ① 전용 진입. PO의 "디자인 지시 근거". |
| `harness-core/render/build_ds_assets.mjs` | **DS 자산 빌더(D8, Node).** ds-source → `ds-compiled.css`(Tailwind 컴파일) + `ds-fixtures.json`(Vue SSR 컴포넌트 마크업). ① 준비단계 1회 실행·커밋. ds-bootstrap Phase 9. |
| `harness-core/render/{engine,tokens,ds_assets,instantiate_screen,pins,render_screen}.py` | 공용 엔진 코어·토큰 추출·**시각 충실도 자산 로더(ds_assets)**·인스턴스화·핀 계산·SCR 렌더 (주로 ②③이 사용, ①은 DP/카탈로그 렌더가 이 코어를 공유). |

### Decisions — 프로젝트별 스택 결정 (foundation 산출물)

규칙이 아니라 **프로젝트마다 확정하는 결정**이므로 `foundation/decisions/`에 둔다. foundation의 일부로 ②·③에 핸드오프된다.

| 파일 | 설명 |
|---|---|
| `foundation/decisions/tech-stack.md` | **앱 스택의 단일 출처.** 백엔드·프론트엔드 스택을 ①에서 프로젝트별로 확정한다(고정값 아님). 현재 선택 예시: 백엔드 Spring Boot / 프론트엔드 React+Vite+TS+Tailwind+shadcn/ui. ②·③·스킬·훅이 이 파일을 따른다. 변경 시 DECISIONS.md 갱신. |
| `foundation/decisions/ops-stack.md` | **운영 스택의 단일 출처.** 형상관리(GitHub\|GitLab)·CI/CD·배포 타깃(k8s\|Docker\|온프렘)·관측성(Phoenix\|Langfuse) 결정을 프로젝트별로 확정(고정값 아님). SPEC-OPS-000 명세의 *도구 선택*에 해당. ③ Phase 0·γ가 따른다. |

### Docs — 플러그인 동봉 참고 문서

| 파일 | 설명 |
|---|---|
| `docs/project-design-guide.md` | 프로젝트 디자인 가이드 작성법 (DS 투입·allowlist 작성 원칙). |
| `docs/first_design_page_guide.md` | 첫 design page(DP) 만들기 가이드. |

---

## 폴더 트리

```
packages/plugin-prerequisite/        # ① Claude Code 플러그인
├── README.md
├── plugin.json                      # 플러그인 매니페스트 (components·shared: ../harness-core)
├── settings.json                    # hook 이벤트 연결 (PostToolUse → ds-guide-validate.py)
├── skills/
│   ├── ds-bootstrap/
│   │   ├── SKILL.md                 # [경로 B] 오픈소스 DS 이름 → ds-source 설치 + tokens.css + ds-allowlist.md 자동 생성
│   │   └── evals/                   #   산출물 검증 명세(evals.json) — Ant Design Vue·Bootstrap Vue·PrimeVue 등
│   └── design-page-builder/
│       ├── SKILL.md                 # DS 조합 → 캔버스 모델 페이지 템플릿 + DP 렌더 + 카탈로그
│       └── scripts/
│           └── design-page-lint.py  # [스킬 전용] 템플릿 DS 폐쇄·캔버스 모델·스파인 ID 검증
├── hooks/
│   └── ds-guide-validate.py         # [저장 이벤트 훅] ds-allowlist.md 형식·목록 검증
└── docs/
    ├── project-design-guide.md
    └── first_design_page_guide.md

projects/<id>/foundation/            # ① 산출물 (Tier 2 데이터 — 플러그인이 작업하는 대상)
├── design-system/
│   ├── ds-source/                   #   사용자가 투입하는 기존 DS 원본 (CSS 토큰 포함)
│   ├── ds-allowlist.md              #   DS 컴포넌트 목록 + 사용 가이드 (②의 허용 집합 원본)
│   ├── ds-compiled.css              #   [D8] build_ds_assets 산출 — DS 실제 CSS (커밋, 렌더 인라인)
│   ├── ds-fixtures.json             #   [D8] build_ds_assets 산출 — 컴포넌트 기본상태 마크업 (커밋)
│   └── catalog/index.html           #   render_catalog.py 산출 시각 카탈로그
├── design-pages/
│   ├── DP-MAIN.yaml                 #   main page 템플릿 (canvas·grid·breakpoints·locked/editable)
│   ├── DP-POPUP.yaml                #   팝업/모달 페이지 템플릿
│   └── renders/DP-*.html            #   render_designpage.py 미리보기 (파생, 편집 금지)
├── platform-baseline/
│   ├── SPEC-000.md                  #   공통 기능 baseline 명세 (로그인/SSO/RBAC/admin)
│   └── SPEC-OPS-000.md              #   운영 baseline 명세 (배포·CI/CD·형상관리·관측성)
├── decisions/
│   ├── tech-stack.md                #   앱 기술스택 결정
│   ├── ops-stack.md                 #   운영 스택 결정
│   └── DECISIONS.md                 #   결정 로그
├── link-manifest.yaml               #   스파인 ID 등록 인덱스 (DP-* 등)
└── VERSION                          #   foundation 핀 (재현성 — ②③이 참조)
```

> 구 구조에서 `01-PREREQUISITE/.claude/`·`input/`·`output/`에 있던 것은 모두 이전됐다 — 코드는 `packages/plugin-prerequisite`+`harness-core`로, 데이터(ds-source·foundation)는 `projects/<id>/foundation/`으로. 자세한 매핑은 [`docs/MIGRATION-PLAN.md`](../../docs/MIGRATION-PLAN.md).

---

## 경계 원칙

이 레이어는 **명세와 자산까지만** 만든다.

- 불변 규칙·DS 허용집합·design page 템플릿·SPEC-000/OPS 명세를 **정의**한다.
- **계약(screen model)**은 ②, **구현(코드)**은 ③의 책임이다.
- baseline·ops 코드를 구현하지 않는다 — 무엇이 공통 기능/운영 요건인지 명세까지만, 구현은 ③ Phase 0.
- 새 DS 컴포넌트를 발명하지 않는다(기존 DS 그대로 투입).

상세 흐름은 루트 [`USER-GUIDE.md`](../../USER-GUIDE.md), 아키텍처는 [`docs/ADR-001`](../../docs/ADR-001-3runtime-architecture.md)·[`docs/ADR-002`](../../docs/ADR-002-deterministic-screen-render.md) 참조.
