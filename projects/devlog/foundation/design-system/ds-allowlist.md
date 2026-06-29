# DS Allowlist — 허용 컴포넌트 집합 (가드레일)

> **이 파일은 DS 폐쇄를 강제하는 계약/가드레일이다.**
> `^## \w+` 헤딩만 파서가 인식한다 — 공백·하이픈 없는 PascalCase.
> 이 목록 밖의 컴포넌트는 화면 설계·구현에서 사용할 수 없다.

---

### 기본 (shadcn-vue primitives)

## Button
- **description**: 사용자 액션을 실행하는 기본 버튼. variant로 시각적 계층 표현
- **props**: variant: string, size: string, disabled: boolean, asChild: boolean
- **usage**: 폼 제출, 액션 트리거, 다이얼로그 확인/취소, 아이콘 버튼
- **states**: default, hover, focus, active, disabled, loading

## Input
- **description**: 단일 줄 텍스트 입력 필드
- **props**: modelValue: string, type: string, placeholder: string, disabled: boolean
- **usage**: 검색, 폼 필드, 필터 입력
- **states**: default, focus, disabled, error, readonly

## Select
- **description**: 드롭다운 선택 컴포넌트 (Radix Vue 기반)
- **props**: modelValue: string, disabled: boolean
- **usage**: 정렬 선택, 카테고리 필터, 폼 선택 필드
- **states**: default, open, focus, disabled

## Textarea
- **description**: 여러 줄 텍스트 입력 필드
- **props**: modelValue: string, placeholder: string, rows: number, disabled: boolean
- **usage**: 글 본문, 댓글, 긴 설명 입력
- **states**: default, focus, disabled, error

## Label
- **description**: 폼 입력 요소와 연결되는 접근성 레이블
- **props**: for: string
- **usage**: 모든 폼 필드 레이블
- **states**: default, disabled

## Card
- **description**: 콘텐츠 컨테이너. CardHeader·CardContent·CardFooter 서브컴포넌트 포함
- **props**: class: string
- **usage**: 게시글 카드, 통계 카드, 설정 섹션
- **states**: default, hover

## Badge
- **description**: 상태·태그·수량 등을 나타내는 인라인 레이블
- **props**: variant: string
- **usage**: 태그, 상태 표시, 카운트 뱃지
- **states**: default, secondary, destructive, outline

## Tabs
- **description**: 콘텐츠 영역을 탭으로 전환하는 컴포넌트
- **props**: defaultValue: string, modelValue: string
- **usage**: 페이지 섹션 전환, 필터 뷰
- **states**: default, active, disabled

## Switch
- **description**: 켜짐/꺼짐 토글 스위치
- **props**: modelValue: boolean, disabled: boolean
- **usage**: 설정 토글, 알림 on/off
- **states**: default, checked, disabled

## Skeleton
- **description**: 콘텐츠 로딩 중 표시하는 플레이스홀더
- **props**: class: string
- **usage**: 게시글 목록, 프로필, 통계 카드 로딩 상태
- **states**: default

## Avatar
- **description**: 사용자 프로필 이미지 또는 이니셜 표시
- **props**: class: string
- **usage**: 헤더 유저 아이콘, 게시글 작성자, 댓글 작성자
- **states**: default, fallback

## DropdownMenu
- **description**: 트리거 요소에 연결된 컨텍스트 메뉴
- **props**: open: boolean
- **usage**: 사용자 메뉴, 게시글 더보기, 설정 옵션
- **states**: default, open, checked, disabled

## Separator
- **description**: 콘텐츠 영역 구분선 (가로/세로)
- **props**: orientation: string, decorative: boolean
- **usage**: 메뉴 구분, 섹션 구분
- **states**: default

## Form
- **description**: vee-validate 기반 폼 유효성 검증 래퍼. FormItem·FormLabel·FormControl·FormMessage 포함
- **props**: validationSchema: object
- **usage**: 로그인, 회원가입, 게시글 작성 폼
- **states**: default, error, success

---

### 합성 컴포넌트 (devlog composite)

## Header
- **description**: 브랜드 + 네비게이션 + 테마 토글 + 인증 액션을 포함한 앱 공통 헤더
- **props**: brand: string, navItems: NavItem[], user: AuthUser|null, isDark: boolean
- **usage**: 모든 페이지 최상단 고정 헤더
- **states**: default, user-logged-in, user-guest

