#!/usr/bin/env python3
"""
Hook: tdd-gate.py
트리거: commit 직전 (pre-commit)
목적:  TDD 강제 — 대응 테스트가 없거나 실패한 구현 커밋을 차단한다.
       scaffold 커밋([SCAFFOLD] 마커)은 예외 처리(skip).
종료코드: 0 = 통과(commit 허용), 1 = 차단(commit 거부)
정책: rules/tdd-policy.md
"""

import sys
import subprocess


SKIP_MARKERS = ("[SCAFFOLD]",)


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
    """프로젝트 테스트 실행. backend(gradle/maven)·frontend(npm) 중 존재하는 것을 시도."""
    # 실제 프로젝트 구성에 맞게 커맨드를 조정한다. 하나라도 실패하면 False.
    commands = []
    import os
    if os.path.exists("app_repo/backend/build.gradle") or os.path.exists("app_repo/backend/pom.xml"):
        commands.append(["bash", "-lc", "cd app_repo/backend && (./gradlew test || mvn -q test)"])
    if os.path.exists("app_repo/frontend/package.json"):
        commands.append(["bash", "-lc", "cd app_repo/frontend && npm test --silent"])
    if not commands:
        # 테스트 러너를 못 찾으면 보수적으로 통과(다른 게이트가 잡도록). 경고만 출력.
        print("[tdd-gate] WARN: 테스트 러너를 찾지 못했습니다. 테스트 구성 여부를 확인하세요.", file=sys.stderr)
        return True
    for cmd in commands:
        r = subprocess.run(cmd)
        if r.returncode != 0:
            return False
    return True


def main() -> int:
    msg = read_commit_message()
    if any(marker in msg for marker in SKIP_MARKERS):
        print("[tdd-gate] scaffold 커밋 — TDD 게이트 skip.")
        return 0

    files = staged_files()
    impl_changed = any(
        f.endswith((".java", ".ts", ".tsx"))
        and "test" not in f.lower()
        and "spec" not in f.lower()
        for f in files
    )
    test_changed = any(
        ("test" in f.lower() or "spec" in f.lower())
        and f.endswith((".java", ".ts", ".tsx"))
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
