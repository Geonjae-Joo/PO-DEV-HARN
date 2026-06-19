# Migration Plan — 3-Tier / 3-Runtime 재구조화

> 목적: 현재 `01/02/03` 레이어 폴더(코드+데이터 혼재)를 **시스템(코드)과 프로젝트(데이터)로 분리**하고,
> 운영자·도구에 맞춰 세 런타임으로 패키징한다. foundation은 복사가 아니라 **버전 있는 단일 소스로 참조**한다.
> 작성일: 2026-06-19.

---

## 1. 왜 바꾸나 (배경)

세 가지 상황이 기존 "한 번 복사하는 핸드오프" 모델을 무효화한다.

1. **운영 중 ① 드문 수정** — app_repo 빌드 후 운영 단계에서도 PREREQUISITE 내용이 가끔 바뀐다. 복사본을 유지하면 드리프트.
2. **② 가 배포 챗봇 제품** — PO-DEV-CHAT은 Claude Agent SDK 기반 챗봇 웹앱이 되어, 그 안의 agent가 ②의 skill을 사용한다. 즉 ②는 일회성 저작 폴더가 아니라 **상시 가동 서비스**.
3. **운영자·도구가 레이어마다 다름**:

| 레이어 | 운영자 | 도구 |
|---|---|---|
| ① PREREQUISITE | 개발자 | Claude Code (IDE) |
| ② PO-DEV-CHAT | 기획자 | Claude Agent SDK 챗봇 (web) |
| ③ AI-WEB-DEV | 개발자 | Claude Code (IDE) |

→ Claude Code는 연 폴더의 `.claude/`를 네이티브로 읽고, Agent SDK는 skill을 코드로 로드한다. **같은 로직, 다른 포장**이 필요하다.

---

## 2. 목표 구조

### 2.1 3-Tier 분류

- **Tier 1 — 시스템(코드, 전 프로젝트 공용)**: 불변 rules(constitution·spine-ids·ds-closure), 공용 lint 라이브러리, 모든 skill·hook, ② 챗봇 앱, ③ builder.
- **Tier 2 — 프로젝트 foundation 데이터(①이 작성)**: ds-allowlist·ds-source·design-pages·decisions(tech/ops-stack)·SPEC-000/OPS·link-manifest.
- **Tier 3 — 프로젝트 작업·산출 데이터**: model_repo(②가 생성), app_repo(③ 빌드 결과).

> constitution·spine-ids·ds-closure는 **모든 프로젝트에 동일한 법**이라 Tier 1. ds-allowlist·decisions·SPEC은 **프로젝트마다 다른 데이터**라 Tier 2.

### 2.2 시스템 모노레포 (Tier 1)

```
PO-DEV-Harn/
├── package.json                 # workspace (pnpm/uv)
├── marketplace.json             # ①③ 플러그인 마켓플레이스
├── docs/                        # 아키텍처·마이그레이션·챗봇 가이드
├── packages/
│   ├── harness-core/            # 불변 rules + ds_closure lint 라이브러리 + SKILL 원본
│   ├── plugin-prerequisite/     # ① → Claude Code 플러그인
│   ├── plugin-ai-web-dev/       # ③ → Claude Code 플러그인
│   └── po-dev-chat/             # ② → Agent SDK 챗봇 (소스; 빌드는 별도)
```

### 2.3 프로젝트 워크스페이스 (Tier 2+3, 데이터)

```
projects/<customer-id>/
├── .claude/settings.json        # 활성화할 플러그인 + PROJECT_ROOT 경로 (①③ Claude Code용)
├── foundation/                  # Tier 2 (① 산출)
│   ├── design-system/{ds-source/, ds-allowlist.md}
│   ├── design-pages/DP-*.yaml
│   ├── decisions/{tech-stack.md, ops-stack.md}
│   ├── platform-baseline/{SPEC-000.md, SPEC-OPS-000.md}
│   ├── link-manifest.yaml
│   └── VERSION                  # 핀·재현성
├── model_repo/                  # Tier 3 (② 챗봇 산출)
└── app_repo/                    # Tier 3 (③ 산출 → 최종 독립 repo로 추출)
```

세 런타임 모두 같은 `projects/<id>/foundation`을 **참조**(복사 아님), `VERSION`으로 핀.

---

## 3. 도구 ↔ 프로젝트 연결

- **개발자 ① (Claude Code)**: `projects/<id>/`를 IDE로 열고 prerequisite 플러그인 활성화 → skill·hook이 `foundation/`에 작업.
- **개발자 ③ (Claude Code)**: 같은 `projects/<id>/`를 열고 ai-web-dev 플러그인 활성화 → `foundation/`+`model_repo/` 읽어 `app_repo/` 빌드.
- **기획자 ② (챗봇)**: 웹앱 접속 → 프로젝트 선택 시 agent에 `PROJECT_ROOT` + `foundation/VERSION` 주입 → 내장 skill이 `foundation/` 읽고 `model_repo/` 씀. IDE 불필요.

복사가 필요한 **유일한 경계** = ③가 `app_repo`를 독립 배포 repo로 추출하는 순간(자기완결성).

---

## 4. 자산 매핑 (재활용 계획)

분류: ✅ 그대로 · 🔧 수정 후 재활용 · 📦 위치만 이동 · 🆕 신규

### harness-core

