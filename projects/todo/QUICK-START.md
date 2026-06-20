# TODO Web — Quick Start (실행 · 수정 · CI/CD)

> 앱 소개는 [README.md](README.md). 이 문서는 **돌리고 / 고치고 / 자동화**하는 실전 가이드다.
> 모든 경로는 `projects/todo/` 기준. 앱 코드는 `app_repo/`(자체 git 레포)에 있다.

---

## 0. 사전 요구사항

| 도구 | 버전(검증됨) | 비고 |
|---|---|---|
| Node.js | 22.x | npm 11 동봉 |
| Python | 3.x | git 훅(tdd-gate 등) 실행용 |
| git | 2.40+ | 훅은 bash로 실행(Windows는 Git Bash 동봉) |

```bash
node -v && npm -v && python --version && git --version
```

---

## 1. 설치

```bash
cd projects/todo/app_repo
( cd backend  && npm install )      # 약 150 패키지
( cd frontend && npm install )      # 약 190 패키지
```

---

## 2. 실행 (개발 서버)

백엔드와 프론트엔드를 **각각** 띄운다. 프론트의 Vite가 `/api`를 백엔드(3001)로 프록시한다.

```bash
# 터미널 A — 백엔드 (http://localhost:3001)
cd projects/todo/app_repo/backend
npm run dev            # tsx watch src/server.ts  (포트 변경: PORT=4000 npm run dev)

# 터미널 B — 프론트엔드 (http://localhost:5173)
cd projects/todo/app_repo/frontend
npm run dev            # vite
```

브라우저에서 **http://localhost:5173** 접속 → 할 일 추가/완료/삭제/필터.

> 헬스 체크: `curl http://localhost:3001/api/todos` → `[]` (초기 빈 목록).
> 데이터는 **인메모리**라 백엔드를 재시작하면 초기화된다(설계 범위).

### 프로덕션 빌드(프론트)

```bash
cd projects/todo/app_repo/frontend
npm run build          # dist/ 생성
npm run preview        # 빌드 결과 미리보기
```

---

## 3. 테스트

```bash
# 백엔드 (API 레벨 — Vitest + Supertest, 18 tests)
cd projects/todo/app_repo/backend  && npm test

# 프론트 (화면 레벨 — Vitest + Testing Library, 6 tests)
cd projects/todo/app_repo/frontend && npm test
```

### E2E (Playwright — 여정 JRN-TODO-MANAGE)

E2E는 두 서버가 떠 있어야 한다(위 2번). 별도 디바이스 브라우저가 필요하다.

```bash
cd projects/todo/app_repo/frontend
npm i -D @playwright/test
npx playwright install chromium
npx playwright test e2e/jrn-todo-manage.spec.ts
```

---

## 4. 수정하기 (TDD 루프 — 게이트가 강제)

`app_repo`는 자체 git 레포이고, commit 시 훅이 **테스트 없는/실패하는 구현**과 **스파인 ID 없는 메시지**를 차단한다.

### 4.1 git 훅 설치 (최초 1회)

```bash
cd projects/todo/app_repo
git init        # (이미 init돼 있으면 생략)
bash "<repo-root>/packages/plugin-ai-web-dev/hooks/install-git-hooks.sh"
# Windows PowerShell: powershell -ExecutionPolicy Bypass -File "<repo-root>\packages\plugin-ai-web-dev\hooks\install-git-hooks.ps1"
```

설치 후 `tdd-gate`가 **Node 백엔드/프론트 테스트를 자동 탐지**하므로 `HARNESS_TEST_CMD` 핀은 불필요하다.

### 4.2 변경 절차 (RED → GREEN → REFACTOR → COMMIT)

1. **RED** — 먼저 실패 테스트를 추가/수정한다.
   - API 동작: `backend/test/*.test.ts` · 화면 동작: `frontend/src/**/**.test.tsx`
   - 실행해 **빨강(실패)** 확인: `npm test`
2. **GREEN** — 통과시키는 **최소 구현**만. (`backend/src/`, `frontend/src/`)
3. **REFACTOR** — green 유지하며 중복 제거.
4. **COMMIT** — 스파인 ID 포함 메시지로 커밋. 훅이 전체 테스트를 돌려 green일 때만 통과.

```bash
git add -A
git commit -m "[PACK-TODO/T003] 마감일 필드 추가 (REQ-TODO-LIST.005)"
#   ↑ 형식: [<PACK|SPEC|MOD>/T###] 요약 (REQ-…)
#   - 테스트 없는 구현    → tdd-gate BLOCK
#   - 스파인 ID 없는 메시지 → commit-spine-id BLOCK
#   - 화면 shell 골격만    → [SCAFFOLD] 접두 (tdd-gate skip)
#   - E2E 여정            → [E2E/JRN-…] 접두
```

