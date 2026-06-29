# PO-DEV-CHAT 챗봇 개발 방법 (제안)

> ② PO-DEV-CHAT 레이어를 **Claude Agent SDK 기반 챗봇 웹앱**으로 만드는 방법 제안.
> 운영자는 기획자(PO), 도구는 IDE가 아니라 **웹 챗봇**. 실제 빌드는 별도 작업이며 이 문서는 설계 지침이다.
> 작성일: 2026-06-19.

---

## 0. 핵심 전환 한 줄

> Claude Code가 "연 폴더의 `.claude/` skill·hook을 자동 실행"하던 것을,
> **Agent SDK가 "skill을 코드로 로드하고, save 훅을 명시적 validator 호출로 대체"** 하도록 옮긴다.

skill의 **내용(SKILL.md)과 검증 로직(L1~L4·schema)은 그대로 재활용**하고, **트리거 방식만** 바꾼다.

---

## 1. 시스템 구성

```
┌─────────────────────────────────────────────────────────┐
│  PO-DEV-CHAT 챗봇 웹앱 (배포 단위)                          │
│  ┌───────────────┐   ┌──────────────────────────────┐    │
│  │ Frontend (web)│◄─►│ Agent Backend (Claude Agent SDK) │ │
│  │ 대화 UI +      │   │  - system prompt = harness-core │ │
│  │ 화면 미리보기   │   │    rules + ② schema             │ │
│  │ (render.html) │   │  - tools = ported skills        │ │
│  └───────────────┘   │  - validators = ex-hooks        │ │
│                      └──────────────┬───────────────────┘ │
└─────────────────────────────────────┼─────────────────────┘
                                       │ PROJECT_ROOT 주입
                                       ▼
                    projects/<id>/{foundation/, model_repo/}
                    (foundation 읽기 · model_repo 쓰기)
```

- **챗봇 코드**(FE+agent)는 제품. **프로젝트 데이터**는 `PROJECT_ROOT`로 마운트.
- 멀티테넌트: 세션마다 `PROJECT_ROOT`만 다르게 주입 → 챗봇 1개가 여러 고객 프로젝트 서빙.
- 챗봇 agent의 **LLM 런타임은 Claude Agent SDK**. (참고: 최종 산출물 app_repo가 쓰는 Samsung Fabrix LLM은 별개 — 그건 ③가 구현하는 대상 앱의 런타임.)

---

## 2. skill 포팅 (9종)

현재 `02/.claude/skills/`의 9개 SKILL.md를 Agent SDK의 **tool/skill 정의**로 옮긴다.

| 현재 skill | 챗봇에서의 역할 | 포팅 방식 |
|---|---|---|
| layout-recommend | Stage 1: DS 매핑 + screen model 초안 + HTML 렌더 | tool: `recommend_layout`, `render_screen` |
| action-interview | Stage 2: interactive 컴포넌트 순회 인터뷰 | 대화 흐름 + tool: `add_action` |
| note-intake | Stage 3: PO verbatim 노트 수집 | tool: `add_note` (본문 수정 금지 규칙 유지) |
| entity-intake / external-intake | 데이터·외부 계약 수집 | tool: `upsert_entity` / `upsert_external` |
| journey-map | 화면 간 여정(JRN-) 집계 | tool: `build_journey` |
| sufficiency-check | Stage 4: 충분성 기계 체크 + gap 분석 | **validator** (아래 §3) |
| gate-a-check | Gate A 통과 판정 | **validator** + 게이트 tool |
| spec-generator | confirmed → PACK-* 발행 | tool: `generate_spec_pack` |

포팅 규칙:
- SKILL.md의 **역할·규칙·출력형식 텍스트는 system prompt 또는 tool description으로 재사용**.
- 파일 경로는 전부 `${PROJECT_ROOT}` 기준. ds-allowlist·design-pages는 `${PROJECT_ROOT}/foundation/`에서 읽기.
- `sufficiency-check.py`·`gate-a-check.py` 스크립트는 **로직 그대로**, agent가 호출하는 함수/tool로 노출.

---

## 3. 훅 → validator 전환 (가장 중요한 변경)

Claude Code는 Write/Edit 저장 시 `on-save-schema-validate.py`(Pre)와 `on-save-lint-L1-L4.py`(Post)를 자동 실행했다. **Agent SDK엔 이 save 이벤트 훅이 없다.** 따라서:

```
[기존 — Claude Code]
PO가 YAML 저장 → PreToolUse(schema) → 저장 → PostToolUse(lint L1~L4) → 렌더

[전환 — 챗봇]
agent가 screen-model patch 생성
  → validate_schema(patch)        ← 통과 못하면 적용 거부 (구 Pre 훅)
  → apply patch to model_repo
  → lint_L1_L4(screen)            ← L1 실패면 롤백, L2~L4 실패면 open_question (구 Post 훅)
  → render_html()
```

