<!-- rule: 03-SENA-WEB-DEV — 커밋 컨벤션 (commit-spine-id hook이 강제) -->

# Commit Convention

constitution(①)의 하드 룰 6번(커밋 규칙)을 ③에서 구체화한다. `commit-spine-id.py` hook이 강제한다.

## 형식

```
[<SPEC|MOD>/<task>] <요약> (REQ-...)
```

- 예: `[SPEC-014/T1] 주문 목록 조회 API 구현 (REQ-ORDER-LIST.001)`
- 예: `[MOD/T7] OrderList 화면 wiring (REQ-ORDER-LIST.003, REQ-ORDER-LIST.004)`

## 규칙

- 커밋 메시지에 **스파인 ID를 반드시 포함**한다. 없으면 `commit-spine-id.py`가 commit을 차단한다.
- `SPEC-` 은 spec 슬라이스, `MOD` 는 모듈 단위 변경에 사용한다.
- `<task>` 는 T### 태스크 ID.
- 관련 REQ-는 괄호 안에 나열한다(복수 가능).

## prefix 예외

- **Phase α scaffold**: `[SCAFFOLD] <요약>` — tdd-gate는 skip하지만 commit-spine-id는 적용된다.
- **Change Order**: `[CO/<dismiss|amend|regenerate>] <요약> (re-pin v…)`.

## 추적

커밋 ID는 추적 그래프의 종점이다: `SCR → CMP → REQ → acceptance → test → SPEC → task → commit`.
