# ADR-001 — 3-Tier / 3-Runtime 아키텍처

- 상태: 채택 (2026-06-19), 이행 진행 중
- 개정: 2026-06-29 — D2 개정(② 듀얼 런타임). 아래 "개정 이력 / R1" 참조.
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

### D2. 같은 harness-core → 런타임 (R1 개정)

- `plugin-prerequisite` (①) · `plugin-ai-web-dev` (③) = **Claude Code 플러그인**.
- ② = **능력/제품 분리**(R2 정정): ②의 **능력**은 플러그인 **`po-define`**(`packages/plugin-po-define/`)이다 — `plugin-prerequisite`(①)·`plugin-ai-web-dev`(③)와 동일한 Claude Code/Cowork 플러그인. ②의 **챗봇**은 별도 패키지 **`po-def-chat`**(`packages/po-def-chat/`)으로, Agent SDK로 빌드되며 **`plugin-po-define`의 skill·hook·rule 소스를 로드해 사용**한다. 즉 "능력=플러그인 / 제품=챗봇"으로 분리하고, 챗봇은 플러그인을 가져다 쓴다("같은 로직, 다른 포장"의 정확한 형태).
- 모든 런타임이 `harness-core`의 rules·skill·lint를 단일 출처로 공유 → 도구 간 강제 일치.

> **개정 전(R0):** ②는 Agent SDK 챗봇으로만 빌드하고 마켓플레이스 플러그인으로 등록하지 않기로 했다. 근거는 "②의 운영자=기획자는 IDE를 쓰지 않는다"였다.
>
> **개정 후(R1) 근거:**
> 1. **교차 의존 노출** — ①의 `design-page-builder`가 만드는 DP-* 템플릿은 ②의 SCR 인스턴스가 `from_template`으로 상속한다. 따라서 `screen-model-schema-v2.md`는 ② 전용이 아니라 **①·②가 함께 지키는 교차 계약**이며, ②가 어느 런타임에도 노출되지 않으면 ①이 이 스키마를 컨텍스트로 로드할 경로가 없다(실제 drift 발생). → 스키마를 `harness-core/rules/`로 이동(D2-a)하고, ②를 플러그인으로도 포장해 같은 런타임에서 검증 가능하게 한다.
> 2. **Cowork 등장** — 비개발자(기획자)가 IDE 없이 Cowork에서 ② skill을 직접 쓸 수 있다. "기획자는 IDE를 안 쓴다"는 R0 전제가 약해졌다 — 오히려 플러그인 포장을 **추가**할 근거.
> 3. **챗봇 빌드와 비충돌** — 챗봇은 플러그인을 import 하는 게 아니라 같은 소스 파일을 코드로 로드한다. `plugin.json`은 그 위에 얹는 Claude Code용 매니페스트일 뿐, 챗봇 빌드를 막지 않는다.

### D2-a. 교차 계약은 harness-core 단일 출처 (R1 신설)

- `screen-model-schema-v2.md`는 ①(DP 템플릿)·②(SCR 인스턴스)가 공유하는 계약이므로 `packages/harness-core/rules/`로 이동한다(constitution·spine-ids·ds-closure와 동일 위치 원칙).
- `packages/plugin-po-define/rules/`의 원본은 harness-core를 가리키는 redirect stub으로 남긴다(내용 중복=drift 방지).
- ①의 `design-page-lint.py`에 §7 필드 검사(`source.kind`·`position.base`·`col_span` 픽셀 금지)를 추가해, 어느 런타임에서 실행되든 저장 시 자동으로 스키마 정합을 강제한다.

### D3. 복사 대신 참조 + 버전 핀

- ①→②, ①→③, ②→③ 모두 같은 `projects/<id>/`를 **참조**. `foundation/VERSION`으로 핀(재현성).
- 물리 복사는 **③가 app_repo를 독립 배포 repo로 추출하는 순간**에만.

