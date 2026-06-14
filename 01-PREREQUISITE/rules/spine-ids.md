# Spine IDs — 스파인 ID 채번 규칙

전 레이어 공통 적용. 모든 아티팩트는 스파인 ID를 가진다.
추적 그래프: `SCR → CMP → REQ → PACK → task → test → commit`

---

## ID 접두사 체계

| 접두사 | 대상 | 예시 | 채번 주체 |
|---|---|---|---|
| `DP-` | design page 템플릿 | `DP-MAIN`, `DP-POPUP` | ① |
| `SCR-` | 화면(screen model) | `SCR-ORDER-LIST` | ② |
| `CMP-` | 컴포넌트 인스턴스 | `CMP-ORDER-LIST.exportBtn` | ② |
| `REQ-` | 요구사항(action) | `REQ-ORDER-LIST.001` | ② |
| `NOTE-` | 노트 | `NOTE-ORDER-LIST.001` | ② |
| `NFR-` | 비기능 요구사항 | `NFR-ORDER-LIST.001` | ② |
| `Q-` | HITL 질문 | `Q-001` | ② |
| `PRM-` | prompt log 항목 | `PRM-0001` | ② |
| `PACK-` | spec 팩(도메인 모듈) | `PACK-ORDER`, `PACK-AUTH` | ② |
| `T` | 태스크(3자리) | `T001`, `T012` | ③ |

---

## 형식 규칙

### SCR-
```
SCR-{도메인}-{화면타입}
예: SCR-ORDER-LIST / SCR-ORDER-DETAIL / SCR-ADMIN-ORDER / SCR-LOGIN
```
화면타입: LIST | DETAIL | CREATE | EDIT | ADMIN | DASHBOARD | POPUP | WIZARD

### CMP-
```
CMP-{SCR도메인+타입}.{컴포넌트역할camelCase}
예: CMP-ORDER-LIST.exportBtn / CMP-ORDER-LIST.filterbar / CMP-ORDER-LIST.table
```
동일 DS 컴포넌트를 같은 화면에서 여러 번 사용 시 숫자 접미사: `.filterbar1`, `.filterbar2`

### REQ- / NOTE- / NFR-
```
REQ-{SCR도메인+타입}.{3자리 순번}
예: REQ-ORDER-LIST.001 / NOTE-ORDER-LIST.001 / NFR-ORDER-LIST.001
```
삭제 시 결번 유지(재사용 금지).

### PACK-
```
PACK-{도메인}[-{액터}]
예: PACK-ORDER / PACK-ORDER-ADMIN / PACK-MEMBER / PACK-AUTH / PACK-DASHBOARD
```
Actor가 달라 API 권한 구조가 다를 때만 접미사 추가.

### T (Task)
```
T{3자리 순번} — 팩 내 순번
T001: [TEST] ExportService 단위 테스트
T002: [IMPL] ExportService 구현
```
테스트 태스크(T###)와 구현 태스크(T###)는 같은 번호 체계. 접두사 [TEST]/[IMPL]로 구분.

### DP-
```
DP-{페이지타입}[-{변형}]
DP-MAIN / DP-POPUP / DP-LIST / DP-DETAIL / DP-FORM / DP-WIZARD
```

---

## 불변 원칙

1. **결번 유지**: 삭제된 ID는 재사용하지 않는다.
2. **전역 유일**: 같은 접두사 내에서 중복 금지.
3. **자동 채번 금지**: AI가 임의로 ID를 발명하지 않는다. link-manifest.yaml의 다음 번호를 참조한다.
4. **커밋에 포함**: 모든 커밋 메시지에 관련 스파인 ID가 포함되어야 한다.
5. **해시 제외 필드**: prompt_log, provenance, intake는 해시 계산에서 제외. 해시는 semantic 필드만(layout·actions·notes body).
