# 튜토리얼 — ③ `plugin-ai-web-dev`로 DevLog 구현하기

> **목적:** 이 프로젝트(`projects/devlog_dev_plugin`)는 ③ **AI-WEB-DEV 플러그인을 테스트**하기 위한 샘플이다.
> ①(foundation)·②(model_repo) 산출물이 **이미 준비**되어 있어, 당신은 **③를 사용하는 단계에서 바로 시작**할 수 있다.
> 원천 명세: 리포 루트 `DevLog_raw.md` (DevLog SRS — 학습 트래커 + 미니 블로그, Next.js).

---

## 0. 이 픽스처에 무엇이 준비돼 있나

③를 시작하려면 ①의 foundation과 ②의 confirmed model_repo가 필요하다. 둘 다 채워져 있다.

```
projects/devlog_dev_plugin/
├── .claude/settings.json              # PROJECT_ROOT=. + prerequisite·po-define·ai-web-dev 활성
├── foundation/                        # ── ① PREREQUISITE 산출 (준비 완료) ──
│   ├── VERSION                        #   foundation 버전 핀(=1)
│   ├── decisions/
│   │   ├── tech-stack.md              #   ★ Next.js 14 App Router·React·Tailwind·Drizzle·PostgreSQL·NextAuth (SRS COR-001)
│   │   ├── ops-stack.md               #   Standalone 빌드 + PM2 (COR-003·004), 비-LLM 관측
│   │   └── DECISIONS.md               #   결정 이유 로그
│   ├── platform-baseline/
│   │   ├── SPEC-000.md                #   공통 기능 명세: 인증(NextAuth)·앱셸(Header)·테마·라우팅 가드
│   │   └── SPEC-OPS-000.md            #   운영 명세: SCM·CI·CD(Standalone+PM2)·관측
│   ├── design-system/
│   │   ├── ds-allowlist.md            #   ★ DS 허용집합(계약): Header·PostCard·FilterBar·PomodoroTimer·ContributionGraph·WeeklyChart·StatCard + primitive
│   │   ├── ds-compiled.css            #   렌더용 실제 DS CSS (ADR-002 D8)
│   │   ├── ds-fixtures.json           #   렌더용 컴포넌트 마크업
│   │   ├── catalog/index.html         #   DS 카탈로그(대시보드)
│   │   └── ds-source/                 #   토큰 + README(프레임워크 주의: 시각 레퍼런스는 Vue, 구현은 React)
│   ├── design-pages/
│   │   ├── DP-MAIN.yaml               #   페이지 템플릿(header locked·content editable·footer locked)
│   │   └── renders/DP-MAIN.html
│   └── link-manifest.yaml             #   DS·DP 등록 인덱스
├── model_repo/                        # ── ② PO-DEFINE 산출 (확정 완료) ──
│   ├── screens/                       #   ★ 3개 confirmed screen model
│   │   ├── SCR-MAIN.yaml              #     메인: 타이머 + 검색/태그/정렬 + 글 카드 목록
│   │   ├── SCR-POST-DETAIL.yaml       #     글 상세: slug 조회 + 로딩/404/에러
│   │   └── SCR-DASHBOARD.yaml         #     대시보드: 통계카드 3 + 잔디밭 + 주간차트 (login 보호)
│   ├── renders/*.render.html          #   각 화면 결정론적 렌더 (실제 DS 모양)
│   ├── entities/
│   │   ├── ENT-POST.yaml              #   글 데이터 계약 (posts)
│   │   └── ENT-STUDY-LOG.yaml         #   학습 로그 계약 (study_logs)
│   ├── journeys/
│   │   ├── JRN-BROWSE-POST.yaml       #   글 탐색 여정 (메인→상세→복귀)
│   │   └── JRN-STUDY-SESSION.yaml     #   학습 세션 여정 (타이머→대시보드)
│   ├── specs/
│   │   ├── PACK-BLOG/spec-pack.yaml   #   ★ 블로그 도메인 팩 (SCR-MAIN+SCR-POST-DETAIL, ENT-POST) — 실측 pin 포함
│   │   └── PACK-STUDY/spec-pack.yaml  #   ★ 학습 도메인 팩 (SCR-MAIN+SCR-DASHBOARD, ENT-STUDY-LOG) — 실측 pin 포함
│   └── link-manifest.yaml             #   스파인 ID 원장 (전역 유일 채번)
└── app_repo/                          # ── ③ 산출물 (지금은 비어 있음 = 당신의 시작점) ──
    ├── frontend/ · backend/ · specs/  #   골격만 (.gitkeep)
    └── README.md
```

