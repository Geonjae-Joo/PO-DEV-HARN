# DS Closure Rule — DS 집합 밖 컴포넌트 금지

## 원칙

**design-guide.md에 정의된 DS 컴포넌트만 screen model과 design page에 사용할 수 있다.**
DS 집합 밖의 컴포넌트는 PI가 요청하더라도 layout-recommend skill이 발명하지 않는다.

## 적용 범위

| 단계 | 적용 |
|---|---|
| ① design page 생성 | design-page-lint.py가 저장 시 자동 검증 |
| ② screen model 작성 | on-save-lint-L1.py가 저장 시 자동 검증 |
| ③ frontend 구현 | code-reviewer subagent가 PR 단계에서 검증 |

## PI가 DS 밖 컴포넌트를 요청하는 경우

1. **가장 근접한 DS 컴포넌트를 대안으로 제안**한다.
   - "커스텀 달력 위젯" → DS의 `DatePicker` 컴포넌트 + `FilterBar` 조합 제안
2. 대안이 없으면 **design-guide.md에 신규 컴포넌트를 추가하는 프로세스**를 밟는다.
   - 개발 리드/운영자가 DS에 컴포넌트 추가
   - design-guide.md 갱신
   - ds-guide-validate.py 재실행
3. **어느 경우에도 "DS에 없는 컴포넌트를 그냥 쓰는" 것은 허용되지 않는다.**

## Lint L1 검증 상세 (on-save-lint-L1-L4.py)

- `layout[].source.ref` 값이 design-guide.md의 컴포넌트 이름 목록에 포함되는지 확인
- `layout[].source.kind == 'ds'` 인 경우 무조건 검증 대상
- `layout[].source.kind == 'page-region'` 인 경우 design-pages의 슬롯명 확인
- 검증 실패 시 `error` 레벨 반환 → 저장 차단 (또는 경고 후 수동 확인)

## DS 신규 컴포넌트 추가 절차

```
1. 개발 리드가 DS 팀/디자이너와 협의
2. input/design-system/ 에 컴포넌트 추가
3. design-guide.md에 섹션 추가 (## ComponentName + 필수 필드)
4. ds-guide-validate.py 실행 → 통과 확인
5. design-page-lint.py 재실행 → 기존 design page 영향 없는지 확인
6. link-manifest.yaml 갱신
```
