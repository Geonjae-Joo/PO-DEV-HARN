# DS Allowlist — 허용 컴포넌트 집합 (가드레일)

> **이 파일은 가이드(안내서)가 아니라 DS 폐쇄를 강제하는 계약/가드레일이다.** 여기 `## 이름`으로 등록된 컴포넌트만 screen model·design page에 쓸 수 있고, lint가 기계적으로 강제한다. DS 종류와 무관한 stack-agnostic 형식(`## 이름` + `description` + `props`)만 담는다.
> 이 프로젝트의 DS 정체성·셋업·컴포넌트 추가 절차(사람용 안내서)는 plugin-prerequisite `docs/project-design-guide.md` 및 `foundation/decisions/tech-stack.md`(DS 핀의 단일 출처)를 참조하라.

## Button
- **description**: 액션을 실행하는 기본 버튼
- **props**: label: string, variant: default|secondary|destructive|outline|ghost|link, size: default|sm|lg|icon, disabled: boolean
- **usage**: 폼 제출, 액션 트리거, 다이얼로그 확인/취소

## Input
- **description**: 한 줄 텍스트 입력 필드
- **props**: value: string, placeholder: string, type: text|email|password|number, disabled: boolean
- **usage**: 폼 입력, 검색, 필터

## Select
- **description**: 드롭다운 단일 선택 컴포넌트
- **props**: options: array, value: string, placeholder: string, disabled: boolean
- **usage**: 단일 항목 선택, 필터 조건

## Table
- **description**: 기본 HTML 테이블 구조 컴포넌트 (헤더·바디·푸터 슬롯 포함)
- **props**: headers: array, rows: array
- **usage**: 정적 데이터 표시, DataTable의 기반

## Dialog
- **description**: 모달 팝업 컨테이너
- **props**: open: boolean, title: string, onClose: function
- **usage**: 확인 팝업, 입력 팝업, 상세 팝업

## Card
- **description**: 정보를 묶어 보여주는 카드 컨테이너
- **props**: title: string, footer: slot
- **usage**: 대시보드 위젯, 정보 그룹

## Badge
- **description**: 상태·분류를 표시하는 작은 라벨
- **props**: label: string, variant: default|secondary|destructive|outline
- **usage**: 상태 표시, 태그, 분류 라벨

## Tabs
- **description**: 탭 전환 컴포넌트
- **props**: items: array, defaultValue: string
- **usage**: 화면 내 카테고리 전환, 멀티뷰

## Checkbox
- **description**: 체크박스 입력 컴포넌트
- **props**: checked: boolean, label: string, disabled: boolean
- **usage**: 다중 선택, 동의 여부, 필터 옵션

## DropdownMenu
- **description**: 클릭 시 펼쳐지는 드롭다운 메뉴
- **props**: items: array, trigger: slot
- **usage**: 더보기 메뉴, 행 액션, 컨텍스트 메뉴

## Form
- **description**: react-hook-form 기반 폼 래퍼 (유효성 검사 통합)
- **props**: onSubmit: function, resolver: zodResolver
- **usage**: 입력 폼 전체 래핑, 유효성 검사

## Label
- **description**: 폼 필드 레이블 컴포넌트
- **props**: htmlFor: string, label: string
- **usage**: 입력 필드 레이블

## Sonner
- **description**: 토스트 알림 컴포넌트 (화면 상단/하단 팝업 메시지)
- **props**: message: string, type: success|error|info|warning
- **usage**: 저장 성공, 오류 알림, 안내 메시지

## Calendar
- **description**: 날짜 선택 달력 기본 컴포넌트
- **props**: mode: single|range, selected: date, onSelect: function
- **usage**: DatePicker 내부 컴포넌트

## Popover
- **description**: 기준 요소 기준으로 떠오르는 레이어 컨테이너
- **props**: open: boolean, trigger: slot, content: slot
- **usage**: DatePicker, 툴팁, 컨텍스트 패널

## DataTable
- **description**: 정렬·페이지네이션을 지원하는 데이터 테이블 (Table + TanStack Table 합성)
- **props**: columns: array, rows: array, sortable: boolean, pageSize: number
- **usage**: 목록 화면의 메인 데이터 표시

## FilterBar
- **description**: 목록 화면 상단의 필터 묶음 (Input + Select + Button 합성)
- **props**: fields: array, onApply: function
- **usage**: 목록 검색/필터 조건 입력 영역

## DatePicker
- **description**: 날짜 선택기 (Calendar + Popover 합성)
- **props**: value: date, onChange: function, range: boolean, placeholder: string
- **usage**: 날짜 입력 필드, 기간 필터

## Header
- **description**: 전체 페이지 상단 글로벌 헤더 셸 (좌 브랜드 · 중 NavMenu 대메뉴 · 우 actions 3분할 합성)
- **props**: brand: node, menu: array, actions: slot
- **usage**: 앱 전역 상단 바, 시스템명·대메뉴·프로필 배치

## NavMenu
- **description**: 상단 헤더의 가로 대메뉴 (Button variant=ghost 묶음으로 만든 합성 컴포넌트)
- **props**: items: array, value: string
- **usage**: 글로벌 대메뉴, 섹션 전환 (예: 프로젝트 관리/개발/설정)

## Avatar
- **description**: 사용자 프로필 이미지/이니셜 표시 (이미지 실패 시 fallback). AvatarBadge·AvatarGroup 합성 지원
- **props**: src: string, alt: string, fallback: string, size: default|sm|lg
- **usage**: 프로필 표시, 헤더 우측 계정 영역, 목록 작성자 표시

## Separator
- **description**: 영역을 시각적으로 나누는 구분선
- **props**: orientation: horizontal|vertical, decorative: boolean
- **usage**: 섹션 구분, 메뉴 그룹 구분, 헤더 내 영역 분리

## Tooltip
- **description**: 호버 시 짧은 보조 설명을 띄우는 말풍선
- **props**: content: string, side: top|right|bottom|left, delay: number
- **usage**: 아이콘 버튼 설명, 축약 텍스트 보충, 도움말

## Skeleton
- **description**: 콘텐츠 로딩 중 자리표시 플레이스홀더 (펄스 애니메이션)
- **props**: className: string
- **usage**: 로딩 상태 표시, 테이블/카드 로딩 자리, 비동기 대기

## Switch
- **description**: 켜짐/꺼짐 토글 스위치
- **props**: checked: boolean, onCheckedChange: function, disabled: boolean, size: default|sm
- **usage**: 설정 on/off, 활성화 토글, 폼 불리언 입력

## Textarea
- **description**: 여러 줄 텍스트 입력 필드
- **props**: value: string, placeholder: string, rows: number, disabled: boolean
- **usage**: 긴 텍스트 입력, 메모/설명 입력, 댓글 작성

## Alert
- **description**: 화면 내 인라인 알림/안내 메시지 박스 (제목+설명)
- **props**: variant: default|destructive, title: string, description: string
- **usage**: 경고·오류·안내 인라인 표시, 폼 검증 메시지, 상태 공지

## Breadcrumb
- **description**: 현재 위치를 경로로 보여주는 탐색 경로
- **props**: items: array, separator: slot
- **usage**: 페이지 계층 경로, 상세 화면 내비게이션, 뒤로가기 경로 표시

## Sheet
- **description**: 화면 가장자리에서 슬라이드되는 패널 (Dialog 기반 드로어)
- **props**: open: boolean, side: top|right|bottom|left, title: string, onClose: function
- **usage**: 모바일 네비게이션 드로어, 측면 상세/필터 패널, 보조 작업 영역