### 핀(pinned_contract)은 실측값이다
각 `PACK-*/spec-pack.yaml`의 `screens[].pinned_contract.layout_hash`는 **렌더 엔진(`pins.py`)으로 실제 계산한 값**이다.
따라서 Phase α의 `layout-hash-guard`가 **실제로 통과**한다(가짜 placeholder가 아님). 검증 명령은 §8 참고.

### 도메인 매핑 (SRS → 이 픽스처)
| SRS 요구 | 화면 | 팩 |
|---|---|---|
| SFR-001~004 글 목록·검색·태그·정렬 | SCR-MAIN | PACK-BLOG |
| SFR-009 좋아요(클라) / SFR-005 상세 이동 | SCR-MAIN → SCR-POST-DETAIL | PACK-BLOG |
| SFR-005 글 상세·로딩·404 | SCR-POST-DETAIL | PACK-BLOG |
| SFR-006 학습 타이머 → 로그 저장 | SCR-MAIN (timer) | PACK-STUDY |
| SFR-010 대시보드 통계·잔디밭·주간차트 | SCR-DASHBOARD | PACK-STUDY |
| SFR-007/012 로그인·로그아웃, SIR-002 Header, SFR-011 테마 | (공통) | **SPEC-000 baseline → Phase 0** |

> **`SCR-MAIN`은 두 팩(BLOG·STUDY)에 걸친다** — 한 화면이 여러 팩에 속하는 실제 사례. 그래서 Phase α가 **모든 화면 shell을 먼저 한 번에** 만든 뒤, Phase β가 팩별로 wiring만 더한다(중복·충돌 방지).

---

## 1. 환경 준비 (1회)

Claude Code(IDE)에서 리포 루트를 연 뒤:

```
/plugin marketplace add .
/plugin install ai-web-dev          # ③ (이 튜토리얼의 주인공)
/plugin install prerequisite        # ① (참고용; foundation은 이미 준비됨)
/plugin install po-define           # ② (참고용; model_repo는 이미 준비됨)
```

그다음 **작업 대상 프로젝트를 IDE로 연다**: `projects/devlog_dev_plugin/`
(루트가 아니라 이 폴더를 열어야 스크립트의 상대경로 `foundation/…`·`model_repo/…`가 맞는다. `.claude/settings.json`의 `PROJECT_ROOT="."` 참조.)

> ③의 입력은 모두 준비돼 있으므로 ①·②는 설치만 해두면 된다(다시 실행할 필요 없음).

---

## 2. 부트스트랩 — speckit 메커니즘 vendoring (1회)

speckit 슬래시 명령이 동작하려면 `app_repo/`에 `.specify/`가 있어야 한다.

```bash
# 리포 루트에서 (또는 절대경로로)
bash packages/plugin-ai-web-dev/hooks/install-speckit.sh
#   (Windows PowerShell: packages/plugin-ai-web-dev/hooks/install-speckit.ps1)
```

설치되는 것:
- `app_repo/.specify/` — speckit scripts·templates·workflows (플러그인에서 vendoring, 멱등)
- git 훅: `tdd-gate.py`·`commit-spine-id.py`·`speckit-artifact-guard.py`·`layout-hash-guard.py`·`manifest-sync.py`
- `app_repo/.specify/.source` — `plugin@version` 핀

> 플러그인을 업그레이드하면 `speckit-sync.sh`로 메커니즘만 다시 복사한다(memory·feature.json 등 상태는 보존).

---

## 3. Phase 0 — 공통 기능 Baseline (프로젝트 1회)

