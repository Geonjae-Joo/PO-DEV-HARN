# Design Guide

> 이 프로젝트의 허용 컴포넌트 집합(DS 폐쇄). 여기 없는 컴포넌트는 화면에 쓸 수 없다.
> 기반: shadcn/ui (Radix + Tailwind v4, new-york 스타일). 컴포넌트 소스: input/design-system/ds-source/src/components/ui/

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
