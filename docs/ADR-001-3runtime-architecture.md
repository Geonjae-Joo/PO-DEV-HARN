# ADR-001 — 3-Tier / 3-Runtime 아키텍처

- 상태: 채택 (2026-06-19), 이행 진행 중
- 관련: `docs/MIGRATION-PLAN.md`, `docs/CHATBOT-DEV-GUIDE.md`

## 맥락

기존 `01/02/03` 레이어 폴더는 **코드와 데이터를 혼재**시켰고, "한 번 복사하는 핸드오프"를 전제했다. 그러나:

1. app_repo 빌드 후 운영 중에도 PREREQUISITE(①) 내용이 드물게 수정된다.
2. ② PO-DEV-CHAT은 Claude Agent SDK 기반 **챗봇 웹앱**(상시 서비스)이 된다.
3. 운영자·도구가 다르다: ①③ = 개발자/Claude Code(IDE), ② = 기획자/Agent SDK 챗봇.

복사 핸드오프는 드리프트·이중관리를 낳고, 운영 중 ① 수정 전파와 맞지 않는다.

## 결정

### D1. 코드와 데이터를 분리 (3-Tier)

- **Tier 1 시스템(코드)** = `packages/` — 전 프로젝트 공용.
- **Tier 2 foundation 데이터** = `projects/<id>/foundation/` — ①이 작성.
- **Tier 3 작업·산출 데이터** = `projects/<id>/{model_repo,app_repo}/`.

불변 rules(constitution·spine-ids·ds-closure)는 모든 프로젝트 공통 법이라 Tier 1(`harness-core`). ds-allowlist·decisions·SPEC은 프로젝트마다 달라 Tier 2.

### D2. 같은 harness-core → 3가지 런타임

- `plugin-prerequisite` (①) · `plugin-ai-web-dev` (③) = **Claude Code 플러그인**.
- `po-dev-chat` (②) = **Agent SDK 챗봇** (skill을 코드로 로드, save 훅을 명시적 validator로 전환).
- 셋 다 `harness-core`의 rules·skill·lint를 단일 출처로 공유 → 도구 간 강제 일치.

### D3. 복사 대신 참조 + 버전 핀

- ①→②, ①→③, ②→③ 모두 같은 `projects/<id>/`를 **참조**. `foundation/VERSION`으로 핀(재현성).
- 물리 복사는 **③가 app_repo를 독립 배포 repo로 추출하는 순간**에만.

### D4. 경로 파라미터화

- 스크립트의 `output/foundation/…` → `foundation/…`. Claude Code는 프로젝트 루트를 cwd로 열어 상대경로가 맞고, 챗봇은 `PROJECT_ROOT` 주입.

## 결과

- 드리프트·이중관리 제거(복사본 0), 운영 중 ① 수정이 ②(다음 세션)·③(re-pin)로 자연 전파.
- 멀티테넌트: 챗봇 1개가 `PROJECT_ROOT`만 바꿔 여러 프로젝트 서빙.
- 트레이드오프: 플러그인/챗봇 패키징·배포 파이프라인이 필요(기존엔 폴더만 있으면 됐음).

## 이행 메모

- 구 레이어 폴더 정리(2026-06-19): `03-AI-WEB-DEV/`·`_archive_pre_migration/`는 **제거 완료**. `01-PREREQUISITE/`·`02-PO-DEV-CHAT/`는 내용은 전부 이전됐으나 sandbox가 최상위 디렉터리 삭제를 막아 빈 셸로 남음 — **사용자 수동 삭제 필요**(파일 탐색기).
- `DECISIONS.md` 신설 완료(`projects/example/foundation/decisions/DECISIONS.md`). ds-closure 검증 로직은 `harness-core/lib/ds_closure.py` 단일 출처로 통합(① design-page-lint·② on-save-lint가 import, 실패 시 동치 폴백).
- 후속 작업: ② 챗봇 실제 빌드, `.specify/` 심층 경로 감사, 플러그인 매니페스트(plugin.json/settings.json hooks) 스키마를 현행 Claude Code 문서로 최종 검증, 프로젝트에 마켓플레이스 등록(`/plugin marketplace add .`).
