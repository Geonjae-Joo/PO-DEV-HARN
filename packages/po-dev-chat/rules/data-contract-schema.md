<!-- supporting-file: skills/entity-intake, skills/external-intake, skills/sufficiency-check, skills/spec-generator -->
<!-- loaded-by: entity-intake·external-intake 스킬이 작성 시, sufficiency-check가 ENT-/EXT- 참조 검증 시, spec-generator가 팩 구성 시 참조 -->

# Data Contract Schema — ENT-*.yaml / EXT-*.yaml

> screen model(SCR-*.yaml)의 action `outcome.target`이 참조하는 **데이터/외부 계약의 단일 진실원**.
> **경계:** ②는 *개념 계약*까지만 만든다 — 의미·핵심 속성·관계·연동 규약. **물리 설계(컬럼 타입·테이블·인덱스·DDL·실제 어댑터 코드)는 ③ Phase β가 이 계약에서 *파생*한다.** (spec-kit의 "Key Entities(spec) → data-model.md(plan)" 분리와 동일 철학.)
> 위치: `model_repo/entities/ENT-*.yaml`, `model_repo/externals/EXT-*.yaml`.

---

## 1. ENT- (개념 데이터 엔티티)

```yaml
schema_version: 1
entity:
  id: ENT-ORDER                # 스파인 ID (spine-ids.md)
  name: "주문"
  description: "고객이 생성한 주문 1건"   # 무엇을 의미하는가 (WHAT/WHY, HOW 아님)
  owner_screens: [SCR-ORDER-LIST, SCR-ORDER-DETAIL]  # 이 엔티티를 다루는 화면
  version: 1
  attributes:                  # 핵심 속성 — 개념 수준 (물리 타입 아님)
    - name: orderId
      meaning: "주문 식별자"
      kind: identifier         # identifier | value | reference | derived
      required: true
    - name: status
      meaning: "주문 상태"
      kind: value
      enum: [PLACED, PAID, SHIPPED, REFUNDED]   # 개념 enum (선택)
      required: true
    - name: member
      meaning: "주문한 회원"
      kind: reference
      ref: ENT-MEMBER          # 관계는 ref로 표현
      cardinality: many-to-one # one-to-one | one-to-many | many-to-one | many-to-many
  relationships:               # 관계 요약 (attributes.ref와 중복 가능, 가독용)
    - to: ENT-MEMBER
      kind: many-to-one
      meaning: "한 회원이 여러 주문"
  identity: [orderId]          # 자연키/식별 속성
  notes:                       # PO verbatim 보충 (note-intake와 동일 정신, 선택)
    - "환불은 PAID 이후에만 가능"
```

**금지(③의 몫):** 컬럼 SQL 타입, 길이, 인덱스, FK 제약 DDL, 마이그레이션, ORM 매핑.

## 2. EXT- (외부 연동 시스템)

```yaml
schema_version: 1
external:
  id: EXT-PAYMENT              # 스파인 ID
  name: "결제 게이트웨이"
  description: "주문 결제 승인/취소 처리 외부 시스템"
  used_by_screens: [SCR-ORDER-DETAIL]
  version: 1
  protocol: REST              # REST | gRPC | GraphQL | SOAP | message-queue
  endpoints:                  # 개념 수준 — 실제 baseURL/시크릿은 ③/ops
    - name: approve
      purpose: "결제 승인"
      direction: outbound
    - name: cancel
      purpose: "결제 취소/환불"
      direction: outbound
  auth:
    kind: api-key             # api-key | oauth2 | mTLS | jwt | none
    note: "키는 ops 시크릿으로 주입 (평문 금지)"
  failure_policy:             # 장애 처리 — ③ 어댑터가 구현
    timeout: "5초"
    on_error: "재시도 1회 후 사용자에게 실패 안내 + 주문 상태 유지"
    idempotency: "approve는 orderId 기준 멱등"
  data_refs: [ENT-ORDER]      # 주고받는 데이터 엔티티
```

**금지(③의 몫):** 실제 URL·시크릿 값, SDK 코드, 재시도 라이브러리 구현.

---

## 3. 검증 (sufficiency-check 연동)

- action의 `outcome.type ∈ {query, mutate, export}`이면 `outcome.target`이 `ENT-`/`EXT-` 형식이어야 한다 — **현재 구현됨**(`sufficiency-check.py` CHK-ACT-DATASOURCE).
- (목표) 참조된 모든 `ENT-`/`EXT-` ID는 `model_repo/entities|externals/`에 **실존**해야 한다 — 실존 교차검증은 sufficiency-check 확장 backlog.
- Gate A 전 모든 참조 엔티티/외부가 정의·확정되는 것을 권장한다.
