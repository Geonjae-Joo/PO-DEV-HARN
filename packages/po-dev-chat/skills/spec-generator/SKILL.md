---
name: spec-generator
description: >
  Gate A 통과(status: confirmed) 후 screen model을 도메인 모듈 단위 PACK-* spec 팩으로 분해·발행한다.
  팩은 speckit.specify의 INPUT 번들이며 PO 계약 원문만 담는다.
  PO가 "spec 생성", "팩 발행", "개발자 인계" 를 언급하거나 Gate A 통과 직후 사용.
when_to_use: Gate A 통과 후 spec 팩 발행, "PACK-", "speckit", "개발자 인계" 요청 시.
disable-model-invocation: true
allowed-tools: Read Write Edit Bash
layer: 02-PO-DEV-CHAT
stage: Gate A 후 (핸드오프 ② → ③)
version: 1.0.0
owner: PO (도메인 전문가)
tags: [spec-pack, handoff, vertical-slice, domain-module, manual-only]
supporting-files: [spec-pack-schema.md, scripts/spec-pack-guard.py]
spine-ids: [SPEC-, PACK-, REQ-, CMP-]
---

# Skill: spec-generator

## 역할

Gate A 통과(`status: confirmed`)된 screen model들을 **도메인 모듈 단위 PACK-* spec 팩**으로 분해·발행한다.
팩은 speckit.specify의 INPUT 번들이다. PO 계약 원문만 담는다.
팩 포맷: [spec-pack-schema.md](spec-pack-schema.md)

> **발행 전 필수 가드 (기계 강제).** 팩을 쓰기 전에 반드시 실행한다:
> ```bash
> python skills/spec-generator/scripts/spec-pack-guard.py model_repo/screens/SCR-<...>.yaml
> ```
> exit 1 이면 **팩을 쓰지 않는다.** 검사: ①대상 화면이 모두 `status: confirmed` (draft/review 차단),
> ②action `outcome.target`의 ENT-/EXT- 가 `model_repo/entities|externals/` 에 실존(dangling ref 차단),
> ③화면을 거치는 JRN- 부재 시 경고. confirmed 아닌 화면에서의 발행을 prose가 아니라 코드로 막는다.

---

## 입력

- `model_repo/screens/SCR-*.yaml` — status: confirmed인 화면 전체
- `model_repo/renders/SCR-*.render.html` — 파생 HTML 뷰 (경로 참조용)
- `model_repo/entities/ENT-*.yaml` — action `outcome.target`이 참조하는 개념 데이터 계약
- `model_repo/externals/EXT-*.yaml` — 외부 연동 계약
- `model_repo/journeys/JRN-*.yaml` — 화면 간 E2E 여정 (step.screen이 팩 화면을 거치는 것)

---

## 팩 절단 기준 (3차원)

### 1차: Domain Entity 응집 (가장 중요)

같은 primary entity를 다루는 화면·기능을 하나의 팩으로 묶는다.
speckit.plan이 Entity, Service, Repository를 도메인 전체에 대해 한 번에 설계할 수 있도록.

```
PACK-ORDER:  SCR-ORDER-LIST + SCR-ORDER-DETAIL + SCR-ORDER-CREATE
             (OrderEntity 기반 사용자 플로우 전체)
```

### 2차: Workflow 연결성

navigate로 직접 이동하는 화면들을 함께 묶는다.
navigate target이 없거나 다른 도메인으로 넘어가는 지점이 팩 경계다.

### 3차: Actor 경계

같은 role이 사용하는 화면을 묶는다.
같은 entity라도 actor가 완전히 다르고 API 권한 구조가 달라지면 분리 검토.

```
PACK-ORDER:        user 플로우 (SCR-ORDER-LIST, SCR-ORDER-DETAIL, SCR-ORDER-CREATE)
PACK-ORDER-ADMIN:  admin 전용 (SCR-ADMIN-ORDER-LIST, SCR-ADMIN-ORDER-CANCEL)
```

### 크기 가드레일

| 신호 | 판단 |
|---|---|
| 화면 1개, action 2개 이하 | 너무 작음 → 같은 도메인 팩에 병합 |
| 3개 이상의 무관한 Entity 등장 | 도메인이 다름 → 분리 |
| speckit.tasks 예상 T### 15개 초과 | 너무 큼 → sub-도메인으로 분리 |

최종 크기 결정은 speckit.specify가 한다. 팩은 "묶음 제안"이다.

---

## 팩 구성 규칙

각 화면에서 **이 팩 scope에 해당하는 것만** 추출한다. 전체 screen model을 복사하지 않는다.

**포함**:
- `screens[]`: yaml_ref + render_ref + `pinned_contract`(version·hash·layout_hash·render_hash·git_ref 를 묶은 단일 매핑 — 소비자 speckit-specify가 읽는 키)

> **pinned_contract 핀은 손으로 쓰지 않는다 (결정론적 계산 위임, ADR-002 D5).** `layout_hash`·`render_hash`·`version` 은 LLM이 추측해 쓰지 말고, `pins.py` 단일 출처로 계산해 채운다:
> ```bash
> python skills/spec-generator/scripts/spec-pack-guard.py --write-pins model_repo/specs/PACK-<...>/spec-pack.yaml
> ```
> 발행 전 검증 시 같은 가드가 `compute_pins` 로 재계산해 대조한다 — 핀 불일치(stale)면 error로 차단, placeholder/누락이면 `--write-pins` 안내 warn.
- `scope`: 이 팩에 속하는 REQ-/CMP- ID 목록
- `entities[]`: scope actions의 `outcome.target` 중 ENT- 를 모아 ref(`model_repo/entities/ENT-*.yaml`)로 등록 (복사 아님)
- `externals[]`: outcome.target / EXT 참조 중 EXT- 를 ref(`model_repo/externals/EXT-*.yaml`)로 등록
- `journeys[]`: steps[].screen 이 이 팩 화면을 1개라도 거치는 JRN- 을 ref(`model_repo/journeys/JRN-*.yaml`)로 등록 — ③ Phase γ E2E 원천
- `actions`: scope의 actions + acceptance **원문 그대로**
- `notes`: scope 컴포넌트 관련 notes **원문 그대로** (verbatim 보존, complexity 포함)
- `open_items`: 해당 컴포넌트의 deferred 항목 원문

**미포함** (speckit이 생성):
- ERD, API 설계, Data Model
- bl-analyst decision_table (speckit.plan 중 생성)
- T### task 목록
- impl 힌트, test scope

---

## bl-analyst 처리

`complexity: high` 노트를 그대로 팩에 포함한다.
bl-analyst 호출은 **speckit.plan 단계**에서 일어난다. spec-generator는 호출하지 않는다.

---

## 산출물 위치

```
model_repo/specs/
  P