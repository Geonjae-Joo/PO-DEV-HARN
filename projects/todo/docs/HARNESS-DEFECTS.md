# 하네스 결함 로그 (TODO 리허설 중 발견)

> 골드패스 리허설 도중 발견한 하네스 결함·마찰·문서 불일치를 기록한다.
> 분류: **fix-now**(즉시 수정, 작고 안전) / **batch**(모아서 일괄) / **wontfix**(설계 의도, 기록만).
> 각 항목: 증상 / 위치 / 영향 / 조치.

| ID | 분류 | 한 줄 요약 | 상태 |
|---|---|---|---|
| DEF-001 | batch | tdd-gate/manifest-sync의 cwd 가정(`app_repo/` 접두)이 실제 훅 설치 위치(cwd=app_repo)와 모순 | ✅ **수정 완료** |
| DEF-002 | batch | tdd-gate 테스트 러너 자동탐지가 Node **백엔드**를 인식 못함(frontend 한정) | ✅ **수정 완료** |
| OBS-003 | wontfix(설계) | root .gitignore가 model_repo/app_repo를 비추적 → app_repo는 자체 레포가 정석 | 기록(설계 의도) |
| OBS-004 | fix-now | manifest-sync 콘솔 출력 mojibake(`����`) — git 훅 파이프 인코딩 | ✅ **수정 완료** |
| OBS-005 | 환경 | 무관 파일 `docs/SUPERPOWERS-CHATBOT-BUILD-GUIDE.md`가 모노레포 커밋에 포함됨 | 기록 |

> ## ✅ 수정 완료 요약 (2026-06-20, 프로젝트 비의존적·일반화)
> 공용 `packages/plugin-ai-web-dev/hooks/`를 다음 어떤 스택/위치의 프로젝트에도 동작하도록 일반화 수정하고, **HARNESS_TEST_CMD 없이 자동탐지만으로** TODO(Node 풀스택)가 통과함을 검증했다.
>
> - **`tdd-gate.py`** — `_app_base()` 추가: cwd가 **app_repo(설치된 훅)** 든 **프로젝트 루트(수동)** 든 backend/frontend를 정확히 찾는다(`.` → `app_repo` 후보 순회). `detect_test_commands()`에 **Node 백엔드(`backend/package.json`)** 탐지 추가(JVM→Node→Python→Go 단일 백엔드). bash용 경로는 forward slash 고정(Windows `os.path.join` 역슬래시 회피).
> - **`manifest-sync.py`** — `_project_root()` 추가: cwd=app_repo면 `..`, 프로젝트 루트면 `.`로 해석해 `model_repo/specs`를 정확히 찾는다(이전엔 SKIP). `shell_ref`는 프로젝트 루트 상대(canonical) 경로로 정규화 저장.
> - **`install-git-hooks.sh`/`.ps1`** — 생성 훅에 `export PYTHONIOENCODING=utf-8 PYTHONUTF8=1` 추가(Windows 한글 출력 mojibake 해소, OBS-004).
>
> **검증(회귀 포함)**: 자동탐지가 ①프로젝트루트→`app_repo/backend|frontend` ②app_repo→`./backend|frontend` ③빈 예제→탐지 없음 으로 정확. HARNESS_TEST_CMD 미설치 훅으로 커밋 시 백엔드(18)+프론트(6) 모두 실행·green, manifest-sync 정상 동기화·한글 출력 정상.
>
> 아래는 발견 당시 원본 기록(보존). OBS-005는 사용자 파일이라 미수정(브랜치라 main 무영향).

---

### DEF-001 — tdd-gate/manifest-sync의 cwd 가정이 훅 설치 위치와 모순
- **분류**: batch (설계 정합성 — 일괄 수정 권장)
- **증상**: `tdd-gate.py`의 `detect_test_commands()`는 `app_repo/frontend/package.json`·`app_repo/backend/build.gradle` 등 **프로젝트 루트 cwd**를 가정한 경로로 러너를 탐지한다. 그러나 `install-git-hooks.sh`는 훅을 `app_repo/.git/hooks/`에 설치하고, git은 훅을 **레포 루트(=app_repo) cwd**로 실행한다. 따라서 cwd=app_repo에서 `app_repo/frontend/...`는 `app_repo/app_repo/frontend/...`가 되어 탐지 실패. `manifest-sync.py`도 `model_repo/specs`를 app_repo 기준으로 찾아 동기화 실패(다만 post-commit non-blocking이라 커밋은 유지).
- **위치**: `packages/plugin-ai-web-dev/hooks/tdd-gate.py` (`detect_test_commands`), `manifest-sync.py`, 그리고 `foundation/decisions/tech-stack.md`의 `HARNESS_TEST_CMD` 예시(`cd app_repo/backend …` — 프로젝트 루트 cwd 가정).
- **근거**: install 스크립트 주석은 "app_repo 루트에서 실행"이라 명시하고 git-hooks.manifest.json도 app_repo 기준. 즉 cwd=app_repo가 의도. 그런데 자동탐지 경로만 프로젝트-루트 접두를 가짐 → 내부 불일치.
- **영향**: HARNESS_TEST_CMD 미지정 시 모든 구현 커밋이 "러너 미탐지"로 BLOCK(또는 HARNESS_TDD_ALLOW_NO_RUNNER 우회 필요). Node 등 비-JVM 백엔드에서 특히 침묵 실패.
- **조치(우회)**: 본 리허설은 `HARNESS_TEST_CMD`를 **app_repo 상대경로**(`cd backend && npm test --silent && cd ../frontend && npm test --silent`)로 설치해 통과. 근본 수정안 → 자동탐지 경로를 cwd 기준 상대(`frontend/`, `backend/`)로 바꾸거나, 훅이 git 최상위(`git rev-parse --show-toplevel`)로 정규화.

