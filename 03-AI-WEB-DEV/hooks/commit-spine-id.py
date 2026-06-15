#!/usr/bin/env python3
"""
Hook: commit-spine-id.py
트리거: commit 직전 (pre-commit / commit-msg)
목적:  커밋 메시지에 스파인 ID가 포함됐는지 검증한다.
       형식: [<SPEC|MOD>/<task>] 요약 (REQ-...)  |  [SCAFFOLD] ...  |  [CO/<판정>] ...
종료코드: 0 = 통과, 1 = 차단
정책: rules/commit-convention.md
"""

import sys
import re


# [SPEC-014/T1] ... (REQ-...)  형태
SPEC_RE = re.compile(r"^\[(SPEC|MOD)-?[A-Z0-9-]*\/T\d+\]")
SCAFFOLD_RE = re.compile(r"^\[SCAFFOLD\]")
CO_RE = re.compile(r"^\[CO\/(dismiss|amend|regenerate)\]")
REQ_RE = re.compile(r"REQ-[A-Z][A-Z0-9-]+\.\d{3}")


def read_commit_message() -> str:
    if len(sys.argv) > 1:
        try:
            return open(sys.argv[1], encoding="utf-8").read()
        except OSError:
            return ""
    return ""


def main() -> int:
    msg = read_commit_message().strip()
    if not msg:
        print("[commit-spine-id] BLOCK: 커밋 메시지를 읽을 수 없습니다.", file=sys.stderr)
        return 1

    first = msg.splitlines()[0]

    if SCAFFOLD_RE.match(first):
        print("[commit-spine-id] PASS (scaffold)")
        return 0

    if CO_RE.match(first):
        print("[commit-spine-id] PASS (change-order)")
        return 0

    if not SPEC_RE.match(first):
        print("[commit-spine-id] BLOCK: 커밋 머리말 형식 오류. "
              "예) [SPEC-014/T1] 요약 (REQ-ORDER-LIST.001)", file=sys.stderr)
        return 1

    if not REQ_RE.search(msg):
        print("[commit-spine-id] BLOCK: 관련 REQ- 스파인 ID가 메시지에 없습니다.", file=sys.stderr)
        return 1

    print("[commit-spine-id] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
