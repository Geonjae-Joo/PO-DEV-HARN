# Constitution — 하드 룰 (불변)

이 파일은 전 레이어 공통으로 항상 적용된다. 변경 시 모든 레이어 README와 CLAUDE.md를 함께 갱신해야 한다.

---

## 원칙 1 — Screen Model이 단일 진실원

**screen model(YAML)이 단일 원본(single source of truth)이다.**

- HTML 파일은 screen model에서 자동 생성된 **파생 뷰**다. 저장은 허용하되 직접 편집은 금지한다.
- PO와 개발자가 화면을 확인할 때는 HTML 뷰를 본다. 수정이 필요하면 반드시 screen model YAML을 수정하고, 렌더링이 자동으로 HTML을 업데이트한다.
- HTML을 직접 편집한 내용은 다음 렌더링 시 덮어씌워진다(소실 보장).
- 모든 렌더된 HTML 파일 상단에는 다음 주석을 포함해야 한다:

```html
<!-- GENERATED VIEW — source: {SCR-ID}.yaml v{version} — DO NOT EDIT -->
```

## 원칙 2 — Design System 폐쇄

**DS(design system) 집합 밖의 컴포넌트는 screen model에 들어올 수 없다.**

- 허용 집합의 원본: `foundation/design-system/ds-allowlist.md`
- lint L1이 model 레벨에서 기계적으로 강제한다. DS 밖 컴포넌트 사용 시 error.
- DS 컴포넌트는 design token으로 모든 스타일이 정의되어 있다. 렌더링 시 토큰을 그대로 사용한다.

## 원칙 3 — 스파인 ID

**모든 아티팩트는 스파인 ID를 가진다.**

규칙 상세: `packages/harness-core/rules/spine-ids.md`

| 접두사 | 대상 |
|---|---|
| SCR- | 화면 |
| CMP- | 컴포넌트 인스턴스 |
| REQ- | 요구사항(action) |
| ENT- | 개념 데이터 엔티티 계약 |
| EXT- | 외부 연동 시스템 계약 |
| NOTE- | 노트 |
| NFR- | 비기능 요구사항 |
| JRN- | 화면 간 사용자 여정(=E2E 시나리오) |
| Q- | HITL 질문 |
| PRM- | prompt log 항목 |
| PACK- | 도메인 spec 팩 (②가 발행, ③ 구현 단위) |
| SPEC- | 플랫폼/baseline spec (SPEC-000 공통 기능, SPEC-OPS-000 운영) |
| T### | 태스크 |
| DP- | design page 템플릿 |

> 전체 채번 규칙·형식은 `spine-ids.md`가 단일 출처다. 위 표는 요약이다.

추적 그래프: `SCR → CMP → REQ → acceptance → PACK → task → test → commit`

## 원칙 4 — 저장은 Optimistic Locking

last-write-wins 금지. version 체크로 충돌 감지 → 409 반환.

## 원칙 5 — Headless 호출 결과물

headless 호출(Claude)은 raw HTML이 아니라 **screen model patch**를 반환한다.
오케스트레이터가 patch를 screen model에 적용하고, 렌더링은 layout-recommend skill이 담당한다.

## 원칙 6 — 플랫폼 코드는 TDD

테스트 먼저, 실패→통과→리팩터. tdd-gate hook이 테스트 없는 commit을 차단한다.

## 원칙 7 — Commit 메시지에 스파인 ID

형식: `[<PACK|SPEC|MOD>/<task>] 요약 (REQ-...)`
예: `[PACK-ORDER/T001] 주문 엑셀 내보내기 API (REQ-ORDER-LIST.001)`
(PACK-=도메인 팩, SPEC-=baseline, MOD=모듈 변경. 상세: `packages/plugin-ai-web-dev/rules/commit-convention.md`)

## 원칙 8 — 기술 스택은 프로젝트마다 constitution으로 정의

**프레임워크·테스트 스택은 하니스에 고정돼 있지 않다.** 프론트엔드·백엔드 모두 ① PREREQUISITE 단계에서 **`/speckit-constitution`** 으로 결정해 `foundation/decisions/tech-stack.md`에 핀으로 박는다. (※ `/speckit-constitution` 커맨드 정의 자체는 ③ AI-WEB-DEV의 speckit 하네스에 들어 있다 — ①은 그 결과인 tech-stack.md 핀을 소유한다.) ②·③의 scaffold·plan·tasks·test·tdd-gate는 이 핀만 참조하고 어떤 특정 스택도 가정하지 않는다. 다른 문서·스킬의 "React"·"Spring Boot" 등은 예시 표기일 뿐이다. 변경은 `/speckit-constitution` 재실행 + 전 레이어 동기화로만(`.specify/memory/constitution.md` §Technology Stack 포함).
