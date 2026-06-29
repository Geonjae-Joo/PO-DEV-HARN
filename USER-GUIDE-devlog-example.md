# USER GUIDE 실전 예제 — DevLog (개발자 학습 트래커 + 미니 블로그)

> 이 문서는 [`USER-GUIDE.md`](USER-GUIDE.md)의 워크플로우를 **실제 SRS 한 건**(`DevLog_raw.md`)에 그대로 적용한 워크스루다. 개념·규칙은 USER-GUIDE를, 각 레이어 상세는 패키지 README를, 또 다른 예제는 [`USER-GUIDE-calculator-example.md`](USER-GUIDE-calculator-example.md)를 참조한다.
>
> **만들 앱:** 사내 개발자가 로그인해 글을 쓰고/읽고, 포모도로 타이머로 학습 시간을 기록하며, 개인 대시보드(잔디밭·주간 차트·통계)로 학습을 가시화하는 **학습 트래커 + 미니 블로그**.
>
> **이 예제의 스택(중요):** 원본 `DevLog_raw.md`는 Next.js 풀스택(Server Actions·Drizzle·NextAuth) 기준으로 쓰였지만, **이 프로젝트는 스택을 바꿔서 진행한다.**
>
> | 계층 | 원본 SRS | **이 예제(현재 환경)** |
> |---|---|---|
> | 프론트엔드 | Next.js(App Router) + React | **Vue 3 + Vite + TypeScript + Tailwind** |
> | 디자인 시스템 | (Tailwind 직접) | **shadcn-vue** (shadcn/ui의 Vue 포팅 — `project-design-guide.md` 절차를 Vue용으로 적응) |
> | 백엔드 | Next.js Server Actions | **Spring Boot 3 (Java 21) + Spring Web** |
> | 데이터 | Drizzle ORM | **Spring Data JPA + Flyway 마이그레이션** |
> | DB | PostgreSQL 17 | PostgreSQL 17 (동일) |
> | 인증 | NextAuth(Credentials, JWT) | **Spring Security + JWT** (데모 계정) |
> | 차트 | Recharts | **Chart.js (vue-chartjs)** |
> | 배포 | Next.js Standalone + PM2 | **프론트 정적 빌드(nginx) + 백엔드 jar(Docker)** |
>
> 스택 전환으로 **재해석되거나 ③/①으로 재배치되는 Next.js 고유 요구사항**(SSR/LCP·`loading.tsx`·Hydration·Standalone·PM2 등)은 [부록 B](#부록-b--스택-전환으로-재해석된-요구사항)에 따로 정리했다.

---

## 이 예제에서 미리 보는 스파인 ID 지도

워크플로우를 따라가며 아래 ID들이 차례로 채번된다. 끝에서 한 줄도 빠짐없이 역추적된다.

```
①  DP-MAIN, DP-POPUP                                  (design page 템플릿)
①  SPEC-000   (로그인/세션/RBAC/공통 레이아웃/테마 토글 공통기능 명세)  → ③ Phase 0가 구현
   SPEC-OPS-000 (빌드·배포·관측성 명세)
②  SCR-BLOG-LIST       ← DP-MAIN 인스턴스화   (메인: 글 목록+검색+필터+정렬+좋아요+타이머)
    SCR-BLOG-DETAIL     ← DP-MAIN 인스턴스화   (글 상세)
    SCR-BLOG-WRITE      ← DP-MAIN 인스턴스화   (글 작성)
    SCR-AUTH-LOGIN      ← DP-MAIN 인스턴스화   (로그인)
    SCR-STUDY-DASHBOARD ← DP-MAIN 인스턴스화   (개인 대시보드)
    ENT-POST, ENT-STUDY-LOG, ENT-USER                 (데이터 계약)
    (EXT 없음 — 내부 인증이라 외부연동 없음. 커버 이미지는 정적 URL)
    JRN-BROWSE-READ, JRN-WRITE-POST, JRN-STUDY-TRACK  (여정)
②  PACK-BLOG (글 목록/상세/작성), PACK-STUDY (타이머+대시보드)   (도메인 팩)
③  T001…, e2e/JRN-*, commit                            (구현·테스트·커밋)
```

> **먼저 알아둘 경계 두 가지:**
> 1. **로그인/인증은 공통 기능이다.** 계산기 예제와 똑같이, 인증·세션·JWT·보호 라우트·RBAC는 PO가 계약으로 정의하는 게 아니라 ①의 **SPEC-000 명세** → ③ **Phase 0(모드 B)** 가 구현한다. PO는 로그인 *화면의 레이아웃*과 "로그인 버튼 → 인증 → 메인" 이라는 *화면 흐름*까지만 ②에서 정의한다. (DevLog는 외부 SSO가 아니라 **사내 데모 계정 내부 인증**이라, 계산기 예제의 `EXT-SSO` 같은 외부 연동 계약이 **없다** — 이게 두 예제의 차이다.)
> 2. **스택 고유 사항은 PO 계약이 아니다.** SSR·`loading.tsx`·Standalone·PM2 같은 Next.js 관용구는 화면 계약(②)이 아니라 ①의 결정(tech-stack/ops-stack·SPEC-OPS-000)이거나 ③의 구현 디테일이다. 스택을 Vue+Spring Boot로 바꾸면 이들은 자연히 그 스택의 등가물로 재해석된다([부록 B](#부록-b--스택-전환으로-재해석된-요구사항)).

---

## 0. 등장 인물 (이 프로젝트)

| 역할 | 누가 | 무엇을 |
|---|---|---|
| 개발 리드 | 운영자 | ① DS(shadcn-vue)·DP·SPEC-000·tech-stack 준비 |
| PO | DevLog 서비스 기획자 | ② 화면 5개를 screen model로 확정 |
| 개발자 | 프론트/백엔드 | ③ `app_repo`에 Vue + Spring Boot로 구현 |

스택 결정: 프론트 **Vue 3 + Vite + TS + Tailwind + shadcn-vue** / 백엔드 **Spring Boot 3 (Java 21) + JPA** / DB **PostgreSQL 17** (`foundation/decisions/tech-stack.md`에 핀).

---

## 1. 프로젝트 시작 (1회)

```
/plugin marketplace add .
/plugin install prerequisite
/plugin install ai-web-dev

# 새 워크스페이스
projects/devlog/.claude/settings.json   ← PROJECT_ROOT + 활성 플러그인
```

이후 ①·③ 작업자는 `projects/devlog/`를 IDE로 연다.

---

## 2. ① 준비 — 개발 리드 (프로젝트당 1회)

> USER-GUIDE §2에 해당. 목표: PO가 백지에서 시작하지 않도록 틀을 못 박는다.

### 2-1. DS 투입 — shadcn-vue ([경로 A 수동], `project-design-guide.md` 절차의 Vue 적응)

이 프로젝트는 [`packages/plugin-prerequisite/docs/project-design-guide.md`](packages/plugin-prerequisite/docs/project-design-guide.md)를 따라 **shadcn/ui 방식**으로 DS를 세팅한다. 단, 스택이 Vue이므로 React용 명령을 **shadcn-vue**용으로 바꾼다. 핵심 원칙(컴포넌트 소스를 내 레포로 *복사*해 소유 → DS 폐쇄가 저절로 성립)은 동일하다.

```bash
cd foundation/design-system
npm create vite@latest ds-source -- --template vue-ts
cd ds-source
npm install
npm install tailwindcss @tailwindcss/vite      # Tailwind v4
npx shadcn-vue@latest init                      # components.json + design token(CSS 변수) + lib/utils
```

`vite.config.ts`에 `@vitejs/plugin-vue` + `@tailwindcss/vite` + `@` alias 등록(가이드 §4와 동일, plugin-react만 plugin-vue로). 쓸 컴포넌트를 골라 가져온다(닫힌 집합 결정):

```bash
npx shadcn-vue@latest add button input select textarea label card badge
npx shadcn-vue@latest add tabs switch skeleton avatar dropdown-menu separator form
```

> 📌 `ds-source/`는 **동작하는 앱이 아니라 DS 소스를 담고 목록화할 그릇**이다(가이드 §3). 실제 구현은 ③(`app_repo/frontend`)에서 한다. `main.ts`/`App.vue`/`index.html`는 남기지 않는다.

#### 합성(custom) 컴포넌트 — shadcn 단품에 없는 것 (가이드 §6)

DevLog는 shadcn 기본 세트에 없는 부품이 몇 개 필요하다. 이는 **여러 부품을 조합한 합성 컴포넌트**로 직접 만들어 `src/components/ui/`에 두고 ds-allowlist.md에 똑같이 등록한다(이게 정상 절차 — 화면에서 임의 발명은 금지).

| 합성 컴포넌트 | 구성 | 쓰임(SFR) |
|---|---|---|
| `Header` | 브랜드 + `NavMenu` + 테마토글 + auth actions | SIR-002 |
| `PostCard` | `Card`+`Badge`+좋아요 `Button` | SFR-001/009 |
| `FilterBar` | `Input`(검색)+태그 `Button` 그룹+`Select`(정렬) | SFR-002/003/004 |
| `PomodoroTimer` | 원형 게이지(SVG) + 시작/정지/초기화 `Button` | SFR-006 |
| `ContributionGraph` | 26×7 격자 + 색강도 + hover 툴팁 (잔디밭) | SFR-010 |
| `WeeklyChart` | Chart.js(vue-chartjs) 막대 차트 래퍼 | SFR-010 |
| `StatCard` | `Card` 기반 통계 카드 | SFR-010 |

> `PomodoroTimer`·`ContributionGraph`처럼 표준 라이브러리에 없는 시각화는 **내가 소유하는 합성 컴포넌트**로 만들어 DS에 등록하는 것이 가이드 §6의 정식 방법이다. 화면(②)에서는 이 ref만 쓴다.

### 2-2. 허용집합 작성 — `ds-allowlist.md`

가져온 단품 + 합성 컴포넌트를 하니스 계약으로 적는다(가이드 §7 형식 strict). 발췌:

```markdown
# DS Allowlist — 허용 컴포넌트 집합 (가드레일)

## Button
- **description**: 액션을 실행하는 기본 버튼
- **props**: label: string, variant: default|secondary|ghost|outline, size: default|sm|lg|icon, disabled: boolean

## PostCard
- **description**: 글 1건을 카드로 표시 (태그·읽기시간·제목·요약·작성자·날짜·좋아요)
- **props**: post: object, liked: boolean, likeCount: number

## PomodoroTimer
- **description**: 25분 포모도로 원형 타이머 (시작/정지/초기화, RECORDING/STANDBY)
- **props**: targetSeconds: number, status: string, elapsed: number

## ContributionGraph
- **description**: 26주×7일 학습 잔디밭. 일별 학습량을 5단계 색강도로 표현
- **props**: cells: array, levelOf: function
```

→ 저장 시 `ds-guide-validate.py` 훅이 형식 검증. **이제 PO는 이 목록 밖 컴포넌트를 쓸 수 없다(DS 폐쇄).**

> 💡 오픈소스 DS를 *이름만으로* 자동 부트스트랩하고 싶으면 [경로 B] `ds-bootstrap` 스킬(*"shadcn-vue로 ds-source 세팅해줘"*)로 설치·`tokens.css`·`ds-allowlist.md`를 한 번에 생성할 수도 있다(USER-GUIDE §2 참조). 이 예제는 가이드 학습을 위해 [경로 A 수동]으로 보인다.

### 2-3. design page 생성 — `design-page-builder`

DevLog 화면은 모두 공통 Header(SIR-002) + content 한 벌이다. DP 2종을 만든다:

- **DP-MAIN** — Header(`locked`: 로고·"DevLog"·테마토글·auth actions) + content(`editable`, 12-col grid) + Footer(`locked`). 메인·상세·작성·로그인·대시보드의 바탕.
- **DP-POPUP** — 모달 컨테이너(DoD 최소 세트). DevLog 본 스펙엔 모달이 없어 화면에는 안 쓰이지만, foundation DoD(DP-MAIN+DP-POPUP)를 충족하고 향후 확장(삭제 확인 등)에 대비해 만들어 둔다.

### 2-4. DS 카탈로그 렌더 + 2-5. 결정·명세 확정

- `foundation/design-system/catalog/index.html` 렌더 — PO가 "여기에 `PostCard`를, 강조색은 `color-cyan-400`"처럼 **이름으로 지시**할 근거.
- `decisions/tech-stack.md` — **프론트 Vue 3+Vite+TS+Tailwind+shadcn-vue / 백엔드 Spring Boot 3(Java 21)+JPA / DB PostgreSQL 17 / 마이그레이션 Flyway / 차트 Chart.js / 테스트 Vitest+Vue Test Utils·JUnit5·Playwright**.
- `decisions/ops-stack.md` — GitHub + GitHub Actions + Docker(백엔드 jar) + nginx(프론트 정적) + 사내망. (원본의 PM2/Standalone는 이 스택에선 jar+Docker로 대체 — [부록 B](#부록-b--스택-전환으로-재해석된-요구사항).)
- **`platform-baseline/SPEC-000.md`** — 공통 기능 명세: **데모 계정 로그인(alice/bob/kim) / JWT 세션 / 보호 라우트(`/write`,`/dashboard`) 다층 방어 / RBAC(본인 데이터만) / 공통 Header(테마 토글·로그아웃) / 다크기본 테마+localStorage 영속**. ← SFR-007·011·012, SER-001, SIR-002가 여기로 들어간다(명세까지만, 코드는 ③).
- `SPEC-OPS-000.md` — 빌드(프론트 정적+백 jar)·배포(Docker, 사내망)·CI/CD·관측성 명세. SER-002(환경변수 분리)·COR-003/004/005가 여기로.

✅ DoD: ds-allowlist + DP-MAIN/DP-POPUP + 카탈로그 + SPEC-000(로그인·테마 포함)·OPS 명세 + tech/ops-stack + VERSION.

---

## 3. ② 화면 정의 — PO (화면마다 반복)

> USER-GUIDE §3에 해당. 코드 한 줄 없이 화면 5개를 계약으로 확정한다. 각 화면은 **Stage 0 → 1 → 2 → (2.5) → 3 → 4 → Gate A** 를 거친다.

### 3-1. 메인 — `SCR-BLOG-LIST` (글 목록 + 검색/필터/정렬 + 좋아요 + 타이머)

**Stage 0 인스턴스화**: DP-MAIN 선택 → 이름 "메인", 도메인 `BLOG`, 타입 `LIST` → `SCR-BLOG-LIST` 채번. Header/Footer 고정영역 상속, content 캔버스는 빈 상태.

**Stage 1 레이아웃**: *"상단에 포모도로 타이머, 그 아래 검색+태그필터+정렬 바, 그 아래 글 카드 목록"*.

```yaml
# SCR-BLOG-LIST.yaml (발췌)
screen: { id: SCR-BLOG-LIST, name: "메인", archetype: list, from_template: { page: DP-MAIN, version: 1 } }
layout:
  - { id: CMP-BLOG-LIST.timer,  source: { kind: ds, ref: PomodoroTimer },
      position: { slot: content, base: { col_start: 1, col_span: full, row: 1 } }, meta: { interactive: true } }
  - { id: CMP-BLOG-LIST.filterbar, source: { kind: ds, ref: FilterBar },
      position: { slot: content, base: { col_start: 1, col_span: full, row: 2 } }, meta: { interactive: true } }
  - { id: CMP-BLOG-LIST.cardlist, source: { kind: ds, ref: PostCard },   # 반복 렌더
      position: { slot: content, base: { col_start: 1, col_span: full, row: 3 } },
      meta: { interactive: true }, reactive: { requery_on: [CMP-BLOG-LIST.filterbar] } }
```
저장 → schema 검증 → L1(DS폐쇄)·L5(canvas-bounds) 통과 → `render_screen` HTML 렌더 → `layout_confirmed`.

**Stage 2 액션 인터뷰**:
```yaml
actions:
  - id: REQ-BLOG-LIST.001                 # 검색 (클라 디바운스)
    component: CMP-BLOG-LIST.filterbar
    trigger: change
    outcome: { type: query, target: ENT-POST }
    acceptance:
      - "Given 글 목록 화면, When 검색어를 입력하면, Then 300ms 디바운스 후 제목·요약을 대소문자 무관 필터링한다(서버 재요청 없음)"
      - "Given 검색 결과 0건, When 필터가 비면, Then 빈 상태 안내 UI를 표시한다"
  - id: REQ-BLOG-LIST.002                 # 태그 필터 + 정렬 (동시 적용)
    component: CMP-BLOG-LIST.filterbar
    trigger: click
    outcome: { type: query, target: ENT-POST }
    acceptance:
      - "Given 태그 버튼 그룹, When 태그를 고르면, Then 그 태그 글만 보이고 선택 태그가 강조된다"
      - "Given 검색+태그+정렬, When 셋을 동시에 적용하면, Then 모든 조건이 함께 반영된다"
  - id: REQ-BLOG-LIST.003                 # 카드 클릭 → 상세 이동
    component: CMP-BLOG-LIST.cardlist
    trigger: rowClick
    outcome: { type: navigate, target: SCR-BLOG-DETAIL }
    acceptance:
      - "Given 글 카드, When 본문 영역을 클릭하면, Then 그 글의 상세 화면으로 이동한다"
  - id: REQ-BLOG-LIST.004                 # 좋아요 토글 (클라 전용)
    component: CMP-BLOG-LIST.cardlist
    trigger: click
    outcome: { type: noop }               # 영구 저장 안 함(의도된 단순화)
    acceptance:
      - "Given 글 카드의 ♡, When 클릭하면, Then ♥로 토글되고 카운트가 ±1되며 상세 이동은 발생하지 않는다(이벤트 전파 차단)"
      - "Given 정렬을 바꿔도, When 같은 글이면, Then 좋아요 상태가 글 ID 기준으로 따라간다(위치 기준 아님)"
  - id: REQ-BLOG-LIST.005                 # 타이머 정지 → 학습 로그 저장
    component: CMP-BLOG-LIST.timer
    trigger: click
    outcome: { type: mutate, target: ENT-STUDY-LOG }
    permission: login                     # 로그인 필요 (비로그인은 저장 안 함)
    acceptance:
      - "Given 로그인 + 1분 이상 학습, When 정지를 누르면, Then 학습 로그 1건이 저장되고 '✓ N분 학습 기록됨'을 표시한다"
      - "Given 비로그인, When 타이머를 써도, Then 저장하지 않고 안내 메시지를 표시한다"
```

**Stage 2.5 데이터 계약**: `query/mutate ENT-POST`, `mutate ENT-STUDY-LOG` →
```yaml
# ENT-POST.yaml — entity-intake (개념 계약, 물리 타입 없음)
entity: { id: ENT-POST, name: "글" }
attributes:
  - { name: slug,        meaning: "URL 식별자(제목에서 생성, 유일)" }
  - { name: title,       meaning: "글 제목" }
  - { name: author,      meaning: "작성자 이름(로그인 사용자)" }
  - { name: date,        meaning: "작성일 YYYY-MM-DD" }
  - { name: tag,         meaning: "분류 태그(단일)" }
  - { name: excerpt,     meaning: "한 줄 요약(본문 첫 100자)" }
  - { name: content,     meaning: "본문 전체" }
  - { name: reading_time,meaning: "읽기 예상 시간(분, 본문 길이 기반)" }
  - { name: cover_image, meaning: "커버 이미지 URL(선택, 외부 정적 URL)" }
relations:
  - { to: ENT-USER, kind: belongs_to, meaning: "글은 한 작성자에 귀속" }

# ENT-STUDY-LOG.yaml
entity: { id: ENT-STUDY-LOG, name: "학습 로그" }
attributes:
  - { name: started_at,       meaning: "학습 시작 시각(KST 기준)" }
  - { name: duration_seconds, meaning: "학습 시간(초)" }
relations:
  - { to: ENT-USER, kind: belongs_to, meaning: "로그는 한 사용자에 귀속(본인 것만 조회)" }
```
> ENT-USER는 인증 도메인(SPEC-000)이 소유한다. ②는 `belongs_to` 참조만 하고 속성(권한·계정)은 baseline이 정의한다.

**Stage 3 노트** (verbatim, AI 수정 금지):
> "타이머 시간은 한국 표준시(UTC+9) 기준. DB timestamp와 프론트 표시 형식이 일치하는지 반드시 검증해야 함."

→ AI가 `complexity: med` 태그 제안(타임존 정합). **Stage 4 → Gate A** → `confirmed`.

### 3-2. 글 상세 — `SCR-BLOG-DETAIL`

**Stage 0**: DP-MAIN 인스턴스화 → `SCR-BLOG-DETAIL` (archetype: detail).

**Stage 1**: 뒤로가기 링크 + (선택)커버 + 태그·읽기시간 + 제목 + 작성자·날짜 + 본문 + `Skeleton`(로딩).

**Stage 2 액션 인터뷰**:
```yaml
actions:
  - id: REQ-BLOG-DETAIL.001               # 글 단건 조회
    component: CMP-BLOG-DETAIL.body
    trigger: load
    outcome: { type: query, target: ENT-POST }
    acceptance:
      - "Given /posts/{slug} 진입, When 로딩 중이면, Then 스켈레톤 UI를 표시한다(스피너 금지)"
      - "Given 존재하지 않는 slug, When 접근하면, Then 404 화면을 표시한다"
      - "Given 조회 에러, When 발생하면, Then 친근한 에러 UI + '다시 시도'/'목록으로' 버튼을 표시한다"
  - id: REQ-BLOG-DETAIL.002               # 목록으로
    component: CMP-BLOG-DETAIL.backlink
    trigger: click
    outcome: { type: navigate, target: SCR-BLOG-LIST }
    acceptance:
      - "Given 상세 화면, When '← 목록으로'를 누르면, Then 메인으로 이동한다"
```
`ENT-POST` 재사용(이미 정의됨). **Gate A** → `confirmed`.

### 3-3. 글 작성 — `SCR-BLOG-WRITE`

**Stage 0**: DP-MAIN 인스턴스화 → `SCR-BLOG-WRITE` (archetype: form). `screen.permission: login` (보호 라우트).

**Stage 1**: `Input`(제목) + `Select`(태그) + `Textarea`(본문) + `Button`(발행/취소).

**Stage 2 액션 인터뷰**:
```yaml
actions:
  - id: REQ-BLOG-WRITE.001                # 글 발행
    component: CMP-BLOG-WRITE.submitBtn
    trigger: submit
    outcome: { type: mutate, target: ENT-POST }
    permission: login
    acceptance:
      - "Given 로그인 사용자가 제목·태그·본문을 채우고, When 발행을 누르면, Then 글이 저장되고 상세로 이동하며 메인 목록에 즉시 반영된다"
      - "Given 제출 중, When 대기하면, Then 버튼이 비활성화되고 '저장 중...'을 표시한다"
      - "Given 비로그인 사용자가 /write에 직접 접근하면, When 진입 시, Then callbackUrl을 붙여 로그인으로 리다이렉트한다"
```

**Stage 3 노트** (verbatim):
> "slug는 제목에서 자동 생성(소문자·공백→하이픈·특수문자 제거). 읽기시간은 약 500자당 1분, excerpt는 본문 첫 100자. 작성자=로그인 이름, 날짜=오늘."

→ AI가 `complexity: med` 태그 제안(slug·파생필드 생성 규칙). **Gate A** → `confirmed`.

### 3-4. 로그인 — `SCR-AUTH-LOGIN`

**Stage 0**: DP-MAIN 인스턴스화 → `SCR-AUTH-LOGIN`.

**Stage 1**: 가운데 `Card` 안에 `Input`(아이디)+`Input`(비밀번호)+`Button`(로그인) + 데모 계정 안내 박스.

**Stage 2 액션 인터뷰**:
```yaml
actions:
  - id: REQ-AUTH-LOGIN.001
    component: CMP-AUTH-LOGIN.submitBtn
    trigger: submit
    outcome: { type: navigate, target: SCR-BLOG-LIST }   # 성공 시 메인(또는 callbackUrl)
    acceptance:
      - "Given 데모 계정(alice/bob/kim) 입력, When 로그인하면, Then 인증 후 callbackUrl 또는 메인으로 이동한다"
      - "Given 잘못된 자격증명, When 로그인하면, Then '아이디 또는 비밀번호가 올바르지 않습니다'를 표시한다"
```

> ⚠️ **여기서 멈춤.** 인증 성공 후의 JWT 발급·세션·보호 라우트·RBAC는 PO가 정의하지 **않는다** — SPEC-000 공통 기능이다. PO는 "폼 → 로그인 → 메인" 이라는 *화면 계약*까지만. 토큰·세션·다층 방어는 ③ Phase 0(모드 B)가 책임진다. (계산기 예제와 달리 **외부 SSO가 없어 EXT- 계약이 없다.**)

**Gate A** → `confirmed`.

### 3-5. 개인 대시보드 — `SCR-STUDY-DASHBOARD`

**Stage 0**: DP-MAIN 인스턴스화 → `SCR-STUDY-DASHBOARD`. `screen.permission: login` (본인만).

**Stage 1**: `StatCard`×3(누적/이번주/streak) + `ContributionGraph`(잔디밭) + `WeeklyChart`(주간 막대).

**Stage 2 액션 인터뷰**:
```yaml
actions:
  - id: REQ-STUDY-DASHBOARD.001           # 통계 조회
    component: CMP-STUDY-DASHBOARD.stats
    trigger: load
    outcome: { type: query, target: ENT-STUDY-LOG }
    permission: login
    acceptance:
      - "Given 로그인 사용자, When 대시보드 진입 시, Then 누적·이번주 학습시간과 연속 학습일(streak)을 카드로 보여준다"
      - "Given 다른 사용자의 데이터, When 접근하면, Then 보이지 않는다(본인 데이터만 — RBAC)"
      - "Given 비로그인, When /dashboard 접근하면, Then 로그인으로 리다이렉트한다"
  - id: REQ-STUDY-DASHBOARD.002           # 잔디밭/주간차트
    component: CMP-STUDY-DASHBOARD.graph
    trigger: load
    outcome: { type: query, target: ENT-STUDY-LOG }
    permission: login
    acceptance:
      - "Given 학습 로그, When 잔디밭을 그리면, Then 26주×7일 격자에 일별 학습량을 5단계 색강도로 표시하고 hover 시 'YYYY-MM-DD — N분 학습'을 보여준다"
      - "Given 최근 7일, When 주간 차트를 그리면, Then 일별 학습시간을 막대로 표시하고 데이터 없는 날도 0 막대로 표시한다"
```

**Stage 3 노트** (verbatim, AI 수정 금지):
> "잔디밭 활동량→색강도 5단계: 0분=회색, ~30분=매우흐린시안, 30분~1h=흐린시안, 1~2h=중간시안, 2h+=진한시안. streak는 오늘부터 거꾸로 연속 학습한 일수. 마지막 칸=이번 주 토요일. 미래 날짜는 opacity 낮춤. 모든 날짜 키는 로컬(KST) YYYY-MM-DD로 일관 생성."

→ AI가 `complexity: high` 태그 제안(날짜 버킷팅·streak 연속일 계산·색강도 매핑). **이 노트가 ③ speckit-plan에서 `bl-analyst` 서브에이전트를 부른다.**

**Stage 4 → Gate A** → `confirmed`.

### 3-6. 여정(JRN) — 5개 화면이 모두 confirmed 된 후 (횡단)

`journey-map` 스킬이 전 화면의 navigate/mutate action을 집계:
```yaml
JRN-BROWSE-READ:  SCR-BLOG-LIST → REQ-BLOG-LIST.001/002(검색·필터) → REQ-BLOG-LIST.003 → SCR-BLOG-DETAIL
JRN-WRITE-POST:   SCR-AUTH-LOGIN → (인증) → SCR-BLOG-WRITE → REQ-BLOG-WRITE.001 → SCR-BLOG-DETAIL
JRN-STUDY-TRACK:  SCR-BLOG-LIST → REQ-BLOG-LIST.005(타이머 저장) → SCR-STUDY-DASHBOARD → REQ-STUDY-DASHBOARD.001/002
```
→ 고립 화면 없음. 이 3개 여정이 ③ Phase γ의 Playwright E2E 출처가 된다.

### 3-7. 발행 — PACK 분해

`spec-generator`가 confirmed 화면을 **엔티티 응집** 기준으로 도메인 팩으로 묶는다:

| PACK | 묶이는 화면 | 핵심 엔티티 | 비고 |
|---|---|---|---|
| **PACK-BLOG** | SCR-BLOG-LIST + SCR-BLOG-DETAIL + SCR-BLOG-WRITE | ENT-POST | 셋 다 글을 읽고/쓰고/조회 → 한 팩 |
| **PACK-STUDY** | SCR-STUDY-DASHBOARD + 타이머 컴포넌트(SCR-BLOG-LIST 위) | ENT-STUDY-LOG | 학습 도메인. 타이머는 메인 화면에 있지만 학습 로그를 쓰므로 이 팩 소속 |
| *(로그인)* | SCR-AUTH-LOGIN | — | **팩 아님.** SPEC-000 공통기능 → ③ Phase 0 |

> **한 화면이 여러 팩에 걸친다:** SCR-BLOG-LIST는 글 카드(PACK-BLOG)와 타이머(PACK-STUDY)를 함께 갖는다. Phase α가 화면 shell 전체를 한 번에 만들고, 각 팩은 자기 컴포넌트의 wiring만 추가한다(Phase α가 선행하는 이유).

발행 전 `spec-pack-guard.py`가 confirmed 여부·ENT 참조 무결성·`layout_hash`/`render_hash` 핀을 검증·기록 → `model_repo/specs/PACK-BLOG/`, `PACK-STUDY/` 발행 → ③ 인계.

---

## 4. ③ 구현 — 개발자 (4 Phase)

> USER-GUIDE §4에 해당. `projects/devlog/app_repo/`에서 작업. 스택은 ①의 tech-stack.md(**Vue + Spring Boot**)에서 파생된다.

### 부트스트랩 (1회)
```bash
bash packages/plugin-ai-web-dev/hooks/install-speckit.sh   # .specify vendoring + git 훅 설치
```

### Phase 0 — Baseline (여기서 로그인·테마가 실제로 구현된다)

SPEC-000을 받아 공통 기능별 전달 모드 결정 → `baseline-delivery-manifest.yaml`:

| 공통 기능 | 모드 | 사유 |
|---|---|---|
| 데모 계정 로그인 / JWT 세션 | **B (직접 주입)** | 변형 불필요 — Spring Security + JWT 필터 완성 코드+테스트로 주입(데모 계정 alice/bob/kim 하드코딩, 주석에 운영 시 bcrypt 필수 명시) |
| 보호 라우트 다층 방어 | **B** | 표준 — Spring Security `SecurityFilterChain`(서버) + Vue 라우터 가드(클라). 비로그인 → `/login?callbackUrl=` |
| RBAC (본인 데이터만) | **A (가이드)** | 도메인마다 조건이 다름 → `baseline-guides/`로. Phase β가 "study_logs는 user_id=본인" 필터에 적용 |
| 공통 Header(테마토글·로그아웃·스켈레톤) | **A** | 화면마다 약간 다름 → `baseline-guides/` |
| 다크 기본 테마 + localStorage 영속 | **A** | Tailwind `dark` class 토글 패턴 가이드 |

> → `SCR-AUTH-LOGIN` 화면은 Phase α에서 shell이 생기고, **JWT 인증 흐름은 Phase 0(모드 B) Spring Security 코드가 연결**한다. *PO 계약(REQ-AUTH-LOGIN.001)은 "폼→로그인→메인"의 acceptance로만 쓰이고, 토큰 검증·세션은 baseline 테스트가 책임진다.*
>
> 운영 요건(SPEC-OPS-000): 환경변수 분리(`.env`/`.env.example`, SER-002)·Docker 빌드·CI는 대개 **모드 B**, 사내망 배포 타깃 차이는 **모드 A** 가이드. (원본의 Standalone/PM2는 이 스택에선 jar+Docker — [부록 B](#부록-b--스택-전환으로-재해석된-요구사항).)

### Phase α — Layout Scaffold (전체 화면 1회)
```
/speckit-scaffold      # SCR-BLOG-LIST, -DETAIL, -WRITE, SCR-AUTH-LOGIN, SCR-STUDY-DASHBOARD → Vue shell 일괄
```
①의 tech-stack.md `frontend.framework: vue`이므로 scaffold는 `.vue` 파일 + `src/pages`(또는 라우트) 구조로 투영한다. `layout-hash-guard`가 5개 화면을 ②와 동일 엔진으로 재렌더 → `layout_hash` 일치 확인. 불일치 시 빌드 차단(②확정 위치를 ③이 못 바꿈). 앱을 띄우면 5개 화면이 데이터 없이 layout만으로 보인다(walking skeleton).

### Phase β — Spec Pack Iteration (팩마다)

**PACK-BLOG 차례:**
```
/speckit-specify   # PACK-BLOG scope 확인 (SCR-BLOG-LIST/DETAIL/WRITE, ENT-POST)
/speckit-plan      # ENT-POST → JPA 엔티티 + posts 테이블(Flyway 마이그레이션) + 인덱스(slug UNIQUE)
                   #   API(Spring REST): GET /api/posts(목록), GET /api/posts/{slug}(상세), POST /api/posts(발행)
                   #   프론트 wiring: 검색/태그/정렬/좋아요는 클라 측(Vue computed/composable), 디바운스 300ms
                   #   ★ complexity:med 노트(slug·읽기시간·excerpt 파생) → 파생 규칙 명세
/speckit-tasks     # T001 PostEntity 테스트 → T002 구현 → T003 글 발행 API 테스트 → … (test-first, [P] 병렬)
   ── Gate B: Data Model·ERD·Task 확정, bl 미해결 0, 개발자 approve ──
/speckit-implement # test-author가 REQ-BLOG-* acceptance → 실패 테스트 먼저 (API: JUnit5 / 화면: Vitest+Vue Test Utils)
                   #   red → green → refactor. tdd-gate·commit-spine-id 강제
                   #   commit: [PACK-BLOG/T002] Post 엔티티 구현 (REQ-BLOG-WRITE.001)
   → code-reviewer subagent 검토 (DS 폐쇄·임의 스타일·보안·스파인 ID)
```

**PACK-STUDY 차례:**
```
/speckit-plan      # ENT-STUDY-LOG → study_logs 테이블 + user_id 인덱스
                   #   API: POST /api/study-logs(기록), GET /api/study-logs/stats(대시보드 집계)
                   #   ★ complexity:high 노트(잔디밭 색강도·streak 연속일·날짜 버킷팅) → bl-analyst 호출
                   #     → decision table(활동량→5단계 색) / streak 알고리즘 / worked examples 산출
                   #   ★ complexity:med 노트(KST 타임존 정합) → started_at 저장/표시 형식 통일·검증
/speckit-tasks     # T001 streak 계산기 테스트 → T002 구현 → T003 stats API 테스트 → 잔디밭/주간차트 컴포넌트 테스트 …
   ── Gate B: BL(streak·색강도) 확정, bl-analyst 미해결 0 ──
/speckit-implement # 타이머 저장(REQ-BLOG-LIST.005)·대시보드 집계(REQ-STUDY-DASHBOARD.001/002)
                   #   RBAC "본인 것만"은 Phase 0 모드 A 가이드(baseline-guides/) 로드해 user_id 필터 적용
```

### Phase γ — Integration & NFR (배포 전)
```
JRN-BROWSE-READ → e2e/browse-read.spec.ts     (검색·필터 → 상세 진입)
JRN-WRITE-POST  → e2e/write-post.spec.ts       (로그인 → 작성 → 목록 즉시 반영)
JRN-STUDY-TRACK → e2e/study-track.spec.ts      (타이머 저장 → 대시보드 잔디밭/통계 증가)
   commit: [E2E/JRN-STUDY-TRACK] ...
```
각 step은 화면 action의 acceptance(Gherkin)를 **재사용**(새 시나리오 발명 금지). + NFR(검색 디바운스·동시 접속·입력 검증 SER-003·에러 메시지 안전성 SER-004) + 관측성 + 배포(ops-stack.md, Docker). Next.js 고유 NFR의 재해석은 [부록 B](#부록-b--스택-전환으로-재해석된-요구사항).

---

## 5. 계약이 바뀌면 — Change Order 예시

> USER-GUIDE §5에 해당.

**상황:** 개발 도중 PO가 *"글에 댓글 기능을 추가하고 싶다"* 고 함.

```
③ 개발자: 새 ENT-COMMENT + SCR-BLOG-DETAIL에 댓글 영역 추가 요청 → diff + blast radius 계산
   - 새 엔티티 + 화면 layout 변경 + REQ 추가 → 중대 변경 (게다가 COR-002에서 댓글은 원래 비-목표였음)
   → 판정: regenerate
② PO: 기존 Gate A 흐름으로 SCR-BLOG-DETAIL 재확정 + ENT-COMMENT 계약 정의
   → spec-generator가 PACK-BLOG 만 버전 +1 재발행 (re-pin)
③ 개발자: 새 Gate B → 댓글 테스트 추가(기존 테스트 깨짐 = TDD 백스톱) → 재구현
```

반대로 *"카드 강조색만 시안→라임으로"* 같은 외관 변경이면 → `dismiss` 후 re-pin (재구현 없음).

핵심: **재정의는 항상 ②로 돌아간다.** ③는 판정만, 새 계약은 만들지 않는다.

---

## 6. 이 앱의 최종 추적 그래프

```
①  SPEC-000(로그인/JWT/RBAC/공통레이아웃/테마) ───→ ③ Phase 0 (모드 B 인증 + 모드 A 가이드)
    SPEC-OPS-000(빌드·배포·관측성) ─────────────────→ ③ Phase 0·γ (Docker·CI)
    DP-MAIN, DP-POPUP
②  DP-MAIN → SCR-BLOG-LIST   → REQ-BLOG-LIST.001~004 → ENT-POST ┐
                             → REQ-BLOG-LIST.005      → ENT-STUDY-LOG ┐
            → SCR-BLOG-DETAIL → REQ-BLOG-DETAIL.001/002 → ENT-POST   ├→ PACK-BLOG
            → SCR-BLOG-WRITE  → REQ-BLOG-WRITE.001     → ENT-POST   ┘
            → SCR-STUDY-DASHBOARD → REQ-STUDY-DASHBOARD.001/002 → ENT-STUDY-LOG ─→ PACK-STUDY
    DP-MAIN → SCR-AUTH-LOGIN → REQ-AUTH-LOGIN.001     (팩 아님 → SPEC-000)
    JRN-BROWSE-READ / JRN-WRITE-POST / JRN-STUDY-TRACK
③  PACK-BLOG  → spec.md → T001…(Post API·검색/필터·작성) → test → [PACK-BLOG/T…] commit
    PACK-STUDY → spec.md → T001…(streak·잔디밭·타이머 저장·집계 API) → test → [PACK-STUDY/T…] commit
    JRN-* → Playwright e2e → [E2E/JRN-*] commit
                                          ↓
                              app_repo (Vue 정적 + Spring Boot jar, Docker 배포)
```

글 한 줄, 잔디밭 한 칸까지도 **SPEC-000(①) 또는 SCR-/REQ-/PACK-(②)** 에서 왔는지, 그리고 어느 task·test·commit이 그것을 구현했는지 끝까지 역추적된다.

---

## 부록 A — 이 예제가 보여주는 6가지 교훈

1. **로그인 = 공통 기능.** 외부 SSO든 내부 데모 계정이든, 인증 로직은 PO가 계약하지 않는다. ①이 SPEC-000으로 명세하고 ③ Phase 0(모드 B)가 구현한다. (계산기 예제는 외부 SSO라 `EXT-SSO`가 있었지만, DevLog는 내부 인증이라 **EXT 계약이 없다** — 외부 연동 유무가 차이.)
2. **DP 인스턴스화.** 5개 화면 모두 DP-MAIN에서 시작해 Header/Footer 고정영역을 상속하고 캔버스에만 작업한다 — 백지에서 시작하지 않는다.
3. **엔티티 응집으로 팩을 자른다.** 글 목록·상세·작성은 모두 `ENT-POST`를 다루므로 한 팩(PACK-BLOG). 대시보드와 타이머는 `ENT-STUDY-LOG`로 묶여 PACK-STUDY.
4. **복잡 노트가 bl-analyst를 부른다.** "잔디밭 색강도 5단계·streak 연속일"이라는 PO 노트(complexity:high)가 ③에서 결정 테이블·worked example을 만들어 TDD 입력이 된다.
5. **여정이 E2E가 된다.** PO가 화면을 잇는 navigate를 정의하면(JRN-*), ③는 그것을 Playwright로 *구현*만 한다.
6. **스택은 ①의 결정이다.** 화면 model은 프레임워크 중립이라, 같은 SCR-*.yaml이 Next.js든 Vue든 그대로 쓰인다. 스택을 Vue+Spring Boot로 바꿔도 ②의 계약은 한 글자도 안 바뀌고, ③의 scaffold/plan/구현만 그 스택으로 투영된다(부록 B).

---

## 부록 B — 스택 전환으로 재해석된 요구사항

원본 `DevLog_raw.md`는 Next.js 풀스택 전제라 일부 요구사항이 **프레임워크 관용구**다. 하니스는 *무엇을(what)* 과 *어떻게(how)* 를 분리하므로, 스택을 Vue+Spring Boot로 바꾸면 이들은 아래처럼 재배치/재해석된다. **PO 화면 계약(②)은 영향받지 않는다** — 전부 ①(결정·명세) 또는 ③(구현)의 몫이다.

| 원본(Next.js) 요구사항 | 성격 | Vue + Spring Boot 재해석 | 귀속 |
|---|---|---|---|
| Server Actions / API 라우트 최소화 (COR-001) | 구현 패턴 | Spring Boot **REST 컨트롤러** + Vue `fetch`/composable | ③ |
| App Router·Server Components (COR-001) | 구현 패턴 | Vue Router + SFC(컴포넌트) | ③ |
| `loading.tsx` 스켈레톤 컨벤션 (PER-002, QAR-003) | 구현 패턴 | Vue **`<Suspense>` + Skeleton 컴포넌트** | ③ |
| `error.tsx`/`notFound()` (QAR-003) | 구현 패턴 | Vue Router 404 라우트 + 에러 바운더리 컴포넌트 | ③ |
| 메인 SSR/LCP 1초·크롤러 빈 HTML 방지 (PER-001) | 결정+구현 | Vue는 기본 SPA → **선택지: ① SPA+스켈레톤으로 LCP 관리, ② SEO 진짜 필요하면 Nuxt(SSR) 채택을 tech-stack에서 결정**. 사내망·로그인 앱이라 보통 ①로 충분 | ① 결정 / ③ |
| Hydration mismatch 방지 (QAR-005) | 구현 패턴 | SPA에선 SSR hydration 이슈 자체가 거의 없음. **단 KST 타임존 날짜 키 일관성(잔디밭)은 그대로 유효** → PACK-STUDY 노트로 유지 | ③ |
| TypeScript strict / ESLint 0 (QAR-001) | 품질 게이트 | 프론트 Vue+TS strict·ESLint 유지 / 백엔드는 **Checkstyle·SpotBugs** 등가물 | ① constitution / ③ |
| Standalone 빌드 `output: standalone` (COR-003) | 배포 | 프론트 **Vite 정적 빌드(dist)** + 백엔드 **Spring Boot fat jar** | SPEC-OPS-000 |
| PM2 무중단·로그 회전 (COR-004) | 배포 | **Docker 컨테이너**(백 jar) + nginx(프론트) + 로그 드라이버. 무중단은 컨테이너 롤링 | SPEC-OPS-000 |
| npm scripts(`db:push`/`db:generate`/`seed`) (COR-005) | 도구 | **Flyway 마이그레이션**(`flyway migrate`) + 시드 SQL/CommandLineRunner. 프론트 npm script는 유지 | SPEC-OPS-000 / ③ |
| Drizzle ORM (기술스택) | 구현 | **Spring Data JPA + Flyway** | ① tech-stack |
| NextAuth(JWT, Credentials) (SFR-007) | 공통기능 | **Spring Security + JWT 필터** (데모 계정) | SPEC-000 → ③ Phase 0 |
| Recharts (주간 차트) | 구현 | **Chart.js (vue-chartjs)** — DS 합성 컴포넌트 `WeeklyChart`로 래핑 | ① DS / ③ |
| 좋아요 클라 전용·영구저장 안 함 (SFR-009, COR-002) | 계약 | 스택 무관 — `outcome: noop`으로 ②에서 그대로 유지 | ② (불변) |

> **개선 제안(검토 필요):**
> - 원본 SRS 본문에는 "Next.js·NextAuth·Drizzle·PM2"가 **요구사항 ID 안에 하드코딩**돼 있다(COR-001/003/004/005, SFR-007). 하니스 원칙(원칙 8: 스택은 tech-stack.md 단일 출처)대로라면 이들은 *기술 중립적 요구*("무중단 배포가 가능해야 한다")로 다시 쓰고, 구체 도구는 `tech-stack.md`/`ops-stack.md`로 내려야 깔끔하다. 이 예제 문서는 그 분리를 적용한 결과다.
> - 원본 PER-001(SSR로 SEO 보장)은 Vue SPA 기본 가정과 충돌한다. **SEO가 실제 요건이면 Nuxt(SSR) 채택을 ①에서 결정**해야 하고, 단순 사내 로그인 앱이면 SPA+스켈레톤으로 충분하다 — 이 결정은 PO가 아니라 개발 리드(①)가 SPEC/tech-stack에서 내린다.
