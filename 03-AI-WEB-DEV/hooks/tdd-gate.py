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
import sys
import subprocess


SKIP_MARKERS = ("[SCAFFOLD]",)

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


def run_tests() -> bool:
    """프로젝트 테스트 실행.
    1순위: HARNESS_TEST_CMD 환경변수(① tech-stack.md가 지정한 명시 명령).
    2순위: 일반 생태계 자동 탐지(JVM/Node/Python/Go). 하나라도 실패하면 False.
    """
    override = os.environ.get("HARNESS_TEST_CMD")
    if override:
        return subprocess.run(["bash", "-lc", override]).returncode == 0

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

    if not commands:
        # 러너를 못 찾으면 보수적으로 통과(다른 게이트가 잡도록). HARNESS_TEST_CMD로 명시 권장.
        print("[tdd-gate] WARN: 테스트 러너 자동 탐지 실패. "
              "HARNESS_TEST_CMD 환경변수로 테스트 명령을 지정하세요(① tech-stack.md 참조).",
              file=sys.stderr)
        return True
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
        low = f.lower()
        return ("test" in low or "spec" in low or "__tests__" in low or "_test." in low)

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

    if not run_tests():
        print("[tdd-gate] BLOCK: 테스트가 실패했습니다. green 상태에서만 commit 가능합니다.", file=sys.stderr)
        return 1

    print("[tdd-gate] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
