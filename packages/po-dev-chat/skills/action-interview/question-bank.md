<!-- supporting-file: skills/action-interview -->
<!-- loaded-by: action-interview 스킬이 Step 2(질문 선택) 시 참조 -->

# Question Bank — Stage 2 Action Interview 질문 뱅크

action-interview skill이 Stage 2에서 컴포넌트를 순회하며 사용하는 표준 질문 목록.
archetype과 outcome.type에 따라 적절한 질문을 선택한다.

---

## 화면 레벨 질문 (컴포넌트 루프 시작 전 — 1회만)

컴포넌트 인터뷰를 시작하기 전에 화면 전체에 대한 3가지를 먼저 확인한다.

```
Q-SCREEN-PERM:
  이 화면은 누구나 들어올 수 있나요, 아니면 특정 사용자만 볼 수 있나요?
  예: 로그인 필수 / 관리자만 / 담당 팀원만 / 누구나
  → screen.permission 필드에 저장

Q-INIT-STATE:
  이 화면에 처음 들어왔을 때 자동으로 보여줄 데이터가 있나요?
  - 목록이 자동으로 불러와지나요? (auto_query: true/false)
  - 기본으로 적용되는 필터 조건이 있나요? (default_filter)
  - 이전 화면에서 선택한 항목 정보를 받아야 하나요? (preloaded_from, params)
  → screen.initial_state 필드에 저장

Q-SCREEN-CHANGE-ORDER: (status: confirmed 이후에만)
  이 화면에서 수정하고 싶은 내용이 있나요?
  어떤 부분을 왜 바꾸고 싶은지 말씀해 주세요.
  → gate-a-check 스킬의 change-order 플로우로 전달
```

---

## 공통 질문 (모든 interactive 컴포넌트)

```
Q-TRIGGER:  이 {컴포넌트}를 {어떻게} 하면 무슨 일이 일어나야 하나요?
Q-OUTCOME:  그 결과로 사용자에게 무엇이 보이거나 바뀌어야 하나요?
Q-DATA:     이 동작에서 사용하거나 변경하는 데이터는 무엇인가요? (어디서 오는 데이터인가요?)
Q-PERM:     이 기능은 누구나 사용할 수 있나요, 아니면 특정 역할만 가능한가요?
Q-ERROR:    이 동작이 실패하면 어떻게 되어야 하나요?
            - 네트워크 오류면? (재시도 버튼 / 메시지만)
            - 권한이 없으면? (버튼 숨김 / 접근 차단 / 안내 메시지)
            - 서버 에러면? (롤백 / 부분 성공 처리)
            → action.error_behavior 필드에 케이스별 저장
```

---

## outcome.type별 추가 질문

### navigate (화면 이동)
```
Q-NAV-TARGET:  어느 화면으로 이동하나요? 이동 시 전달해야 할 데이터(파라미터)가 있나요?
Q-NAV-COND:    이동 전에 검증이나 확인이 필요한가요? (저장 후 이동, 확인 팝업 등)
```

### query (데이터 조회)
```
Q-QUERY-FILTER: 조회 조건(필터)은 무엇인가요? 기본값은 무엇인가요?
Q-QUERY-SORT:   기본 정렬 순서는 무엇인가요? 사용자가 정렬을 바꿀 수 있나요?
Q-QUERY-PAGE:   페이징이 필요한가요? 한 페이지에 몇 건을 보여줘야 하나요?
Q-QUERY-EMPTY:  조회 결과가 0건일 때 무엇을 보여줘야 하나요?
Q-QUERY-LOAD:   화면 진입 시 자동으로 조회하나요, 아니면 버튼을 눌러야 하나요?
Q-REACTIVE:     다른 컴포넌트(필터, 탭, 드롭다운 등)가 바뀔 때 이 목록/차트가 자동으로
                갱신되어야 하나요? 어떤 컴포넌트가 바뀔 때 갱신되나요?
                → layout[].reactive.requery_on 필드에 저장
```

### mutate (데이터 생성/수정/삭제)
```
Q-MUTATE-CONFIRM: 실행 전에 확인이 필요한가요? ("정말 삭제하시겠습니까?")
Q-MUTATE-RESULT:  성공 후 어떻게 되나요? (같은 화면 유지 / 목록으로 이동 / 알림 표시)
Q-MUTATE-VALID:   입력값 검증 규칙은 무엇인가요? (필수 항목, 형식, 범위)
Q-MUTATE-PARTIAL: 일부만 실패하는 경우(배치 처리 등)는 어떻게 처리하나요?
Q-MUTATE-AUDIT:   이 변경을 감사 로그로 남겨야 하나요?
```

### export (파일 내보내기)
```
Q-EXPORT-SCOPE:   어떤 데이터를 내보내나요? 현재 필터 조건을 반영하나요?
Q-EXPORT-FORMAT:  파일 형식은 무엇인가요? (xlsx / csv / pdf)
Q-EXPORT-COLS:    어떤 컬럼을 포함해야 하나요? 순서가 정해져 있나요?
Q-EXPORT-SIZE:    최대 몇 건까지 내보낼 수 있나요? 건수 초과 시 어떻게 하나요?
Q-EXPORT-NAME:    파일명 규칙이 있나요? (날짜 포함, 조건 반영 등)
```

### open (팝업/모달 열기)
```
Q-OPEN-TRIGGER:   어떤 데이터를 이 팝업에 전달해야 하나요?
Q-OPEN-CLOSE:     팝업을 닫는 방법은 무엇인가요? (X 버튼 / ESC / 완료 후 자동)
Q-OPEN-RESULT:    팝업에서 완료 후 원래 화면에 변화가 있나요? (목록 새로고침 등)
```

### validate (입력 검