<!-- rule: 03-AI-WEB-DEV — Change Order 정책 (③ → ② 인계) -->

# Change Order Policy

확정된 계약(②)이 구현 중(③) 바뀔 때의 처리 규칙. **자동 재생성을 금지**하고,
pin·freeze 위에서 개발자가 판정한다.

## 5단계

1. **Pin** — spec은 생성 시점의 계약 버전(version·hash·git_ref)에 고정된다. 얼어붙은 스냅샷 위에서 작업한다.
2. **Freeze** — 구현 중인 화면은 소프트 프리즈. PO 편집은 즉시 반영되지 않고 **change-order 큐**에 누적된다.
3. **Change Order 발행** — PO 재확정 시, 스파인 ID 단위 diff + **blast radius**(영향 화면·팩 범위)를 계산해 변경 지시서를 만든다.
4. **개발자 판정** — 셋 중 하나:
   - **dismiss** — 외관/무관 변경 → 코드 변경 없이 **re-pin**만.
   - **amend** — 경미한 수정 → 제자리 수정 후 re-pin.
   - **regenerate** — 중대한 변경 → **해당 팩만** 재생성 + 새 Gate B. 재생성 자체는 ②의 `spec-generator` 스킬이 수행한다(PO 재확정 → 팩 재발행). ③는 *판정*까지만 — 새 계약을 만들지 않는다.
5. **TDD 백스톱** — acceptance 변경이면 기존 테스트가 깨진다(breaking). REQ 추가만이면 새 task(additive).

## 원칙

- **자동 재생성 금지** — 변경은 항상 개발자 판정을 거친다.
- 영향 범위는 **해당 팩으로 한정**한다. 전역 재생성하지 않는다.
- 판정 결과(dismiss/amend/regenerate + re-pin 버전)는 ②의 model_repo에 반영된다(③ → ② 인계).
- 커밋 prefix: `[CO/<판정>]`.
