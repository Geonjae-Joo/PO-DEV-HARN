---
name: external-intake
description: >
  화면 action이 의존하는 외부 연동 시스템(EXT-*)을 계약으로 수집·정의한다.
  엔드포인트 목적·인증 방식·장애 처리 규약까지만 — 실제 URL·시크릿·어댑터 코드는 만들지 않는다(③의 몫).
  결제·SSO·알림·외부 LLM(Fabrix) 등 외부 시스템 연동이 action에 등장할 때 사용.
when_to_use: '"결제 시스템 연동", "외부 API", "SSO", "문자/메일 발송", outcome.target에 미정의 EXT- 참조 발생 시.'
allowed-tools: Read Write Edit
layer: ② PO-DEV-CHAT
stage: Stage 2.5 (action-interview 중/후, 외부 의존 식별 시)
version: 1.0.0
owner: PO (도메인 전문가)
tags: [external-system, integration-contract, EXT]
supporting-files: [../../rules/data-contract-schema.md]
spine-ids: [EXT-]
---

# Skill: external-intake

## 역할

action이 의존하는 외부 시스템을 **연동 계약(EXT-*.yaml)**으로 정의한다.
*무엇을 위해 어떤 호출을, 어떤 인증으로, 실패하면 어떻게*까지의 규약을 모은다.

**경계(중요):** 실제 baseURL·시크릿 값·SDK·재시도 라이브러리 코드는 **만들지 않는다.** ③ Phase β 어댑터가 이 계약에서 구현한다. 시크릿/URL은 ops(SPEC-OPS-000)로 주입.

---

## 트리거 & 흐름

```
action-interview/note-intake에서 외부 시스템 의존 발견
  → outcome.target 또는 note(kind: external_system)로 EXT- 식별
  → EXT- 가 model_repo/externals/ 에 없으면 이 스킬 진입
  │
  ▼
1. 명명: EXT-{시스템명}  (link-manifest 다음 번호, 임의 채번 금지)
2. 목적·프로토콜(REST/gRPC/MQ 등)
3. 엔드포인트 순회: 이름 + 목적 + 방향(inbound/outbound)
4. 인증 방식(api-key/oauth2/mTLS/jwt) — 값이 아니라 *방식*만
5. 장애 처리: timeout / on_error / 멱등성
6. 주고받는 ENT- (data_refs)
7. data-contract-schema.md 형식으로 model_repo/externals/EXT-*.yaml 저장
```

## 질문 가이드 (규약 수준만)

```
Q-EXT-PURPOSE:  이 외부 시스템으로 무엇을 하나요?
Q-EXT-CALLS:    어떤 동작들을 호출하나요? (승인/취소/조회 등)
Q-EXT-AUTH:     어떻게 인증하나요? (키 / OAuth / 인증서)
Q-EXT-FAIL:     호출이 실패하면 사용자에게 무엇을 보여주고, 데이터는 어떻게 하나요?
Q-EXT-IDEM:     같은 요청이 두 번 가면 안 되는 동작이 있나요? (멱등성)
```

## 산출 & 검증

- 산출: `model_repo/externals/EXT-*.yaml` (data-contract-schema.md 준수)
- 검증: action의 `outcome.target`/note 참조와 ID 일치 / data_refs의 ENT- 실존
- Gate A 전: 참조된 모든 EXT-가 정의·확정 (미정의 시 sufficiency-check gap)
