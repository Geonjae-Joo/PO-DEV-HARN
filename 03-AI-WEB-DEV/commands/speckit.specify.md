# Command: /speckit.specify

## 목적

PACK-* spec 팩의 **scope를 확인·확정**한다. Phase β 각 반복의 시작점이며, Phase 0에서는
SPEC-000 scope 확인 + 기능별 전달 모드(A/B) 결정에도 사용한다.

## 실행 조건

- `input/spec-pack/PACK-X/` 에 ②가 발행한 spec 팩이 존재 (Phase β)
- 또는 `input/harness/` 에 SPEC-000 명세 존재 (Phase 0)

## 입력

```
input/spec-pack/PACK-X/spec.yaml      # screens(yaml_ref·render_ref·pinned_contract) + scope + actions + notes + open_items
input/spec-pack/PACK-X/renders-ref.txt
```

## 실행 절차

1. 팩 `scope` 확인 — 묶인 화면(SCR-*), REQ-/CMP- 범위, actor·entity 경계를 읽는다.
2. **크기 판정** — 너무 크면(예상 T### 15개 초과, 무관한 Entity 3개 이상) **sub-pack으로 재분할**한다.
3. `open_items`의 **deferred 항목 처리 방향** 결정 — 이번 팩에서 다룰지, 보류할지, ②에 질의할지.
4. **pinned_contract 확인** — 각 화면이 고정된 계약 버전(version·hash·git_ref) 위에서 작업하는지 확인(Pin).
5. 확정된 scope를 다음 단계(`/speckit.plan`)로 넘긴다.

## Phase 0 전용 절차

- SPEC-000의 공통 기능 목록을 확인하고, 각 기능에 **전달 모드(A/B)** 를 지정한다.
  - 판정: "프로젝트마다 변형되나?" → 예면 A(가이드), 아니면 B(직접 주입).
- 결정을 `app_repo/baseline-delivery-manifest.yaml` 에 `기능 → mode:A|B + 사유` 로 기록한다.

## 산출물

- 확정된 팩 scope (sub-pack 분할 결과 포함)
- (Phase 0) `baseline-delivery-manifest.yaml`

## 경계

- 이 명령은 **scope를 확정**할 뿐, 새 계약(화면·요구사항)을 만들지 않는다 — 정의는 ②의 책임.
- scope를 넘어선 요구가 보이면 Change Order로 ②에 되돌린다.
