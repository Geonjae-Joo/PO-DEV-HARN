<!-- rule: 03-SENA-WEB-DEV — Gate B (개발자 소유) -->

# Gate B Checklist

Phase β에서 `/speckit.tasks` 완료 후, **구현(`/speckit.implement`) 시작 전**에 통과해야 하는 관문.
개발자가 소유한다. PI는 acceptance에 대한 **비차단 소프트 리뷰**만 한다.

## 통과 조건 (전부 충족)

1. **Data Model 확정** — 팩 도메인의 엔티티·필드·관계·제약이 빠짐없이 정의됨.
2. **ERD 확정** — 엔티티 간 관계가 다이어그램으로 정리됨.
3. **API 설계 확정** — endpoint, request/response, 권한(actor·role)별 접근이 명세됨.
4. **BL 해소** — `complexity: high` 노트가 bl-analyst의 decision table·state machine으로
   구조화되고 **open decision이 0개**.
5. **Task 확정** — T### 목록이 test-first로 정렬되고, 각 구현 태스크에 대응 테스트 태스크 존재.
6. **개발자 approve** — 위 항목을 개발자가 검토·승인.

## 차단 규칙

- bl-analyst **미해결 항목이 1개라도 있으면 통과 불가**.
- 테스트 태스크 없는 구현 태스크가 있으면 통과 불가(TDD 강제).
- approve 전에는 어떤 구현 커밋도 허용하지 않는다.

## PI 소프트 리뷰 (비차단)

- PI는 acceptance가 의도와 맞는지 확인할 수 있으나, 이 리뷰는 **Gate B를 막지 못한다**.
- 의도 불일치가 크면 Change Order로 ②에 되돌린다(구현 전이므로 비용 최소).