### DEF-002 — tdd-gate 자동탐지가 Node 백엔드를 인식하지 못함
- **분류**: batch
- **증상**: `detect_test_commands()`는 백엔드를 JVM(gradle/maven)·pytest·go.mod로만 탐지한다. `app_repo/backend/package.json`(Node) 케이스가 없어, Node 풀스택에서 백엔드 테스트가 게이트에서 누락된다(프론트만 `npm test`).
- **위치**: `packages/plugin-ai-web-dev/hooks/tdd-gate.py` `detect_test_commands()`.
- **영향**: Node 백엔드 구현 커밋이 테스트 green 검증 없이 통과할 수 있음(테스트 파일 존재 여부만 통과시키면).
- **조치(우회)**: HARNESS_TEST_CMD로 백+프론트 모두 실행하도록 명시 핀. 근본 수정안 → `if exists("backend/package.json"): commands.append(["bash","-lc","cd backend && npm test"])` 추가.

### 결합 패치 제안 (DEF-001 + DEF-002) — `packages/plugin-ai-web-dev/hooks/tdd-gate.py`
`detect_test_commands()`를 **git 최상위 기준 + Node 백엔드 인식**으로 교체:
```python
def _root() -> str:
    import subprocess
    try:
        return subprocess.run(["git","rev-parse","--show-toplevel"],
                              capture_output=True, text=True, check=True).stdout.strip() or "."
    except Exception:
        return "."

def detect_test_commands() -> list:
    r = _root()              # 훅이 app_repo/.git/hooks에서 cwd=app_repo로 실행돼도 정확
    cmds = []
    be = f"{r}/backend"; fe = f"{r}/frontend"
    # JVM
    if os.path.exists(f"{be}/build.gradle") or os.path.exists(f"{be}/build.gradle.kts"):
        cmds.append(["bash","-lc",f"cd '{be}' && ./gradlew test"])
    elif os.path.exists(f"{be}/pom.xml"):
        cmds.append(["bash","-lc",f"cd '{be}' && mvn -q test"])
    # Node 백엔드  ← DEF-002 추가
    elif os.path.exists(f"{be}/package.json"):
        cmds.append(["bash","-lc",f"cd '{be}' && npm test --silent"])
    # Python / Go ... (동일 패턴)
    if os.path.exists(f"{fe}/package.json"):
        cmds.append(["bash","-lc",f"cd '{fe}' && npm test --silent"])
    return cmds
```
`manifest-sync.py`도 동일하게 `git rev-parse --show-toplevel`로 정규화하면 `model_repo/specs` 동기화가 app_repo cwd에서도 동작한다(현재는 SKIP).
검증: 이 패치 적용 시 `HARNESS_TEST_CMD` 없이도 본 리허설의 backend(Node)+frontend가 자동 탐지·실행되어야 한다.

### OBS-004 — manifest-sync 출력 mojibake
- 증상: post-commit에서 `[manifest-sync] SKIP: model_repo\specs ����.` — 한글이 깨짐.
- 원인 추정: git이 훅 stdout을 파이프로 받을 때 인코딩. 스크립트는 `reconfigure(utf-8)` 하지만 메시지가 cp949 콘솔 경유로 깨짐. 기능 영향 없음(SKIP 자체는 DEF-001 사유).
- 조치: DEF-001 cwd 수정으로 SKIP이 사라지면 대부분 해소. 잔여 시 메시지 ASCII화 또는 `PYTHONIOENCODING=utf-8` 훅 export.

### OBS-005 — 무관 파일 커밋 포함
- 증상: 첫 모노레포 커밋(`git add -A`)에 시작 시점 untracked였던 `docs/SUPERPOWERS-CHATBOT-BUILD-GUIDE.md`가 포함됨.
- 영향: 리허설과 무관한 사용자 파일이 `harn-todo-test` 브랜치에 함께 커밋됨. 기능 영향 없음.
- 조치: 필요 시 별도 커밋으로 분리/되돌리기. (브랜치라 main 영향 없음)
