# DS Source — DevLog 디자인 시스템 (시각 레퍼런스)

> **DS 계약의 단일 출처는 `../ds-allowlist.md`다.** 이 디렉터리는 컴포넌트의 *시각·동작 레퍼런스*다.

## 구성

- `src/assets/tokens.css` — 디자인 토큰(CSS custom properties). 시안 강조색 + zinc 기반 다크 테마(SIR-003). `tailwind.config.ts`의 `theme.extend`가 이 변수를 참조한다.
- 렌더 자산(상위 `../`): `ds-compiled.css`·`ds-fixtures.json` — 렌더 엔진(ADR-002 D8)이 화면을 **실제 DS 모양**으로 그릴 때 사용. 없으면 와이어프레임 폴백(layout_hash 불변).

## 프레임워크 주의 (중요)

DevLog의 DS 시각 레퍼런스 컴포넌트(`Header`·`PostCard`·`PomodoroTimer`·`ContributionGraph`·`WeeklyChart`·`StatCard` 등)는 원래 **shadcn-vue(Vue)** 로 작성되어 있다(원본: `projects/devlog/foundation/design-system/ds-source/`).

그러나 **본 앱(`app_repo`)의 구현 프레임워크는 React/Next.js다**(`../../decisions/tech-stack.md`, DevLog SRS COR-001). 화면 모델(②)은 프레임워크 중립이므로, ③ `design-system-usage` 스킬이 **allowlist의 컴포넌트 계약(props·states·usage)** 을 React 컴포넌트로 구현한다. 즉:

- **계약(무엇)** = `ds-allowlist.md` (프레임워크 중립, 권위)
- **시각 레퍼런스(어떻게 보이나)** = 이 디렉터리 + `projects/devlog`의 Vue 소스
- **구현(어떤 코드)** = ③ Phase α/β가 React/Next.js로 생성

> 이 픽스처는 ③ plugin-ai-web-dev를 테스트하기 위한 것이다. 전체 Vue 소스를 복사하지 않고, 렌더·핀에 필요한 중립 자산(allowlist·tokens·compiled css·fixtures)만 둔다.