`SPEC-000`(인증·셸·테마)·`SPEC-OPS-000`(배포·CI)을 받아 **각 요건의 전달 모드(A/B)**를 정하고 산출한다.

```
/speckit-specify
```
- 입력: `foundation/platform-baseline/SPEC-000.md` + `SPEC-OPS-000.md` + `foundation/decisions/{tech-stack,ops-stack}.md`
- 출력: `app_repo/baseline-delivery-manifest.yaml` — 기능·운영 요건별 `mode: A|B + 사유`

DevLog 권장 모드(각 SPEC의 `delivery(권장)` 열):
| 요건 | 모드 | 산출 |
|---|---|---|
| FEAT-AUTH-1/2/3 NextAuth 로그인·JWT·로그아웃 | **B** | `app_repo/`에 NextAuth 설정·Server Action 완성 코드 + 테스트 |
| FEAT-AUTH-4 라우팅 가드, FEAT-SHELL-* Header, FEAT-THEME-1 테마 | **A** | `app_repo/.claude/skills/baseline-guides/<feature>/SKILL.md` 가이드 |
| FEAT-ERR-*/VALID-*/HYDRATION-1 공통 패턴 | **A** | baseline-guides 가이드 |
| OPS-CD-1 Standalone 빌드, OPS-SCM-* | **B** | `next.config.ts`(standalone)·`.gitignore`·CI 파이프라인 |

```
# mode B 요건 (예: NextAuth)
/speckit-plan        # 데이터/설정 설계
/speckit-tasks       # test-first 태스크
   ── Gate B (개발자 승인) ──
/speckit-implement   # red→green→refactor→commit  [SPEC-000/T### (baseline)]
```
mode A 요건은 `baseline-guides/<feature>/SKILL.md`로 작성되어 Phase β가 도메인 구현 시 로드해 적용한다.

> 데모 계정(alice/bob/kim, 평문 비교) = DAR-004. NextAuth Credentials + JWT(쿠키) = SFR-007. 운영 시 bcrypt 필수(코드 주석).

---

## 4. Phase α — Layout Scaffold (전체 화면 1회)

모든 confirmed screen model → 프론트엔드 페이지 shell **일괄 생성**.

```
/speckit-scaffold
```
- 입력: `model_repo/screens/*.yaml` (3개 confirmed) + `renders/*.render.html`(참조)
- 동작: 각 화면의 `position`(좌표) 그대로 DS 컴포넌트를 배치한 **layout-only shell** 생성. wiring·이벤트·API는 없음.
- 프레임워크 파생: `tech-stack.md`의 `frontend.framework = Next.js(App Router)` → `app_repo/frontend/app/` 아래 `.tsx`:
  - `app/page.tsx` (SCR-MAIN) · `app/posts/[slug]/page.tsx` (SCR-POST-DETAIL) · `app/dashboard/page.tsx` (SCR-DASHBOARD)
  - 경로는 각 팩 `spec-pack.yaml`의 `screens[].shell_ref`와 일치.

**진입 가드 — `layout-hash-guard.py`** (이 픽스처의 핵심 검증):
각 화면을 ②와 동일 엔진으로 재렌더해 `layout_hash`가 `pinned_contract.layout_hash`와 일치하는지 확인한다. 불일치면 **빌드 차단**(=②확정 위치를 ③이 못 바꾼다). 이 픽스처는 실측 pin이라 **통과**한다.

```bash
python packages/plugin-ai-web-dev/hooks/layout-hash-guard.py --root projects/devlog_dev_plugin
# 기대: ✅ SCR-MAIN / SCR-POST-DETAIL / SCR-DASHBOARD layout_hash 일치 → PASS
```
커밋: `[SCAFFOLD] ...` (tdd-gate skip, commit-spine-id 예외).

---

## 5. Phase β — Spec Pack Iteration (팩마다 반복)

팩 = 도메인 모듈. 두 팩을 각각 돈다: **PACK-BLOG**, **PACK-STUDY**.