### 4.3 지켜야 할 규칙

- **layout 구조(②의 계약)는 임의로 바꾸지 않는다.** 화면 컴포넌트 구성·요구사항이 바뀌면
  그건 코드가 아니라 `model_repo/screens/SCR-TODO-LIST.yaml`(단일 진실원) 변경 → ② Gate A 재확정 →
  `PACK-TODO` 재발행(Change Order) 순서다. app_repo는 그 계약의 구현만 한다.
- **DS 폐쇄**: 화면 컴포넌트는 `foundation/design-system/ds-allowlist.md` 허용집합 안에서만.
- **2계층 테스트**: 새 REQ-는 **API 레벨 + 화면 레벨** 둘 다 테스트. 상태 전이는 모든 방향을 각각 1개 이상.

---

## 5. CI/CD

운영 범위는 `foundation/decisions/ops-stack.md` / `SPEC-OPS-000.md` 기준(현재 로컬 실행 + 테스트 게이트 중심).
아래는 **GitHub Actions**로 백엔드·프론트 테스트(+선택 E2E)를 자동 검증하는 권장 파이프라인이다.

### 5.1 워크플로 (app_repo/.github/workflows/ci.yml)

> 이 파일은 이미 생성돼 있다(`app_repo/.github/workflows/ci.yml`). 그대로 사용하거나 수정해 쓴다.

```yaml
name: ci
on:
  push: { branches: [main, master] }
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22', cache: 'npm' }
      # 백엔드 (API 레벨)
      - run: npm ci
        working-directory: backend
      - run: npm test
        working-directory: backend
      # 프론트 (화면 레벨)
      - run: npm ci
        working-directory: frontend
      - run: npm test
        working-directory: frontend

  e2e:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci && npm i -D @playwright/test
        working-directory: backend
      - run: npm ci && npm i -D @playwright/test && npx playwright install --with-deps chromium
        working-directory: frontend
      # 서버 기동 후 E2E
      - name: start backend
        run: (cd backend && PORT=3001 npm run start &) && sleep 3
      - name: start frontend (preview)
        run: (cd frontend && npm run build && npm run preview -- --port 5173 &) && sleep 3
      - run: npx playwright test e2e/jrn-todo-manage.spec.ts
        working-directory: frontend
```

### 5.2 로컬 게이트 ↔ CI 정합

- **로컬**: `app_repo`의 commit-msg 훅(`tdd-gate` + `commit-spine-id`)이 1차 방어선. 푸시 전에 이미 green·추적성 보장.
- **CI**: 같은 `npm test`를 클린 환경에서 재실행해 "내 머신에서만 통과" 방지. PR 머지 게이트로 사용 권장.
- **2단계 분리**: `test`(빠름, 항상) → `e2e`(브라우저 필요, test 통과 후). E2E가 느리면 nightly로 분리 가능.

### 5.3 배포(확장 시)

현재 인메모리·로컬 범위라 배포 단계는 비대상이다. 영속화/배포가 필요해지면:
1. 저장소를 인메모리 → DB로 교체(별도 REQ-/ENT- 계약 변경부터, §4.3).
2. 프론트 `npm run build` 산출물(`dist/`)을 정적 호스팅, 백엔드는 컨테이너화.
3. 위 `ci.yml`에 `deploy` job 추가(test/e2e 통과 후 `needs`로 연결).

---

## 6. 트러블슈팅

| 증상 | 원인/해결 |
|---|---|
| 프론트에서 API 404/연결 실패 | 백엔드(3001) 미기동. 터미널 A 확인. 프록시는 `vite.config.ts`의 `/api`. |
| 커밋이 `tdd-gate BLOCK` | 구현만 바뀌고 테스트가 없음 → 테스트 먼저(§4.2). 의도적 골격은 `[SCAFFOLD]`. |
| 커밋이 `commit-spine-id BLOCK` | 메시지에 `[PACK-TODO/T###] … (REQ-…)` 형식·스파인 ID 누락. |
| 훅이 "러너 미탐지" | 거의 없음(자동탐지). 특수 명령은 설치 시 `HARNESS_TEST_CMD`(cwd=app_repo 상대) 지정. |
| 목록이 새로고침하면 사라짐 | 정상 — 인메모리 저장소(재시작 시 초기화). |
