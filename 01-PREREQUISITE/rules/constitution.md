# Constitution — 하드 룰 (불변)

이 파일은 전 레이어 공통으로 항상 적용된다. 변경 시 모든 레이어 README와 CLAUDE.md를 함께 갱신해야 한다.

---

## 원칙 1 — Screen Model이 단일 진실원

**screen model(YAML)이 단일 원본(single source of truth)이다.**

- HTML 파일은 screen model에서 자동 생성된 **파생 뷰**다. 저장은 허용하되 직접 편집은 금지한다.
- PI와 개발자가 화면을 확인할 때는 HTML 뷰를 본다. 수정이 필요하면 반드시 screen model YAML을 수정하고, 렌더링이 자동으로 HTML을 업데이트한다.
- HTML을 직접 편집한 내용은 다음 렌더링 시 덮어씌워진다(소실 보장).
- 모든 렌더된 HTML 파일 상단에는 다음 주석을 포함해야 한다:

```html
<!-- GENERATED VIEW — source: {SCR-ID}.yaml v{version} — DO NOT EDIT -->
```

## 원칙 2 — Design System 폐쇄

**DS(design system) 집합 밖의 컴포넌트는 screen model에 들어올 수 없다.**

- 허용 집합의 원본: `foundation/design-system/design-guide.md`
- lint L1이 model 레벨에서 기계적으로 강제한다. DS 밖 컴포넌트 사용 시 error.
- DS 컴포넌트는 design token으로 모든 스타일이 정의되어 있다. 렌더링 시 토큰을 그대로 사용한다.

## 원칙 3 — 스파인 ID

**모든 아티팩트는 스파인 ID를 가진다.**

규칙 상세: `01-PREREQUISITE/rules/spine-ids.md`

| 접두사 | 대상 |
|---|---|
| SCR- | 화면 |
| CMP- | 컴포넌트 인스턴스 |
| REQ- | 요구사항(action) |
| NOTE- | 노트 |
| NFR- | 비기능 요구사항 |
| SPEC- | 수직 슬라이스 spec |
| T### | 태스크 |
| DP- | design page 템플릿 |

추적 그래프: `SCR → CMP → REQ → acceptance → test → SPEC → task → commit`

## 원칙 4 — 저장은 Optimistic Locking

last-write-wins 금지. version 체크로 충돌 감지 → 409 반환.

## 원칙 5 — Headless 호출 결과물

headless 호출(Claude)은 raw HTML이 아니라 **screen model patch**를 반환한다.
오케스트레이터가 patch를 screen model에 적용하고, 렌더링은 layout-recommend skill이 담당한다.

## 원칙 6 — 플랫폼 코드는 TDD

테스트 먼저, 실패→통과→리팩터. tdd-gate hook이 테스트 없는 commit을 차단한다.

## 원칙 7 — Commit 메시지에 스파인 ID

형식: `[<SPEC|MOD>/<task>] 요약 (REQ-...)`
예: `[SPEC-014/T1] 주문 엑셀 내보내기 API (REQ-ORDER-LIST.001)`