```
# ── PACK-BLOG (글 목록·검색·정렬·상세) ──
/speckit-specify   # pack-to-spec.py 가 PACK-BLOG/spec-pack.yaml + SCR-MAIN·SCR-POST-DETAIL 에서 spec.md 초안 생성
                   #   → app_repo/specs/<NNN>-blog/spec.md (검토)
/speckit-plan      # ENT-POST → Data Model·ERD·Drizzle posts 스키마 *파생* (발명 금지)
                   #   NOTE-MAIN.001(complexity:high, KST 시각 규칙) → bl-analyst subagent 자동 호출
/speckit-tasks     # T### test-first 정렬 ([P] 병렬 마커, backend→frontend)
   ── Gate B: Data Model·ERD·BL·Task 확정, bl 미해결 0, 개발자 approve ──
/speckit-implement # T### 순서대로:
                   #   ① test-author subagent: acceptance(Gherkin)+worked example → 실패 테스트 먼저 (API·화면 2계층)
                   #   ② red→green→refactor
                   #   ③ tdd-gate.py: 테스트 없음/실패 시 commit 차단
                   #   ④ commit-spine-id.py → [PACK-BLOG/T001] 요약 (REQ-MAIN.001) 자동 커밋
                   # → code-reviewer subagent 검토
```
같은 흐름을 **PACK-STUDY**(타이머 저장 + 대시보드 집계, ENT-STUDY-LOG)로 반복. `NOTE-DASHBOARD.001`(complexity:high, 잔디밭 KST 날짜 키)도 bl-analyst가 받는다.

**Frontend wiring 원칙:** Phase α shell에 API hook·상태·권한 조건부 렌더·에러 처리만 더한다. **layout 좌표는 건드리지 않는다**(layout-hash-guard가 계속 감시).

> `SCR-MAIN`은 두 팩에 걸치므로, PACK-BLOG는 검색/목록/좋아요/이동 wiring을, PACK-STUDY는 타이머→study_log 저장 wiring을 **같은 shell(`app/page.tsx`)에 분담**해 추가한다.

---

## 6. Phase γ — Integration & NFR (배포 전)

②의 여정(JRN-)을 Playwright(+BDD) E2E로 구현한다(새 시나리오 발명 금지 — 각 step은 화면 action의 acceptance 재사용).

```
JRN-BROWSE-POST   → e2e: 메인에서 카드 클릭 → 상세 표시 → 목록 복귀
JRN-STUDY-SESSION → e2e: (로그인) 타이머 1분+ 정지 → study_log 저장 → 대시보드 반영
```
- 커밋: `[E2E/JRN-BROWSE-POST] ...`
- NFR: 성능(PER-001 LCP 1초)·보안(SER-001 다층 방어)·Hydration(QAR-005) + 배포(ops-stack: Standalone+PM2).

---

## 7. (선택) Change Order — 계약이 바뀌면

구현 중 PO가 화면을 고치고 싶으면 자동 재생성하지 않는다.
- ③: 스파인 ID 단위 diff + blast radius → `dismiss`(외관, re-pin) / `amend`(경미, 제자리 수정) / `regenerate`(중대 → ② Gate A 재확정 → 해당 팩만 재발행).
- `layout_hash`가 바뀌는 위치 변경은 **반드시 ② Gate A 재확정 → re-pin**으로만 반영된다.

---

## 8. 검증 체크포인트 (직접 돌려볼 수 있는 명령)

이 픽스처가 ③ 게이트를 실제로 통과하는지 확인:

