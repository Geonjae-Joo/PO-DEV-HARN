<!-- supporting-file: skills/journey-map, skills/spec-generator -->
<!-- loaded-by: journey-map 스킬이 여정 집계 시, spec-generator가 JRN- ref 포함 시 참조 -->

# Journey Schema — JRN-*.yaml (화면 간 사용자 여정 = E2E 시나리오)

> 화면 내부 acceptance(action 단위)와 달리, **여러 화면을 가로지르는 사용자 여정**의 단일 진실원.
> ②가 각 화면 action의 `navigate` outcome을 **집계**해 정의하고, ③ Phase γ가 **Playwright(+BDD)** E2E로 구현한다.
> step의 검증은 새로 쓰지 않고 각 화면 action의 **acceptance(Gherkin)를 재사용**한다 — 여정은 "어떤 화면·action을 어떤 순서로 거치는가"의 계약일 뿐.
> 위치: `model_repo/journeys/JRN-*.yaml`.

---

## 구조

```yaml
schema_version: 1
journey:
  id: JRN-ORDER-REFUND          # 스파인 ID (spine-ids.md)
  name: "주문 환불 여정"
  description: "회원이 주문을 조회해 환불을 완료하기까지"
  actor: member                 # 여정 주체 (permission 맥락)
  version: 1
  preconditions:                # 시작 전 상태
    - "로그인된 회원"
    - "PAID 상태 주문 1건 이상"
  steps:                        # 화면→화면 이동 시퀀스
    - seq: 1
      screen: SCR-LOGIN
      action: REQ-LOGIN.001     # 거치는 action (acceptance 재사용 대상)
      expect: "대시보드로 이동"
    - seq: 2
      screen: SCR-ORDER-LIST
      action: REQ-ORDER-LIST.002
      expect: "주문 목록 표시"
    - seq: 3
      screen: SCR-ORDER-DETAIL
      action: REQ-ORDER-DETAIL.004
      expect: "환불 버튼 노출 (PAID일 때만)"
    - seq: 4
      screen: SCR-ORDER-DETAIL
      action: REQ-ORDER-DETAIL.005
      expect: "환불 완료 → status REFUNDED"
  postconditions:
    - "주문 status = REFUNDED"
    - "EXT-PAYMENT cancel 호출됨"
  data_refs: [ENT-ORDER]        # 여정이 다루는 데이터
  ext_refs: [EXT-PAYMENT]       # 여정이 거치는 외부 연동
  priority: high                # E2E 우선순위 (high/med/low)
```

---

## 집계 규칙 (journey-map 스킬)

1. 모든 `SCR-*.yaml`의 action 중 `outcome.type: navigate`를 수집해 화면 간 간선(edge)을 만든다.
2. 간선을 이어 의미 있는 end-to-end 경로를 여정 후보로 제안 → PO가 확정/명명.
3. **고립 화면 탐지**: 어떤 navigate로도 도달 불가한 SCR-은 경고로 보고.
4. (선택) Mermaid 흐름도 산출로 PO가 전체 화면 흐름을 시각 확인.

## ③ Phase γ 매핑

- `JRN-*` 1개 → Playwright(+BDD) E2E 스펙 1개.
- 각 step → 해당 화면 action의 acceptance(Gherkin) 시나리오를 호출/재사용.
- 커밋: `[E2E/JRN-ORDER-REFUND] ...` (commit-convention.md).
- 추적: `JRN- → (거치는 SCR/action) → e2e-test → commit`.