- 검증 **코드는 100% 재활용**(L1 DS폐쇄·L2 완전성·L3 일관성·L4 커버리지·schema). `harness-core/lib/ds_closure.py`를 공유.
- 차이는 **자동 트리거 → agent 파이프라인의 명시적 단계**. agent는 patch를 적용하기 전·후에 validator를 반드시 호출하도록 오케스트레이션한다(스킵 불가하게 코드로 강제).
- **DS 폐쇄(L1)는 옵션이 아니다** — validator 실패 시 patch를 적용하지 않는다(가드레일 유지).

---

## 4. 4-Stage HITL → 대화 흐름

상태 머신 `draft → layout_confirmed → actions_in_progress → review → confirmed`을 **세션 상태**로 들고 간다.

1. **Stage 1 (layout)**: PO 발화 → `recommend_layout` → 렌더 미리보기 → patch 루프. 저장 시 §3 검증.
2. **Stage 2 (actions)**: interactive 컴포넌트별 인터뷰 → `add_action` + Gherkin acceptance.
3. **Stage 3 (notes)**: `add_note` (verbatim).
4. **Stage 4 (sufficiency)**: `sufficiency-check` validator → gap 있으면 재질문.
5. **Gate A**: `gate-a-check` → lint 0 + 충분성 통과 + 전 action 확정 + PO 승인 → `status: confirmed`.
6. **spec-generator**: PACK-* 발행 → `${PROJECT_ROOT}/model_repo/specs/`.

각 단계의 질문은 `question-bank.md` 재사용.

---

## 5. 데이터 접근·동시성

- **읽기**: `${PROJECT_ROOT}/foundation/`(ds-allowlist·design-pages·decisions). 세션 시작 시 `foundation/VERSION` 핀 → 세션 중 일관성.
- **쓰기**: `${PROJECT_ROOT}/model_repo/{screens,entities,externals,journeys,renders,specs}/`.
- **실서비스 스토리지**: 파일 대신 DB/object storage를 써도 **논리 구조 동일**(키 prefix `project/<id>/model_repo/...`). render.html은 파생 뷰로 캐시.
- **Optimistic locking 유지**: screen model의 `version` 필드 체크(constitution 원칙 4). 동시 편집 충돌 시 409 → 재조회.
- **단일 진실원 유지**: render.html은 model에서 생성된 파생 뷰, 직접 편집 금지(constitution 원칙 1).

---

## 6. system prompt 조립 (harness-core 재사용)

agent의 system prompt = 다음을 빌드 시 결합:
- `harness-core/rules/`의 constitution·spine-ids·ds-closure·**screen-model-schema-v2**(R1 이후 단일 출처, ①②③ 공통 계약)
- `plugin-po-define/rules/`의 data-contract-schema·journey-schema·state-machine·spec-readiness-checklist·prompt-log-policy (② 전용)

→ Claude Code가 `.claude/rules/`를 읽던 것과 **동일 내용을 system prompt로 주입**. rules 단일 출처(harness-core) 유지로 ①③와 강제가 일치.

---

## 7. ③로의 인계 / Change Order

- **②→③**: `generate_spec_pack`이 만든 PACK-*를 ③가 같은 워크스페이스에서 참조(`${PROJECT_ROOT}/model_repo/specs/`). 복사 아님.
- **③→②**: Change Order(dismiss/amend/regenerate) 도착 시, 별도 ② 스킬 없이 기존 Gate A 흐름으로 재확정 → `generate_spec_pack`이 버전 +1 재발행.

---

## 8. 권장 스택·구현 순서

스택 (예시, 확정은 `decisions/tech-stack.md` 원칙 따름):
- Agent: **Claude Agent SDK** (TypeScript 또는 Python).
- Backend: 세션·프로젝트 라우팅 + tool 실행 + validator.
- Frontend: 대화 UI + render.html 미리보기 + Gate A 승인 버튼.
- 저장: 초기엔 파일(`projects/<id>/`), 이후 DB/object storage.

구현 순서 (제안):
1. `harness-core/lib`의 validator(schema·L1~L4·sufficiency·gate-a)를 **순수 함수 라이브러리**로 확정.
2. agent tool 6종(`recommend_layout`·`render_screen`·`add_action`·`add_note`·`upsert_entity/external`·`generate_spec_pack`) 정의.
3. 오케스트레이션(§3 파이프라인 + §4 상태 머신).
4. PROJECT_ROOT 라우팅 + VERSION 핀 + optimistic locking.
5. 프런트(대화 + 미리보기 + Gate A).
6. ③ 인계·Change Order 경로.

---

## 9. 체크리스트 (빌드 시 DoD)

- [ ] 9개 skill 로직이 tool/validator로 포팅됨(경로 `PROJECT_ROOT` 기준)
- [ ] save 훅 2종이 patch 전후 validator 호출로 전환됨(스킵 불가)
- [ ] DS 폐쇄(L1) 실패 시 patch 미적용(가드레일)
- [ ] system prompt가 harness-core rules + ② schema에서 조립됨
- [ ] foundation 읽기/model_repo 쓰기가 PROJECT_ROOT 기준, VERSION 핀
- [ ] optimistic locking(version) 동작
- [ ] PACK-* 발행이 `model_repo/specs/`에 기록, ③가 참조