```bash
# (a) Phase α 진입 가드 — layout_hash 일치 (가장 중요)
python packages/plugin-ai-web-dev/hooks/layout-hash-guard.py --root projects/devlog_dev_plugin
#   → PASS (3화면 × 2팩 모두 일치)

# (b) screen model 스키마 + L1~L5 lint (②의 저장 훅)
for f in projects/devlog_dev_plugin/model_repo/screens/SCR-*.yaml; do
  python packages/plugin-po-define/hooks/on-save-schema-validate.py "$f"
  python packages/plugin-po-define/hooks/on-save-lint-L1-L4.py "$f"
done
#   → 모두 ✅ pass

# (c) pin 재계산이 spec-pack 값과 일치하는지
python packages/harness-core/render/pins.py --json projects/devlog_dev_plugin/model_repo/screens/SCR-MAIN.yaml
#   → layout_hash: sha256:05a3d59b…  (PACK-BLOG/PACK-STUDY 의 SCR-MAIN pinned_contract 와 동일)

# (d) Gate A 재현 (이미 confirmed; --pi-approved 로 판정만 재확인)
cd projects/devlog_dev_plugin && GATE_A_PO_APPROVED=1 python \
  ../../packages/plugin-po-define/skills/gate-a-check/scripts/gate-a-check.py --pi-approved \
  model_repo/screens/SCR-MAIN.yaml model_repo/screens/SCR-POST-DETAIL.yaml model_repo/screens/SCR-DASHBOARD.yaml
#   → 🎉 Gate A 통과
```

> 화면 위치를 바꿔보면(예: 어떤 `position.base.col_span`을 full→half) (a)가 **❌ 차단**된다 — ②확정 위치 보호가 작동하는지 직접 확인할 수 있다. (확인 후 되돌리고 `render_screen.py`로 재렌더.)

---

## 9. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `/speckit-*`가 안 먹힘 | §2 `install-speckit` 부트스트랩 미실행. `app_repo/.specify/` 존재 확인. |
| `tdd-gate`가 commit 차단 | 테스트가 없거나 실패. test-author로 테스트 먼저. 러너 미설정 시 `HARNESS_TEST_CMD` 지정(예: `vitest run`). 정 안되면 `HARNESS_TDD_ALLOW_NO_RUNNER=1`(권장 안 함). |
| 커밋이 스파인 ID로 거부 | `[PACK-BLOG/T001] 요약 (REQ-MAIN.001)` 형식 준수. baseline은 `[SPEC-000/T### (baseline)]`. |
| `layout-hash-guard` 불일치 차단 | ②확정 위치를 ③이 바꾼 것. 위치 변경은 ② Gate A 재확정→re-pin으로만. (시각 자산 변경은 무관 — layout_hash는 좌표 전용.) |
| `spec-pack-guard.py`가 "yaml_ref 파일 없음" | **수정됨(2026-06-30).** 과거 이 스크립트는 팩을 `<root>/specs/`(3-depth)로 가정해 `model_repo/specs/`(4-depth)의 yaml_ref를 못 찾았으나, 이제 `layout-hash-guard`와 동일하게 프로젝트 루트를 역추적한다. 어느 cwd에서도 동작하며 `--write-pins`(핀 자동 기록)도 정상 작동한다. |
| DS 컴포넌트가 Vue인데 앱은 React? | 화면 모델은 프레임워크 중립. `ds-allowlist.md`의 **계약**(props·states)만 ③가 React로 구현(`design-system-usage` 스킬). `ds-source/README.md` 참조. |

---

## 부록 — 스파인 추적 그래프 (이 픽스처)

```
DP-MAIN ─인스턴스화→ SCR-MAIN ┬ CMP-MAIN.{timer,filterbar,postlist}
                              │   REQ-MAIN.001~006 → acceptance(Gherkin)
                              ├─→ ENT-POST · ENT-STUDY-LOG
                              ├─→ PACK-BLOG  (SCR-MAIN+SCR-POST-DETAIL, ENT-POST,    JRN-BROWSE-POST)
                              └─→ PACK-STUDY (SCR-MAIN+SCR-DASHBOARD,  ENT-STUDY-LOG, JRN-STUDY-SESSION)
        ─인스턴스화→ SCR-POST-DETAIL → REQ-POST-DETAIL.001~002
        ─인스턴스화→ SCR-DASHBOARD   → REQ-DASHBOARD.001~002

③:  PACK → /speckit-* → app_repo/specs/<NNN>/{spec,plan,tasks}.md → T### → test → commit
    JRN  → Playwright e2e
```

> 상세 아키텍처: 리포 루트 `README.md`·`USER-GUIDE.md`·`docs/ADR-001`·`docs/ADR-002`, ③ 상세: `packages/plugin-ai-web-dev/README.md`.
