---
name: gate-a-check
description: >
  Gate A 종합 판정 스킬. lint error 0 + sufficiency pass + 전 action user_confirmed + PO 승인을
  확인하고 통과 시 status: confirmed로 전환한다.
  PO가 "확정", "confirm", "Gate A", "승인" 을 명시적으로 요청할 때만 실행.
when_to_use: PO가 화면 정의를 확정하고 개발로 넘기겠다고 명시적으로 요청할 때.
disable-model-invocation: true
allowed-tools: Bash Read Write
layer: 02-PO-DEV-CHAT
stage: Gate A
version: 1.0.0
owner: PO (도메인 전문가)
tags: [gate-a, confirm, status-transition, optimistic-lock, manual-only]
supporting-files: [scripts/gate-a-check.py, ../../rules/state-machine.md]
spine-ids: [SCR-, REQ-]
---

## Gate A 실행 절차

PO가 확정을 요청하면:

1. **5가지 조건 종합 판정 스크립트 실행**
```bash
python3 skills/gate-a-check/scripts/gate-a-check.py model_repo/screens/SCR-*.yaml --pi-approved
```

2. **통과 시** — `status: confirmed` + `version` 고정 + git commit 권장
3. **차단 시** — stderr에 출력된 미충족 조건을 PO에게 제시하고 해소 요청

---

## Gate A 통과 조건 (AND)

| 조건 | 체크 방법 |
|---|---|
| lint L1~L4 error 0 | on-save-lint-L1-L4.py 재실행 |
| sufficiency pass 또는 pass_with_deferred | sufficiency-check.py 재실행 |
| 모든 action status: user_confirmed | YAML 직접 확인 |
| open_questions: open 항목 0개 | deferred는 defer_reason 필수 |
| PO 명시적 승인 | --pi-approved 플래그 |
| 전역 스파인 ID 유일성 | harness-core/lib/spine_ledger.py (link-manifest 원장 기준 중복 차단) |

> 상태 전환 규칙: [state-machine.md](../../rules/state-machine.md)

---

## 확정 후

- `model_repo/screens/SCR-*.yaml` → `status: confirmed`, `confirmed_at` 기록
- `spec-generator` 스킬로 PACK-* 팩 발행 가능 상태
- 이후 수정은 Change Order 프로세스 경유
