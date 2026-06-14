---
name: spec-generator
description: >
  Gate A 통과(status: confirmed) 후 screen model을 도메인 모듈 단위 PACK-* spec 팩으로 분해·발행한다.
  팩은 speckit.specify의 INPUT 번들이며 PI 계약 원문만 담는다.
  PI가 "spec 생성", "팩 발행", "개발자 인계" 를 언급하거나 Gate A 통과 직후 사용.
when_to_use: Gate A 통과 후 spec 팩 발행, "PACK-", "speckit", "개발자 인계" 요청 시.
disable-model-invocation: true
allowed-tools: Read Write Edit Bash
layer: 02-PI-DEV-CHAT
stage: Gate A 후 (핸드오프 ② → ③)
version: 1.0.0
owner: PI (도메인 전문가)
tags: [spec-pack, handoff, vertical-slice, domain-module, manual-only]
supporting-files: [spec-pack-schema.md]
spine-ids: [SPEC-, PACK-, REQ-, CMP-]
---

# Skill: spec-generator

## 역할

Gate A 통과(`status: confirmed`)된 screen model들을 **도메인 모듈 단위 PACK-* spec 팩**으로 분해·발행한다.
팩은 speckit.specify의 INPUT 번들이다. PI 계약 원문만 담는다.
팩 포맷: [spec-pack-schema.md](spec-pack-schema.md)

---

## 입력

- `model_repo/screens/SCR-*.yaml` — status: confirmed인 화면 전체
- `model_repo/renders/SCR-*.render.html` — 파생 HTML 뷰 (경로 참조용)

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
- `screens[]`: yaml_ref + render_ref + pinned_contract (version·hash·git_ref)
- `scope`: 이 팩에 속하는 REQ-/CMP- ID 목록
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
  PACK-ORDER/
    spec.yaml
    renders-ref.txt    # "model_repo/renders/SCR-ORDER-LIST.render.html" 등 경로 목록
  PACK-ORDER-ADMIN/
    spec.yaml
    renders-ref.txt
  PACK-MEMBER/
    spec.yaml
    renders-ref.txt
```

생성 후 `app_repo/specs/`로 동기화 (manifest-sync hook).

---

## shell_ref 필드

Phase α(speckit.scaffold) 실행 전에는 `shell_ref` 가 없다.
speckit.scaffold 실행 후 shell 컴포넌트가 생성되면 `spec.yaml`의 `screens[].shell_ref`를 업데이트한다.
(manifest-sync hook이 자동 처리)
