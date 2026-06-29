<!-- rule: ③ AI-WEB-DEV — 커밋 컨벤션 (commit-spine-id hook이 강제) -->

# Commit Convention

constitution(①)의 하드 룰 6번(커밋 규칙)을 ③에서 구체화한다. `commit-spine-id.py` hook이 강제한다.

## 형식

```
[<PACK|SPEC|MOD>/<task>] <요약> (REQ-...)
```

- 예: `[PACK-ORDER/T001] 주문 목록 조회 API 구현 (REQ-ORDER-LIST.001)`
- 예: `[SPEC-000/T003] JWT 인증 필터 구현 (baseline)`
- 예: `[SPEC-OPS-000/T002] GitHub Actions CI 파이프라인 구성 (ops baseline)`
- 예: `[MOD/T007] OrderList 화면 wiring (REQ-ORDER-LIST.003, REQ-ORDER-LIST.004)`

## 규칙

- 커밋 메시지에 **스파인 ID를 반드시 포함**한다. 없으면 `commit-spine-id.py`가 commit을 차단한다.
- `PACK-` 은 ②가 발행한 도메인 spec 팩(`PACK-ORDER` 등), `SPEC-` 은 플랫폼/baseline spec(`SPEC-000`, `SPEC-OPS-000`), `MOD` 는 모듈 단위 변경에 사용한다.
- `<task>` 는 T### 태스크 ID(3자리 권장: `T001`).
- 관련 REQ-는 괄호 안에 나열한다(복수 가능). baseline 작업처럼 REQ-가 없는 경우 `(baseline)` 등 사유 표기.

## prefix 예외

- **Phase α scaffold**: `[SCAFFOLD] <요약>` — tdd-gate는 skip하지만 commit-spine-id는 적용된다.
- **Change Order**: `[CO/<dismiss|amend|regenerate>] <요약> (re-pin v…)`.
- **E2E 여정 (Phase γ)**: `[E2E/JRN-…] <요약>` — JRN-가 스파인 ID 역할. 예: `[E2E/JRN-ORDER-REFUND] 환불 여정 Playwright 시나리오`.

## 추적

커밋 ID는 추적 그래프의 종점이다: `SCR → CMP → REQ → acceptance → PACK → task → test → commit`.
