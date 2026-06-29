# DevLog 실행 런북 — "어느 단계에서 어떤 스킬로, 어떻게 프롬프트하나"

> 이 문서는 [`USER-GUIDE-devlog-example.md`](USER-GUIDE-devlog-example.md)를 **실제로 따라 치며 실행하는 런북**이다. 예제 문서가 *무엇이 만들어지는지*를 보여준다면, 이 문서는 **각 단계에서 (1) 어떤 도구/스킬을, (2) 무슨 프롬프트로 호출하고, (3) 무엇이 나오면 성공인지**를 그대로 복사·입력 가능한 형태로 정리한다.
>
> 개념·경계·산출물의 의미는 예제 문서를, 스택 전환 배경은 그 [부록 B](USER-GUIDE-devlog-example.md#부록-b--스택-전환으로-재해석된-요구사항)를 본다.

## 표기 규약

| 표기 | 의미 |
|---|---|
| 💬 | Claude(또는 ② 챗봇)에게 **입력할 자연어 프롬프트**. 그대로 복사해 쓴다(필요값만 수정). |
| ⌨️ | **터미널/슬래시 명령**. `/`로 시작하면 Claude Code 슬래시, 아니면 셸. |
| 📂 | 작업 위치(IDE로 열어야 하는 디렉터리). |
| ✅ | 성공 판정 / 검증 방법. |
| 📤 | 이 단계의 산출물. |

> **스킬은 어떻게 불리나:** ①③은 Claude Code 플러그인이라, 자연어가 스킬 description에 맞으면 자동 로드되거나 `/스킬명`으로 호출한다(speckit은 `/speckit-*` 슬래시). ②의 챗봇 po-def-chat은 **빌드 예정**이고, 능력은 플러그인 `po-define`으로 마켓플레이스에 등록돼 있다 — 현재는 Claude Code를 `projects/devlog/`에서 열고 `packages/plugin-po-define/skills/`의 SKILL.md를 로드해(프로젝트 `.claude`에 스킬 경로를 추가하거나 해당 SKILL.md를 참조하게 함) 같은 프롬프트로 따라간다. 아래 💬 프롬프트는 챗봇/Claude Code 공통으로 **각 스킬의 트리거**에 해당한다.

---

## 단계 ↔ 스킬 ↔ 프롬프트 한눈에

| # | 레이어 | 단계 | 도구/스킬 | 호출 방식 |
|---|---|---|---|---|
| 0 | — | 워크스페이스·플러그인 | Claude Code | ⌨️ `/plugin …` |
| 1 | ① | DS 부트스트랩 | `ds-bootstrap` | 💬 자연어 |
| 2 | ① | 합성 컴포넌트+allowlist | `ds-bootstrap`/수동 | 💬 자연어 |
| 3 | ① | design page | `design-page-builder` | 💬 자연어 |
| 4 | ① | DS 카탈로그·결정·명세 | 렌더 엔진/수동 작성 | ⌨️/💬 |
| 5 | ② | 인스턴스화 | `layout-recommend`(Stage 0) | 💬 자연어 |
| 6 | ② | 레이아웃 | `layout-recommend`(Stage 1) | 💬 자연어 |
| 7 | ② | 액션 인터뷰 | `action-interview` | 💬 자연어(Q&A) |
| 8 | ② | 데이터 계약 | `entity-intake`/`external-intake` | 💬 자연어 |
| 9 | ② | 노트 | `note-intake` | 💬 자연어 |
| 10 | ② | 충분성 | `sufficiency-check` | 💬 자연어 |
| 11 | ② | Gate A | `gate-a-check` | 💬 "확정해줘" |
| 12 | ② | 여정 | `journey-map` | 💬 자연어 |
| 13 | ② | 발행 | `spec-generator` | 💬 "팩 발행" |
| 14 | ③ | 부트스트랩 | `install-speckit` | ⌨️ 셸 |
| 15 | ③ | Phase 0 baseline | `/speckit-*` | ⌨️ 슬래시 |
| 16 | ③ | Phase α scaffold | `/speckit-scaffold` | ⌨️ 슬래시 |
| 17 | ③ | Phase β 팩 구현 | `/speckit-specify→plan→tasks→implement` | ⌨️ 슬래시 |
| 18 | ③ | Phase γ E2E·NFR | Playwright + `/speckit-*` | 💬/⌨️ |

---

## 0. 사전 준비 (1회)

📂 저장소 루트에서 Claude Code 실행.

⌨️
```
/plugin marketplace add .
/plugin install prerequisite
/plugin install ai-web-dev
```

워크스페이스 생성 — `projects/devlog/.claude/settings.json`:
```json
{
  "env": { "PROJECT_ROOT": "." },
  "enabledPlugins": ["prerequisite", "ai-web-dev"]
}
```
폴더 골격: `projects/devlog/{foundation,model_repo,app_repo}/`.

✅ 이후 ①·③ 작업은 **`projects/devlog/`를 IDE로 열고** 진행(루트 아님 — 스크립트 상대경로가 `foundation/…`로 맞아야 함).

---

# ① PREREQUISITE — 개발 리드

📂 `projects/devlog/` 를 IDE로 연다. (prerequisite 플러그인 활성)

## 1단계 — DS 부트스트랩 (shadcn-vue)

**스킬:** `ds-bootstrap` (경로 B 자동). 오픈소스 DS 이름만 주면 설치+토큰+allowlist 생성.

💬
```
ds-bootstrap으로 shadcn-vue를 ds-source에 세팅해줘.
- 위치: foundation/design-system/ds-source/ (Vite vue-ts)
- Tailwind v4 + shadcn-vue init
- 가져올 컴포넌트: button input select textarea label card badge tabs switch skeleton avatar dropdown-menu separator form
- tokens.css는 다크 기본, 강조색 시안 계열(#00D9FF 근처)로 채워줘
- 실행 앱 파일(main.ts/App.vue/index.html)은 만들지 말고 참조 라이브러리로만.
```
> 기존 사내 DS를 직접 넣는 경우(경로 A)라면: 💬 `"기존 DS를 ds-source에 넣었어. ds-allowlist.md를 내가 부르는 컴포넌트로 작성해줘"` 로 수동 진행.

📤 `ds-source/`(package.json·vite.config·src/tokens.css·src/plugins/…) + `foundation/design-system/ds-allowlist.md`

✅ 저장 시 `ds-guide-validate.py` 훅 자동 실행. 수동 검증:
⌨️
```
PYTHONUTF8=1 python packages/plugin-prerequisite/hooks/ds-guide-validate.py
```
`✓ 컴포넌트 N개 발견` + `✓ ds-allowlist.md 검증 통과` 면 성공.

## 2단계 — 합성 컴포넌트 + allowlist 보강

shadcn 단품에 없는 DevLog 전용 부품을 **합성 컴포넌트**로 만들어 등록한다(임의 발명 금지, 가이드 §6).

💬
```
ds-source/src/components/ui/ 에 아래 합성 컴포넌트를 만들고 ds-allowlist.md에도 등록해줘(PascalCase 헤딩, description·props 필수):
- Header: 브랜드 + NavMenu + 테마토글 + auth actions
- PostCard: Card+Badge+좋아요 Button (props: post, liked, likeCount)
- FilterBar: Input(검색)+태그 Button 그룹+Select(정렬)
- PomodoroTimer: 원형 SVG 게이지 + 시작/정지/초기화 (props: targetSeconds, status, elapsed)
- ContributionGraph: 26×7 잔디밭 + 색강도 + hover 툴팁 (props: cells, levelOf)
- WeeklyChart: Chart.js(vue-chartjs) 막대 차트 래퍼
- StatCard: Card 기반 통계 카드
```
✅ 다시 `ds-guide-validate.py` 통과 확인(컴포넌트 수 증가).

## 3단계 — design page 생성

**스킬:** `design-page-builder`.

💬
```
design-page-builder로 DP-MAIN과 DP-POPUP을 만들어줘.
- DP-MAIN: canvas 12-col, breakpoints lg/md/sm.
  · slot header (locked): Header
  · slot content (editable, 12col)
  · slot footer (locked): Separator
- DP-POPUP: 모달 컨테이너(locked: 타이틀바·닫기) + body(editable). (DevLog는 모달이 없지만 DoD 최소 세트로 생성)
생성 직후 design-page-lint로 검증해줘.
```
📤 `foundation/design-pages/DP-MAIN.yaml`·`DP-POPUP.yaml` + `renders/DP-*.html`

✅
⌨️
```
PYTHONUTF8=1 python packages/plugin-prerequisite/skills/design-page-builder/scripts/design-page-lint.py
```
DS 폐쇄·캔버스 모델·DP- ID 통과 확인.

## 4단계 — DS 카탈로그 + 결정 + 명세

💬 DS 카탈로그 렌더:
```
render_catalog로 foundation/design-system/catalog/index.html 생성해줘. (PO가 이름으로 디자인 지시할 근거)
```

💬 결정·명세 작성(운영자가 확정):
```
다음 foundation 파일들을 작성해줘:
- decisions/tech-stack.md: 프론트 Vue3+Vite+TS+Tailwind+shadcn-vue / 백 Spring Boot 3(Java 21)+Spring Web+JPA / DB PostgreSQL 17 / 마이그레이션 Flyway / 인증 Spring Security+JWT / 차트 Chart.js / 테스트 Vitest+Vue Test Utils·JUnit5·Playwright
- decisions/ops-stack.md: GitHub + GitHub Actions + Docker(백 jar) + nginx(프론트 정적) + 사내망
- platform-baseline/SPEC-000.md: 공통기능 명세 — 데모계정 로그인(alice/bob/kim)·JWT 세션·보호라우트(/write,/dashboard) 다층방어·RBAC(본인 데이터만)·공통 Header(테마토글·로그아웃)·다크 기본+localStorage 영속. (명세까지만, 코드는 ③)
- platform-baseline/SPEC-OPS-000.md: 빌드(프론트 정적+백 jar)·배포(Docker, 사내망)·CI/CD·환경변수 분리(.env/.env.example)·관측성 명세
```

💬 골격·핀:
```
빈 app_repo 골격을 tech-stack에 맞춰 스캐폴드하고(backend Spring Boot, frontend Vue) foundation/VERSION을 핀해줘. baseline 코드는 만들지 마(③ Phase 0 몫).
```

✅ **① DoD:** ds-allowlist + DP-MAIN/DP-POPUP + 카탈로그 + SPEC-000/OPS 명세 + tech/ops-stack + VERSION.

---

# ② PO-DEFINE — PO (화면마다 반복)

📂 `projects/devlog/` (`po-define` 플러그인 스킬 로드 — 위 "스킬은 어떻게 불리나" 참조). 화면 5개를 **Stage 0→1→2→2.5→3→4→Gate A** 로 확정한다.

> 아래는 **첫 화면(SCR-BLOG-LIST)을 모든 Stage까지 전부** 보이고, 나머지 4개는 동일 패턴이라 핵심 프롬프트만 압축해 싣는다.

## 화면 1 — 메인 `SCR-BLOG-LIST` (전체 Stage)

### 5단계 — Stage 0 인스턴스화 (`layout-recommend`)
💬
```
DP-MAIN으로 새 화면을 시작할게. 이름 "메인", 도메인 BLOG, 타입 LIST.
```
📤 `model_repo/screens/SCR-BLOG-LIST.yaml`(status: draft, Header/Footer 상속, content 빈 캔버스, from_template 핀)

### 6단계 — Stage 1 레이아웃 (`layout-recommend`)
💬
```
content 캔버스에 위에서부터 배치해줘(전부 full width):
1행 PomodoroTimer, 2행 FilterBar(검색+태그 버튼 그룹+정렬 Select), 3행 PostCard 목록(반복).
PostCard 목록은 FilterBar 변경 시 다시 조회되게 reactive로 연결해줘.
```
✅ 저장 시 자동: schema-validate(Pre) → L1~L5 lint(Post) → `render_screen` HTML. L1·L5 통과 시 `status: layout_confirmed`.
수동 결정성 확인(선택):
⌨️ `python packages/harness-core/render/render_screen.py model_repo/screens/SCR-BLOG-LIST.yaml --check`

### 7단계 — Stage 2 액션 인터뷰 (`action-interview`)
💬 시작:
```
액션 인터뷰 시작하자. interactive 컴포넌트를 하나씩 물어봐줘.
```
스킬이 컴포넌트별로 질문한다. 답변 프롬프트 예(타이머·필터바·카드 순회):
💬
```
- FilterBar 검색: 입력하면 300ms 디바운스 후 제목·요약을 대소문자 무관 클라 필터링(서버 재요청 없음). 0건이면 빈 상태 UI. → ENT-POST query
- FilterBar 태그/정렬: 태그 고르면 그 태그만(선택 강조), 정렬 4종(최신/오래된/읽기짧은/긴). 검색+태그+정렬 동시 적용. → ENT-POST query
- PostCard 본문 클릭: 글 상세(SCR-BLOG-DETAIL)로 이동.
- PostCard 좋아요(♡): 클라 토글만(영구저장 X), 카운트 ±1, 상세이동 전파 차단, 글 ID 기준 상태 유지. → noop
- PomodoroTimer 정지: 로그인+1분 이상이면 학습로그 저장 후 "✓ N분 학습 기록됨". 비로그인은 저장 안 하고 안내. (permission: login) → ENT-STUDY-LOG mutate
각 액션의 Gherkin acceptance 초안 만들고 확정해줘.
```
📤 `actions[]`(REQ-BLOG-LIST.001~005) + acceptance + prompt_log. (`status: review` 방향)

### 8단계 — Stage 2.5 데이터 계약 (`entity-intake`)
action outcome이 `ENT-POST`·`ENT-STUDY-LOG`를 가리키므로 정의를 요구한다.
💬
```
ENT-POST 정의할게: slug(URL식별자,유일)·title·author·date(YYYY-MM-DD)·tag(단일)·excerpt(첫100자)·content·reading_time(분)·cover_image(선택,외부URL). ENT-USER에 belongs_to.
ENT-STUDY-LOG 정의할게: started_at(KST)·duration_seconds. ENT-USER에 belongs_to(본인 것만 조회).
물리 타입은 ③에서 파생할 거니까 의미·속성·관계까지만.
```
📤 `model_repo/entities/ENT-POST.yaml`·`ENT-STUDY-LOG.yaml`
> 외부 연동이 없으므로 `external-intake`는 호출하지 않는다(내부 인증 = SPEC-000). 만약 외부 API가 있었다면 💬 `"EXT-… 정의할게: 프로토콜·엔드포인트·인증·장애처리"`로 `external-intake` 호출.

### 9단계 — Stage 3 노트 (`note-intake`)
💬
```
노트 추가(원문 그대로 보존해줘): "타이머 시간은 한국 표준시(UTC+9) 기준. DB timestamp와 프론트 표시 형식이 일치하는지 반드시 검증해야 함."
```
📤 `notes[]`(NOTE-…, verbatim). AI는 `complexity: med` 태그만 제안(본문 불변).

### 10단계 — Stage 4 충분성 (`sufficiency-check`)
💬
```
이 화면 충분한지 점검해줘. 누락 있으면 질문해줘.
```
스킬이 기계 체크 + gap 분석 → `open_questions[]`. 답하거나 사유와 함께 보류:
💬 `"빈 상태 메시지는 '아직 글이 없어요'로. 정렬 기본값은 최신순."`

### 11단계 — Gate A (`gate-a-check`)
💬
```
이 화면 확정해줘. (PO 승인 — 6조건 점검)
```
✅ lint 0 + 충분성 pass + 전 action user_confirmed + open_questions 0(또는 deferred 사유) + 전역 ID 유일 + PO 승인 → `status: confirmed`.

---

## 화면 2~5 — 압축 프롬프트 시퀀스

각 화면 모두 **Stage 0 인스턴스화 → 1 레이아웃 → 2 액션 → (2.5) → 3 노트 → 4 충분성 → Gate A** 동일. 핵심 프롬프트만:

### 화면 2 — 글 상세 `SCR-BLOG-DETAIL`
💬 0: `DP-MAIN으로 새 화면. 이름 "글 상세", 도메인 BLOG, 타입 DETAIL.`
💬 1: `뒤로가기 링크 + (선택)커버 + 태그·읽기시간 + 제목 + 작성자·날짜 + 본문 + 로딩용 Skeleton 배치.`
💬 2: `load 시 ENT-POST 단건 조회(로딩 중 스켈레톤, 없는 slug면 404, 에러면 친근한 UI+'다시 시도'/'목록으로'). '← 목록으로'는 SCR-BLOG-LIST로 navigate. acceptance 만들어줘.`
💬 (2.5 생략 — ENT-POST 재사용) → 💬 4 `충분성 점검` → 💬 `확정해줘`

### 화면 3 — 글 작성 `SCR-BLOG-WRITE`
💬 0: `DP-MAIN으로 새 화면. 이름 "글 작성", 도메인 BLOG, 타입 FORM. 접근 권한 login(보호 라우트).`
💬 1: `Input(제목)+Select(태그)+Textarea(본문)+Button(발행/취소) 폼 배치.`
💬 2: `submit 시 ENT-POST mutate(저장→상세 이동→메인 즉시 반영). 제출 중 버튼 비활성+"저장 중...". 비로그인 직접 접근은 callbackUrl 붙여 로그인 리다이렉트. acceptance 만들어줘.`
💬 3: `노트(원문 보존): "slug는 제목에서 자동 생성(소문자·공백→하이픈·특수문자 제거), 읽기시간 약 500자당 1분, excerpt 본문 첫 100자, 작성자=로그인 이름, 날짜=오늘."`
💬 4 `충분성 점검` → 💬 `확정해줘`

### 화면 4 — 로그인 `SCR-AUTH-LOGIN`
💬 0: `DP-MAIN으로 새 화면. 이름 "로그인", 도메인 AUTH, 타입 LOGIN.`
💬 1: `가운데 Card에 Input(아이디)+Input(비번)+Button(로그인) + 데모 계정 안내 박스.`
💬 2: `submit 시 SCR-BLOG-LIST로 navigate(성공). 실패 시 "아이디 또는 비밀번호가 올바르지 않습니다". acceptance 만들어줘.`
> ⚠️ 인증 로직(JWT·세션·보호라우트)은 정의하지 않는다 — SPEC-000 공통기능(③ Phase 0). PO는 화면 흐름까지만.
💬 4 `충분성 점검` → 💬 `확정해줘`

### 화면 5 — 대시보드 `SCR-STUDY-DASHBOARD`
💬 0: `DP-MAIN으로 새 화면. 이름 "대시보드", 도메인 STUDY, 타입 DASHBOARD. 접근 권한 login(본인만).`
💬 1: `StatCard 3개(누적/이번주/streak) + ContributionGraph(잔디밭) + WeeklyChart(주간 막대) 배치.`
💬 2: `load 시 ENT-STUDY-LOG 조회 — 통계카드·잔디밭·주간차트. 본인 데이터만(RBAC), 비로그인은 리다이렉트. acceptance 만들어줘. (permission: login)`
💬 3 (**중요, complexity:high 유발**):
```
노트(원문 보존): "잔디밭 활동량→색강도 5단계: 0분=회색, ~30분=매우흐린시안, 30분~1h=흐린시안, 1~2h=중간시안, 2h+=진한시안. streak는 오늘부터 거꾸로 연속 학습한 일수. 마지막 칸=이번 주 토요일. 미래 날짜 opacity 낮춤. 모든 날짜 키는 로컬(KST) YYYY-MM-DD로 일관 생성."
```
> AI가 `complexity: high` 제안 → ③ speckit-plan에서 **bl-analyst** 자동 호출의 근거.
💬 4 `충분성 점검` → 💬 `확정해줘`

---

## 12단계 — 여정 (`journey-map`)
5개 화면이 모두 confirmed 된 후:
💬
```
전체 화면의 navigate/mutate를 모아 여정을 만들어줘. 고립 화면도 찾아줘.
```
📤 `model_repo/journeys/JRN-BROWSE-READ.yaml`·`JRN-WRITE-POST.yaml`·`JRN-STUDY-TRACK.yaml`. ✅ 고립 화면 0.

## 13단계 — 발행 (`spec-generator`)
💬
```
confirmed 화면을 엔티티 응집 기준으로 팩으로 묶어 발행해줘.
로그인은 SPEC-000 공통기능이라 팩에서 빼고.
```
스킬이 발행 전 `spec-pack-guard.py`로 confirmed·ENT 참조 무결·pin(layout_hash/render_hash) 검증·기록.
📤 `model_repo/specs/PACK-BLOG/`(LIST+DETAIL+WRITE, ENT-POST) · `PACK-STUDY/`(DASHBOARD+타이머, ENT-STUDY-LOG)

✅ 수동 가드 확인(선택):
⌨️ `python packages/plugin-po-define/skills/spec-generator/scripts/spec-pack-guard.py --write-pins`

---

# ③ AI-WEB-DEV — 개발자 (4 Phase)

📂 `projects/devlog/app_repo/` (ai-web-dev 플러그인). 스택은 ①의 tech-stack.md(**Vue + Spring Boot**)에서 파생.

## 14단계 — 부트스트랩 (1회)
⌨️
```
bash packages/plugin-ai-web-dev/hooks/install-speckit.sh    # Windows: install-speckit.ps1
```
📤 `app_repo/.specify/` vendoring + git 훅 설치.

## 15단계 — Phase 0 Baseline (로그인·테마가 여기서 구현됨)
⌨️ `/speckit-specify`
💬 (scope + 전달 모드 결정)
```
SPEC-000·SPEC-OPS-000 받아서 baseline-delivery-manifest.yaml 만들어줘.
- 데모계정 로그인/JWT 세션: 모드 B (Spring Security+JWT 완성 코드+테스트, alice/bob/kim 하드코딩, 주석에 운영 bcrypt 필수)
- 보호 라우트 다층 방어: 모드 B (SecurityFilterChain + Vue 라우터 가드)
- RBAC 본인 데이터만: 모드 A (baseline-guides/)
- 공통 Header(테마토글·로그아웃·스켈레톤): 모드 A
- 다크 기본+localStorage: 모드 A
운영: 환경변수 분리·Docker 빌드·CI는 모드 B, 사내망 배포 차이는 모드 A.
```
모드 B 기능 구현 루프:
⌨️ `/speckit-plan` → `/speckit-tasks` → (💬 `Gate B 체크리스트 점검하고 승인할게`) → `/speckit-implement`
모드 A 기능:
💬 `baseline-guides/<feature>/SKILL.md로 예시 코드블럭+패턴 가이드 작성해줘 (RBAC 본인필터, Header 슬롯, 테마 토글).`
📤 `baseline-delivery-manifest.yaml` + (B) Spring Security·JWT·라우터가드 실제 코드+테스트 + (A) `app_repo/.claude/skills/baseline-guides/`

## 16단계 — Phase α Layout Scaffold (전체 화면 1회)
⌨️ `/speckit-scaffold`
💬 (필요 시) `confirmed 화면 5개를 Vue shell로 일괄 생성해줘(.vue, layout만, wiring 없음).`
✅ `layout-hash-guard.py`가 각 화면을 ②와 동일 엔진으로 재렌더 → `layout_hash` 일치 강제(불일치 시 빌드 차단). 앱 띄우면 5개 화면이 데이터 없이 layout만(walking skeleton).
📤 `app_repo/frontend/src/pages/*.vue` (라우팅 연결)

## 17단계 — Phase β 팩 구현 (팩마다 반복)

### PACK-BLOG
⌨️
```
/speckit-specify     # PACK-BLOG scope 확인 (LIST/DETAIL/WRITE, ENT-POST)
/speckit-plan        # ENT-POST → JPA 엔티티 + posts 테이블(Flyway) + slug UNIQUE 인덱스
                     # API: GET /api/posts, GET /api/posts/{slug}, POST /api/posts
                     # 프론트 wiring: 검색/태그/정렬/좋아요는 클라(Vue computed/composable), 디바운스 300ms
/speckit-tasks       # test-first 정렬, [P] 병렬
```
💬 `Gate B 체크리스트(Data Model·ERD·Task·bl 미해결 0) 점검하고 승인할게.`
⌨️ `/speckit-implement`
> `test-author`가 REQ-BLOG-* acceptance → 실패 테스트 먼저(API: JUnit5 / 화면: Vitest+Vue Test Utils) → red→green→refactor. `tdd-gate`·`commit-spine-id` 강제. 커밋 예: `[PACK-BLOG/T002] Post 엔티티 (REQ-BLOG-WRITE.001)`. 끝나면 `code-reviewer` 검토.

### PACK-STUDY (complexity:high → bl-analyst)
⌨️ `/speckit-plan`
💬
```
ENT-STUDY-LOG → study_logs 테이블 + user_id 인덱스. API: POST /api/study-logs(기록), GET /api/study-logs/stats(집계).
대시보드 노트가 complexity:high니까 bl-analyst로 잔디밭 색강도 decision table·streak 연속일 알고리즘·worked examples 만들어줘. KST 타임존 날짜 키 정합도 명세.
```
⌨️ `/speckit-tasks` → (💬 `Gate B 승인` — bl-analyst 미해결 0 확인) → `/speckit-implement`
> RBAC "본인 것만"은 Phase 0 모드 A 가이드(`baseline-guides/`)를 로드해 `user_id` 필터 적용.

## 18단계 — Phase γ Integration & NFR (배포 전)
💬
```
JRN-* 여정을 Playwright E2E로 구현해줘(새 시나리오 발명 금지, 화면 acceptance 재사용):
- JRN-BROWSE-READ → e2e/browse-read.spec.ts (검색·필터 → 상세)
- JRN-WRITE-POST → e2e/write-post.spec.ts (로그인 → 작성 → 목록 즉시 반영)
- JRN-STUDY-TRACK → e2e/study-track.spec.ts (타이머 저장 → 대시보드 통계 증가)
NFR도 점검: 검색 디바운스·입력 검증(SER-003)·에러 메시지 안전성(SER-004)·동시 접속.
배포는 ops-stack(Docker, 사내망) 따라 준비.
```
커밋: `[E2E/JRN-STUDY-TRACK] …`
> 📌 Next.js 고유 NFR(SSR/LCP·loading.tsx·Hydration·Standalone·PM2)은 Vue+Spring Boot 등가물로 재해석 — [예제 부록 B](USER-GUIDE-devlog-example.md#부록-b--스택-전환으로-재해석된-요구사항).

---

## 막히면 (FAQ)

| 증상 | 원인 | 해결 |
|---|---|---|
| 저장이 막힌다(schema) | px/auto 좌표·필수필드 누락 | 반응형 `base/at` 정수 좌표로, 누락 필드 보강 |
| L1 lint error | DS 밖 컴포넌트 ref | ds-allowlist에 정식 추가(① 2단계) 후 사용 |
| L5 canvas-bounds error | col_start+col_span-1 > grid_columns 또는 locked 슬롯 침범 | 캔버스 폭 안으로, locked 영역 건드리지 말 것 |
| Gate A 거부 | 6조건 중 미충족(보통 open_questions·미확정 action) | sufficiency-check 재실행 → 답/보류 |
| 발행 거부(spec-pack-guard) | confirmed 아님 / ENT dangling / pin stale | 화면 confirmed·ENT 정의·재핀 |
| Phase α 빌드 차단 | layout_hash 불일치(③이 위치 변경) | ② Gate A 재확정 → re-pin (③에서 위치 못 바꿈) |
| tdd-gate가 commit 차단 | 테스트 없음/실패 | test-author로 테스트 먼저. 러너 미설정 시 `HARNESS_TEST_CMD` 지정 |
| 커밋 거부 | 메시지에 스파인 ID 없음 | `[PACK-BLOG/T001] 요약 (REQ-…)` 형식 |

---

## 한 줄 요약 흐름

```
① /plugin → ds-bootstrap → 합성+allowlist → design-page-builder → 카탈로그·결정·SPEC → app_repo 골격
② (화면×5) 인스턴스화 → 레이아웃 → 액션인터뷰 → 엔티티 → 노트 → 충분성 → "확정해줘"
   → journey-map → "팩 발행"
③ install-speckit → Phase0(/speckit-* 모드 A/B) → /speckit-scaffold
   → (팩×2) /speckit-specify→plan→tasks→[Gate B]→implement → Phase γ Playwright
```
모든 화살표는 스파인 ID로 연결되어, 글 한 줄·잔디밭 한 칸까지 어느 화면·요구사항에서 왔는지 끝까지 역추적된다.
