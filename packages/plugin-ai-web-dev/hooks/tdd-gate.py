#!/usr/bin/env python3
"""
Hook: tdd-gate.py
트리거: commit 직전 (pre-commit)
목적:  TDD 강제 — 대응 테스트가 없거나 실패한 구현 커밋을 차단한다.
       scaffold 커밋([SCAFFOLD] 마커)은 예외 처리(skip).
종료코드: 0 = 통과(commit 허용), 1 = 차단(commit 거부)
정책: rules/tdd-policy.md

스택 비고: 테스트 명령·소스 확장자는 ①의 tech-stack.md가 정한 스택에 따른다(고정값 아님).
  - 명시 지정: 환경변수 HARNESS_TEST_CMD="<테스트 실행 명령>" 이 있으면 그대로 실행한다.
  - 미지정 시: 아래 자동 탐지(JVM/Node/Python/Go 등 일반 생태계)로 폴백한다.
"""

import os
import re
import sys
import subprocess

# Windows 콘솔(cp949 등) 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


SKIP_MARKERS = ("[SCAFFOLD]",)

# 테스트 파일 판별 — 명확한 테스트 네이밍 컨벤션만 매칭한다.
# 주의: 'spec' 부분문자열을 통째로 쓰면 하니스의 spec-pack 디렉터리(specs/)·spec.yaml·spec.md를
# 테스트로 오인한다. 따라서 파일명 컨벤션(.spec.<ext>/.test.<ext>/test_*/*_test) + 테스트 전용
# 디렉터리(test/tests/__tests__/e2e)만 인정하고, 'specs'는 테스트 디렉터리로 보지 않는다.
TEST_FILE_RE = re.compile(r"(^test_|_test\.|\.test\.|\.spec\.|_spec\.)", re.IGNORECASE)
TEST_DIR_PARTS = {"test", "tests", "__tests__", "e2e"}

# 구현/테스트 판별용 소스 확장자 (스택 중립). 필요 시 HARNESS_SRC_EXT로 확장.
DEFAULT_SRC_EXT = (".java", ".kt", ".ts", ".tsx", ".js", ".jsx",
                   ".py", ".go", ".rb", ".cs", ".vue", ".svelte", ".php", ".rs")

def src_exts() -> tuple:
    extra = os.environ.get("HARNESS_SRC_EXT", "")
    extra_list = tuple(e.strip() for e in extra.split(",") if e.strip())
    return DEFAULT_SRC_EXT + extra_list


def read_commit_message() -> str:
    """commit message 파일 경로가 인자로 오면 읽고, 없으면 환경에서 추정."""
    if len(sys.argv) > 1:
        try:
            return open(sys.argv[1], encoding="utf-8").read()
        except OSError:
            return ""
    return ""


def staged_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, check=True,
        ).stdout
        return [f for f in out.splitlines() if f.strip()]
    except Exception:
        return []


def detect_test_commands() -> list:
    """일반 생태계 자동 탐지(JVM/Node/Python/Go). 러너를 못 찾으면 빈 리스트."""
    commands = []
    # JVM (Gradle/Maven)
    if os.path.exists("app_repo/backend/build.gradle") or os.path.exists("app_repo/backend/build.gradle.kts"):
        commands.append(["bash", "-lc", "cd app_repo/backend && ./gradlew test"])
    elif os.path.exists("app_repo/backend/pom.xml"):
        commands.append(["bash", "-lc", "cd app_repo/backend && mvn -q test"])
    # Node (package.json에 test 스크립트가 있을 때)
    if os.path.exists("app_repo/frontend/package.json"):
        commands.append(["bash", "-lc", "cd app_repo/frontend && npm test --silent"])
    # Python
    if any(os.path.exists(f"app_repo/backend/{f}") for f in ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini")):
        commands.append(["bash", "-lc", "cd app_repo/backend && python -m pytest -q"])
    # Go
    if os.path.exists("app_repo/backend/go.mod"):
        commands.append(["bash", "-lc", "cd app_repo/backend && go test ./..."])
    return commands


def run_tests():
    """프로젝트 테스트 실행.
    1순위: HARNESS_TEST_CMD 환경변수(① tech-stack.md가 지정한 명시 명령).
    2순위: 일반 생태계 자동 탐지(JVM/Node/Python/Go).
    반환: True=green, False=실패, None=러너를 찾지 못함(판정 불가).
    """
    override = os.environ.get("HARNESS_TEST_CMD")
    if override:
        return subprocess.run(["bash", "-lc", override]).returncode == 0

    commands = detect_test_commands()
    if not commands:
        return None  # 러너 미탐지 — silent pass 하지 않고 호출자가 정책 결정
    for cmd in commands:
        if subprocess.run(cmd).returncode != 0:
            return False
    return True


def main() -> int:
    msg = read_commit_message()
    if any(marker in msg for marker in SKIP_MARKERS):
        print("[tdd-gate] scaffold 커밋 — TDD 게이트 skip.")
        return 0

    files = staged_files()
    exts = src_exts()

    def is_test_path(f: str) -> bool:
        low = f.replace("\\", "/").lower()
        name = low.rsplit("/", 1)[-1]
        if TEST_FILE_RE.search(name):
            return True
        # 디렉터리 경로 성분이 테스트 전용 폴더명과 정확히 일치할 때만 (부분문자열 금지)
        return any(part in TEST_DIR_PARTS for part in low.split("/")[:-1])

    impl_changed = any(
        f.endswith(exts) and not is_test_path(f)
        for f in files
    )
    test_changed = any(
        f.endswith(exts) and is_test_path(f)
        for f in files
    )

    if impl_changed and not test_changed:
        print("[tdd-gate] BLOCK: 구현 변경에 대응하는 테스트 변경이 없습니다. "
              "테스트를 먼저 작성하세요(red→green→refactor).", file=sys.stderr)
        return 1

    # 테스트 스위트는 구현 파일이 스테이징된 commit에만 적용한다.
    # (spec/plan/tasks 등 문서-only 커밋은 코드 스위트의 green 여부로 막지 않는다.)
    if impl_changed:
        result = run_tests()
        if result is False:
            print("[tdd-gate] BLOCK: 테스트가 실패했습니다. green 상태에서만 commit 가능합니다.", file=sys.stderr)
            return 1
        if result is None:
            # 러너 미탐지 → silent pass 금지. 명시 명령 또는 명시적 escape 필요.
            if os.environ.get("HARNESS_TDD_ALLOW_NO_RUNNER") == "1":
                print("[tdd-gate] WARN: 테스트 러너를 찾지 못했으나 HARNESS_TDD_ALLOW_NO_RUNNER=1 로 통과. "
                      "(스캐폴드 초기 단계에서만 사용 권장)", file=sys.stderr)
            else:
                print("[tdd-gate] BLOCK: 테스트 러너를 자동 탐지하지 못했습니다. "
                      "HARNESS_TEST_CMD 로 테스트 명령을 지정하세요(① tech-stack.md 핀). "
                      "초기 스캐폴드 등 의도적 우회는 HARNESS_TDD_ALLOW_NO_RUNNER=1.", file=sys.stderr)
                return 1

    print("[tdd-gate] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