### D4. 경로 파라미터화

- 스크립트의 `output/foundation/…` → `foundation/…`. Claude Code는 프로젝트 루트를 cwd로 열어 상대경로가 맞고, 챗봇은 `PROJECT_ROOT` 주입.

## 결과

- 드리프트·이중관리 제거(복사본 0), 운영 중 ① 수정이 ②(다음 세션)·③(re-pin)로 자연 전파.
- 멀티테넌트: 챗봇 1개가 `PROJECT_ROOT`만 바꿔 여러 프로젝트 서빙.
- (R1) ②가 Claude Code/Cowork에서도 즉시 사용 가능 — 챗봇 빌드 완료를 기다리지 않아도 됨. 교차 계약 drift를 스키마 위치(harness-core)·lint·플러그인 컨텍스트 로딩 세 겹으로 방지.
- 트레이드오프: 플러그인/챗봇 패키징·배포 파이프라인이 필요(기존엔 폴더만 있으면 됐음). (R1) ②의 save 훅이 두 런타임(플러그인 Write|Edit 훅 / 챗봇 validator)에서 모두 동작하도록 stdin·argv 양쪽을 인식해야 함.

## 이행 메모

- 구 레이어 폴더 정리(2026-06-19): `03-AI-WEB-DEV/`·`_archive_pre_migration/`는 **제거 완료**. `01-PREREQUISITE/`·`02-PO-DEV-CHAT/`는 내용은 전부 이전됐으나 sandbox가 최상위 디렉터리 삭제를 막아 빈 셸로 남음 — **사용자 수동 삭제 필요**(파일 탐색기).
- `DECISIONS.md` 신설 완료(`projects/example/foundation/decisions/DECISIONS.md`). ds-closure 검증 로직은 `harness-core/lib/ds_closure.py` 단일 출처로 통합(① design-page-lint·② on-save-lint가 import, 실패 시 동치 폴백).
- 후속 작업: ② 챗봇 실제 빌드, `.specify/` 심층 경로 감사, 플러그인 매니페스트(plugin.json/settings.json hooks) 스키마를 현행 Claude Code 문서로 최종 검증, 프로젝트에 마켓플레이스 등록(`/plugin marketplace add .`).

## 개정 이력

### R1 (2026-06-29) — ② 듀얼 런타임 + 교차 계약 단일출처화

- **D2 개정**: ②를 "Agent SDK 챗봇 전용"에서 "Claude Code/Cowork 플러그인 + Agent SDK 챗봇" 듀얼 런타임으로. 둘 다 같은 ② 소스를 가리킴. (R2에서 능력/제품 분리로 재정정 — 아래 참조.)
- **D2-a 신설**: `screen-model-schema-v2.md`를 교차 계약으로 보고 `harness-core/rules/`로 이동(단일 출처). ② rules의 원본은 redirect stub.
- **변경 파일**: `packages/plugin-po-define/.claude-plugin/plugin.json`(신규), `marketplace.json`(② 등록), `packages/harness-core/rules/screen-model-schema-v2.md`(이동), `packages/plugin-prerequisite/skills/design-page-builder/scripts/design-page-lint.py`(§7 검사 추가), `plugin-po-define/hooks/on-save-*.py`(stdin·SCR 필터). *(경로는 R2 추출 후 기준으로 표기.)*
- **동기 결함**: 직전 design-page-builder 실행 시 ②의 스키마가 ① 런타임 컨텍스트에 없어 DP YAML이 §7과 drift할 위험이 있었음.

### R2 (2026-06-29) — ② 능력/제품 분리

- 능력을 `plugin-po-define`으로 추출(마켓플레이스 ID `po-define`), 챗봇 패키지를 `po-def-chat`으로 리네임.
- 이유: `po-dev-chat`은 챗봇 제품명. 능력은 ①③처럼 독립 플러그인이어야 함. R1이 둘을 한 패키지에 합친 것을 정정.