| 현재 | 처리 | 변경 |
|---|---|---|
| `01/.claude/rules/constitution.md` | 🔧 | core로 이동, 단일 원본화. `③/.specify/memory/constitution.md`는 빌드 시 동기화 복사 |
| `01/.claude/rules/spine-ids.md` | 📦 | core로 이동 |
| `01/.claude/rules/ds-closure.md` | 📦 | core로 이동 |
| ds-closure 검증 로직 (lint 2곳 중복) | 🔧 | 공용 `lib/ds_closure.py`로 추출, 양쪽 import |

### plugin-prerequisite (①)

| 현재 | 처리 | 변경 |
|---|---|---|
| `design-page-builder/SKILL.md` | 🔧 | 경로 `output/foundation/`→`foundation/` |
| `scripts/design-page-lint.py` | 🔧 | 경로 파라미터화 + core lib import |
| `hooks/ds-guide-validate.py` | 🔧 | 경로 파라미터화 |
| `.claude/settings.json` | 🔧 | plugin.json 형식 |
| `input/design-system/project-design-guide.md` | ✅ | 플러그인 docs로 |
| `guides/first_design_page_guide.md` | 🔧 | 경로 갱신 후 플러그인 docs로 |

### plugin-ai-web-dev (③)

| 현재 | 처리 | 변경 |
|---|---|---|
| `speckit-*` 스킬 | 🔧 | 경로 파라미터화, 로직 유지 |
| `agents/*` | ✅ | 그대로 |
| `hooks/{commit-spine-id,tdd-gate,manifest-sync}.py` | 🔧 | 타깃 `${PROJECT_ROOT}/app_repo/.git` |
| `hooks/install-git-hooks.sh`·매니페스트 | 🔧 | 경로 파라미터화 |
| `rules/{change-order,commit-convention,gate-b,tdd-policy}` | ✅ | 그대로 |
| `.specify/*` | 🔧 | tech-stack 경로 등 갱신 |
| `design-system-usage·coding-style·baseline-guides·complex-bl` | ✅/🔧 | 대부분 그대로 |

### po-dev-chat (② — 변경 최대, 빌드는 다음 작업)

| 현재 | 처리 | 변경 |
|---|---|---|
| 9개 스킬 SKILL.md | 🔧 | 내용 재활용, 호출 방식 IDE→챗봇 대화로 |
| `hooks/on-save-*.py` | 🔧 | 로직 재활용, save 훅→**patch 적용 전 호출 validator**로 |
| `scripts/{sufficiency,gate-a}.py` | ✅ | 로직 그대로, 챗봇 tool로 |
| `rules/*` | 📦 | 챗봇 agent 컨텍스트로 |
| `question-bank.md`·`spec-pack-schema.md` | ✅ | 그대로 |
| `.claude/settings.json` | 🆕 | 폐기 → Agent SDK 설정 코드 |

### 프로젝트 데이터 (현재 output → projects/example 씨앗)

| 현재 | 처리 | 대상 |
|---|---|---|
| `01/output/foundation/*` | 📦 | `projects/example/foundation/` |
| `02/output/model_repo/*` | 📦 | `projects/example/model_repo/` |
| `03/output/app_repo/*` | 📦 | `projects/example/app_repo/` |

---

## 5. 공통 수정 규칙 (기계적)

1. **경로**: 스크립트 `output/foundation/…` → `foundation/…`. Claude Code는 프로젝트 루트를 열면 cwd가 거기라 상대경로 그대로 동작. 챗봇은 `PROJECT_ROOT` 주입.
2. **constitution 단일화**: core가 원본, `.specify/memory/`는 빌드 시 복사.
3. **ds-closure 검증 단일화**: 중복 2곳 → core 라이브러리 1곳.

---

## 6. 단계별 실행 순서 (동작 유지하며 점진)

1. **모노레포 골격** — `packages/` `projects/` + 루트 `package.json` + `marketplace.json` + plugin.json들.
2. **harness-core 추출** — rules 3종 + `ds_closure` 라이브러리.
3. **plugin-prerequisite** — ① 자산 이동 + 경로 파라미터화.
4. **plugin-ai-web-dev** — ③ 자산 이동 + 경로 파라미터화.
5. **po-dev-chat 소스 보존** — ② 자산 이동(빌드는 별도 작업; 방법은 `CHATBOT-DEV-GUIDE.md`).
6. **projects/example 데이터 이전** — 현재 output + `VERSION` 부여 + `.claude/settings.json`.
7. **README/ADR 정리 + 전체 검수**.

---

## 7. 재활용률 요약

- ①③ 자산: ~90% 그대로(경로만 변경)
- 공유 rules: 100%
- ② 스킬·검증 로직: ~85%(런타임 래핑만 변경)
- 데이터: 100% 이전

---

## 8. 남은 작업 (이 마이그레이션 범위 밖)

- **② 챗봇 실제 빌드** — `CHATBOT-DEV-GUIDE.md` 참조.
- **`.specify/` 심층 경로 감사** — speckit 스크립트의 잔여 경로 점검.
- ~~**DECISIONS.md 신설**~~ — 완료(`projects/example/foundation/decisions/DECISIONS.md`).
- ~~**ds-closure 로직 단일화**~~ — 완료(`harness-core/lib/ds_closure.py`를 ①② lint가 import).
- **플러그인 매니페스트 스키마 검증** — `plugin.json`/`settings.json`의 hooks 선언을 현행 Claude Code 플러그인 문서로 최종 확인(훅 경로는 `${CLAUDE_PLUGIN_ROOT}` 기준으로 정정함).
- **구 `01`·`02` 빈 폴더 수동 삭제** — sandbox 제약으로 자동 제거 불가.
