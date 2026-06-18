---
name: entity-intake
description: >
  화면 action이 참조하는 개념 데이터 엔티티(ENT-*)를 계약으로 수집·정의한다.
  의미·핵심 속성·관계까지만 — 물리 타입·테이블·DDL은 만들지 않는다(③ Phase β의 몫).
  action-interview에서 outcome.target으로 ENT-가 등장하거나, PO가 "데이터", "엔티티", "테이블 항목"을 언급할 때 사용.
when_to_use: '"이 데이터는 무엇무엇으로 구성", "주문 항목", "회원 정보 필드", outcome.target에 미정의 ENT- 참조 발생 시.'
allowed-tools: Read Write Edit
layer: 02-PO-DEV-CHAT
stage: Stage 2.5 (action-interview 중/후, 데이터 출처 식별 시)
version: 1.0.0
owner: PO (도메인 전문가)
tags: [entity, data-contract, ENT]
supporting-files: [../../rules/data-contract-schema.md]
spine-ids: [ENT-]
---

# Skill: entity-intake

## 역할

action의 `outcome.target`이 가리키는 데이터를 **개념 엔티티 계약(ENT-*.yaml)**으로 정의한다.
spec-kit의 "Key Entities"(spec 단계)에 해당 — *무엇을 의미하고 어떤 핵심 속성·관계를 갖는가*까지만 모은다.

**경계(중요):** 물리 컬럼 타입·길이·인덱스·FK DDL·마이그레이션·ORM 매핑은 **만들지 않는다.** 그것은 ③ Phase β가 이 계약에서 파생한다.

---

## 트리거 & 흐름

```
action-interview Step에서 outcome.type ∈ {query, mutate, export} 발견
  → outcome.target 으로 ENT-/EXT- 식별 필요 (sufficiency-check CHK-ACT-DATASOURCE)
  → ENT- 가 model_repo/entities/ 에 없으면 이 스킬 진입
  │
  ▼
1. 엔티티 명명: ENT-{도메인}  (link-manifest 다음 번호 확인, 임의 채번 금지)
2. 의미 수집: "이 데이터는 무엇을 나타내나요? 한 건이 의미하는 게 뭔가요?"
3. 핵심 속성 순회: 이름 + 의미 + kind(identifier|value|reference|derived) + 필수 여부
   - reference면 어떤 ENT-와 어떤 관계(cardinality)인지
4. 관계 요약 + 식별 속성(identity)
5. data-contract-schema.md 형식으로 model_repo/entities/ENT-*.yaml 저장
```

## 질문 가이드 (개념 수준만)

```
Q-ENT-MEANING:  이 데이터 한 건은 무엇을 의미하나요?
Q-ENT-ATTR:     꼭 있어야 하는 항목들은 무엇인가요? (각 항목이 뭘 뜻하는지)
Q-ENT-ID:       이 데이터를 무엇으로 구분하나요? (식별자)
Q-ENT-REL:      다른 데이터(회원, 상품 등)와 어떻게 연결되나요? (1:N 등)
Q-ENT-ENUM:     상태/구분 값이 정해져 있나요? (PLACED/PAID 등)
```

> 물리 타입을 물어보고 싶어도 묻지 않는다. "문자열인가요 숫자인가요?"는 ③ Phase β plan의 질문이다.

## 산출 & 검증

- 산출: `model_repo/entities/ENT-*.yaml` (data-contract-schema.md 준수)
- 검증: 참조하는 action의 `outcome.target`과 ID 일치 / 관계 ref가 실존 ENT- 가리키는지
- Gate A 전: action이 참조하는 모든 ENT-가 정의·확정되어야 통과 (미정의 시 sufficiency-check gap)