## PostCard
- **description**: 게시글 썸네일·태그·제목·요약·좋아요를 포함한 카드형 게시글 미리보기
- **props**: post: Post, liked: boolean, likeCount: number
- **usage**: 게시글 목록, 관련 게시글, 인기 게시글
- **states**: default, hover, liked

## FilterBar
- **description**: 검색 Input + 태그 Button 그룹 + 정렬 Select를 묶은 필터 복합 컴포넌트
- **props**: tags: TagOption[], sortOptions: SortOption[], modelValue: FilterState
- **usage**: 게시글 목록 필터링, 검색 결과 정렬
- **states**: default, searching, tag-selected

## PomodoroTimer
- **description**: 원형 SVG 진행 게이지와 시작/정지/초기화 버튼을 포함한 뽀모도로 타이머
- **props**: targetSeconds: number, status: TimerStatus, elapsed: number
- **usage**: 집중 타이머 위젯, 대시보드 사이드 패널
- **states**: idle, running, paused, done

## ContributionGraph
- **description**: GitHub 스타일 26×7 잔디밭 그래프. 날짜별 활동량을 색 강도로 표현하며 hover 툴팁 제공
- **props**: cells: Cell[], levelOf: (count: number) => 0|1|2|3|4
- **usage**: 대시보드 기여도, 학습 기록, 연속 달성 표시
- **states**: default, hover

## WeeklyChart
- **description**: Chart.js(vue-chartjs) 기반 주간 활동 막대 차트 래퍼
- **props**: data: WeekData[], title: string, color: string, height: number, yLabel: string
- **usage**: 주간 학습량, 주간 글쓰기, 포모도로 완료 통계
- **states**: default, empty

## StatCard
- **description**: Card 기반 단일 통계 수치 카드. 추세(trend) 배지·아이콘·설명 텍스트 포함
- **props**: title: string, value: string|number, description: string, trend: Trend, icon: Component, variant: string
- **usage**: 대시보드 KPI, 총 게시글 수, 총 좋아요, 연속 학습일
- **states**: default, accent, trend-up, trend-down

---

### 확장 (추가 가능 shadcn-vue 컴포넌트)

## Dialog
- **description**: 페이지 위에 표시되는 모달 다이얼로그
- **props**: open: boolean, modal: boolean
- **usage**: 삭제 확인, 상세 보기, 수정 폼
- **states**: default, open, closed

## Alert
- **description**: 인라인 알림 메시지 (성공/경고/오류/정보)
- **props**: variant: string
- **usage**: 폼 오류 요약, 시스템 알림, 빈 상태 안내
- **states**: default, destructive

## Tooltip
- **description**: 요소에 마우스를 올렸을 때 보조 설명을 표시하는 작은 팝업
- **props**: content: string, side: string, delay: number
- **usage**: 아이콘 버튼 설명, 축약 텍스트 전체 보기
- **states**: default, visible

## Checkbox
- **description**: 단일 항목 선택/해제 체크박스
- **props**: modelValue: boolean, disabled: boolean, indeterminate: boolean
- **usage**: 약관 동의, 목록 다중 선택
- **states**: default, checked, indeterminate, disabled

## RadioGroup
- **description**: 상호 배타적 선택지 중 하나를 고르는 라디오 버튼 그룹
- **props**: modelValue: string, disabled: boolean
- **usage**: 뽀모도로 세션 유형, 설정 옵션 선택
- **states**: default, checked, disabled

## Progress
- **description**: 작업 진행률을 표시하는 선형 프로그레스 바
- **props**: modelValue: number, max: number
- **usage**: 목표 달성률, 파일 업로드, 레벨 게이지
- **states**: default, complete

## Sheet
- **description**: 화면 가장자리에서 슬라이드인하는 패널 (모바일 서랍 메뉴)
- **props**: open: boolean, side: string
- **usage**: 모바일 네비게이션, 설정 패널
- **states**: default, open, closed

## Popover
- **description**: 트리거 요소 근처에 표시되는 자유형 팝업 패널
- **props**: open: boolean
- **usage**: 날짜 피커, 색상 선택, 복잡한 필터 UI
- **states**: default, open

## Accordion
- **description**: 클릭 시 열리고 닫히는 확장 패널 목록
- **props**: type: string, collapsible: boolean
- **usage**: FAQ, 설정 그룹, 필터 카테고리
- **states**: default, open, closed

## Pagination
- **description**: 페이지 번호 탐색 컴포넌트
- **props**: page: number, totalPages: number, siblingCount: number
- **usage**: 게시글 목록 페이지네이션
- **states**: default, active, disabled
