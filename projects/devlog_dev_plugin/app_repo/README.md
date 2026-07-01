# app_repo — ③ AI-WEB-DEV 산출물 (비어 있음, 시작 지점)

> 이 디렉터리는 **③ plugin-ai-web-dev가 채울 단 하나의 웹앱**이다. 지금은 비어 있다(골격만).
> ③를 시작하기 위한 입력(① foundation + ② model_repo)은 이미 `../foundation/`·`../model_repo/`에 준비돼 있다.

## 시작 방법

리포 루트 `docs/TUTORIAL-ai-web-dev-devlog.md` 또는 `../TUTORIAL.md`의 step-by-step을 따른다. 요약:

1. **부트스트랩**: `bash packages/plugin-ai-web-dev/hooks/install-speckit.sh` → 이 `app_repo/`에 `.specify/` vendoring + git 훅 설치.
2. **Phase 0**: `/speckit-specify`로 `../foundation/platform-baseline/SPEC-000.md`·`SPEC-OPS-000.md`의 공통 기능 전달 모드(A/B) 결정 → `baseline-delivery-manifest.yaml`.
3. **Phase α**: `/speckit-scaffold` → `../model_repo/screens/*.yaml`(3 confirmed) → `frontend/app/` shell. `layout-hash-guard`가 ②확정 위치 일치 강제.
4. **Phase β**: `PACK-BLOG`·`PACK-STUDY`별 `/speckit-specify → plan → tasks → Gate B → implement` (TDD).
5. **Phase γ**: `../model_repo/journeys/JRN-*.yaml` → Playwright E2E + NFR.

> 스택: `../foundation/decisions/tech-stack.md` (Next.js 14 App Router + React + Tailwind + Drizzle + PostgreSQL + NextAuth).
> 디렉터리 구조(`frontend/app/`·`backend/`·`specs/`)는 Phase 0/α가 tech-stack 프레임워크에서 파생해 생성한다.
