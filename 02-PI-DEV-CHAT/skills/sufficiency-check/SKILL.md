---
name: sufficiency-check
description: >
  Stage 4 스킬. sufficiency-check.py(기계 체크)를 실행한 뒤 AI gap 분석으로
  의미적 누락을 찾아 open_questions를 생성한다. Gate A 진입 판정.
  PI가 "충분한가?", "Gate A", "spec 준비됐나?" 를 언급하거나 Stage 3 완료 시 사용.
when_to_use: >
  Stage 3 완료 후 sufficiency 판정 요청 시.
  "Gate A", "충분성 확인", "스펙 준비", "open question" 언급 시.
allowed-tools: Read Write Edit Bash
layer: 02-PI-DEV-CHAT
stage: Stage 4
version: 1.0.0
owner: PI (도메인 전문가)
tags: [sufficiency, gap-analysis, open-question, gate-a, readiness]
supporting-files: [scripts/sufficiency-check.py, ../../rules/spec-readiness-checklist.md]
spine-ids: [REQ-]
---

# Skill: sufficiency-check

## 실행 순서

이 스킬이 로드되면:

1. **기계 체크 실행**
```bash
python3 skills/sufficiency-check/scripts/sufficiency-check.py model_repo/screens/SCR-*.yaml
```
결과 JSON을 stdout으로 받아 `sufficiency`, `error_count`, `warn_count`, `results` 파싱.

2. **AI gap 분석** — 아래 범위에서 의미적 누락 탐지

3. **open_questions 생성** → HITL 재질문 → Gate A 판정

---

## 역할 (Stage 4 — AI gap 분석)

기계 체크 완료 후, AI가 **spec 작성 관점에서 의미적 누락**을 찾아 open_questions를 생성한다.

스크립트와 AI는 **같은 spec-readiness-checklist.md**를 기준으로 하되:

> 체크리스트: [spec-readiness-checklist.md](../../rules/spec-readiness-checklist.md)
- 스크립트: "필드가 존재하는가" (결정론)
- AI: "내용이 충분한가" (의미론)

---

## AI gap 분석 범위

### 1. Action 완전성
- navigate action이 있는데 target SCR-가 screen model에 없거나 계획에 없음
- mutate action이 있는데 성공/실패 후 동작이 미정의
- 목록 화면에 조회 action이 있는데 페이징·정렬 언급이 없음
- 삭제 action이 있는데 확인 절차(팝업 등) 언급이 없음

### 2. Data 완전성
- 화면에 표시되는 필드가 있는데 어느 Entity에서 오는지 불명확
- 외부 API/시스템 의존성이 있는데 EXT- 참조가 없음
- 계산 필드가 있는데 계산 방식이 미정의

### 3. UX 완전성
- 비동기 작업(export, 대용량 조회)이 있는데 loading 상태 미정의
- 에러 발생 시 사용자 피드백 방법이 미정의
- 모바일/반응형 요구사항 언급 없음 (nfr notes 유도)

### 4. 권한 완전성
- 화면 레벨 접근 권한이 정의되지 않음
- `action.permission`이 `screen.permission`보다 더 넓음 (예: screen=admin, action=all) → **error** (역할 체계 붕괴)
- `action.permission != all`인데 `error_behavior.permission_denied`가 미정의 → warn

### 5. error_behavior 완전성
- `outcome.type: mutate` / `export` / `query` action인데 `error_behavior`가 없음 → **error**
- `error_behavior`가 있지만 `default` 케이스만 있고 `network_fail`이 없음 → warn

### 6. reactive / initial_state 완전성
- 화면에 list / DataTable 컴포넌트가 있는데 `screen.initial_state`가 미정의 → **error**
- FilterBar 등 필터 컴포넌트와 DataTable이 함께 있는데 `reactive`가 없음 → warn (필터 변경 시 갱신 여부 불명확)

### 7. NFR 구조화
- `kind: nfr`인 note가 있는데 `nfr_detail`이 없음 → warn (open_question 생성: "동시 접속자 수 / 응답 목표 / 우선순위")

---

## open_question 생성 형식

```yaml
intake:
  open_questions:
    - id: Q-{다음번호}
      target: {CMP-... | screen}
      ask: "{구체적이고 답하기 쉬운 질문}"
      reason: "{spec-readiness-checklist의 항목 ID}"
      status: open
```

질문은 명확하고 답하기 쉬워야 한다:
- ❌ "이 화면의 NFR을 정의해 주세요."
- ✓ "이 화면은 몇 명이 동시에 사용하나요? 응답 속도 요구사항이 있나요?"

---

## HITL 재질문 프로세스

1. open_questions 생성 후 사용자에게 제시.
2. 사용자가 답변하면:
   - `status: answered`
   - `answer_ref: PRM-{새 발화 ID}`
   - 관련 action/note에 정보 반영 (patch)
3. 사용자가 보류하면:
   - `status: deferred`
   - `defer_reason` 필수 (이유를 적어야 보류 가능)
   - deferred 항목은 spec 팩에 그대로 포함되어 ③으로 전달됨
4. 모든 질문이 answered 또는 deferred → sufficiency 재평가.

---

## sufficiency 판정

```
error 항목 미충족 → sufficiency: fail → Gate A 차단
warn 항목 미충족(deferred) → sufficiency: pass_with_deferred → Gate A 가능 (팩에 포함)
모두 pass → sufficiency: pass → Gate A 가능
```
