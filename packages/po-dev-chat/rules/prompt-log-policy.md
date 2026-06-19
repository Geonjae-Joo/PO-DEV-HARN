<!-- supporting-file: skills/action-interview, skills/note-intake -->
<!-- loaded-by: action-interview Step 6(prompt_log 기록) + note-intake(verbatim 원칙) 시 참조 -->

# Prompt Log Policy — 사용자 발화 적재 규칙

## 핵심 원칙: 하이브리드 적재

| 방식 | 장점 | 단점 |
|---|---|---|
| 전량 적재만 | 완전한 감사 추적, 정보 무손실 | 소비자(spec-generator·개발자)가 모순 발화 더미 직접 해석 |
| compact 요약만 | 소비 효율적 | 뉘앙스 손실, AI 요약 오류 시 원본 소실 |
| **하이브리드 (채택)** | 원문 보존 + 소비 효율 양립 | 저장 구조 2곳 (자동 동기화) |

---

## prompt_log[] — 원문 원장 (append-only)

```yaml
prompt_log:
  - id: PRM-0005
    at: 2026-06-12T10:41:00Z
    author: ubc
    stage: action         # layout | action | revision | note
    text: "엑셀로 전체 다운로드 받는 버튼 하나 추가해줘"
    affected: [CMP-ORDER-LIST.exportBtn, REQ-ORDER-LIST.001]
    applied_version: 8
  - id: PRM-0009
    at: 2026-06-12T11:15:00Z
    author: ubc
    stage: revision
    text: "아 엑셀은 전체 말고 지금 필터된 것만. 그리고 관리자만 보이게"
    affected: [REQ-ORDER-LIST.001]
    applied_version: 9
    supersedes: [PRM-0005]   # 이전 발화를 의미상 대체
```

**규칙:**
- 발화는 절대 수정·삭제하지 않는다.
- 수정 발화는 `supersedes`로 이전 발화를 가리킨다.
- `applied_version`은 이 발화로 만들어진 model version.
- git-backed이므로 저장 비용은 무시 가능.

---

## provenance.intent — 소비용 compact 요약

```yaml
actions:
  - id: REQ-ORDER-LIST.001
    provenance:
      intent: >
        관리자 전용 엑셀 다운로드. 필터 조건 반영.
        처음엔 전체 다운로드 요청이었으나 v9에서 필터 반영으로 변경.
      prompts: [PRM-0005, PRM-0009]
```

**규칙:**
- AI가 해당 action에 연결된 발화들을 종합한 compact 요약.
- 발화가 추가될 때마다 재생성.
- 변경 이력이 의미 있으면 요약 안에 명시 ("처음엔 X였으나 vN에서 Y로 변경").
- **본문은 AI가 재작성 가능** (prompt_log 원문과 달리 요약이 목적).

---

## 소비자별 읽기 규칙

| 소비자 | 읽는 것 | 읽지 않는 것 |
|---|---|---|
| spec-generator | `intent` + `acceptance` + `notes` | prompt_log 원문 더미 |
| 개발자(③) | `intent` + `acceptance` | prompt_log (모호/분쟁 시에만 ref 역추적) |
| 감사/분쟁 | `prompt_log` 전체 원문 | |

---

## 해시 계산 제외 필드

`prompt_log`, `provenance`, `intake`는 screen model의 노드 해시 계산에서 **제외**한다.
이유: 메타데이터 변경이 가짜 Change Order(스파인 diff)를 만들면 안 됨.
해시는 semantic 필드에만: `layout` 구조·props / `actions` behavior·acceptance / `notes` body.
