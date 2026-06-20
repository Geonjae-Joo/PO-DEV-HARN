#!/usr/bin/env python3
"""
Hook: commit-spine-id.py
트리거: commit 직전 (pre-commit / commit-msg)
목적:  커밋 메시지에 스파인 ID가 포함됐는지 검증한다.
       형식: [<PACK|SPEC|MOD>/<task>] 요약 (REQ-...)  |  [SCAFFOLD] ...  |  [CO/<판정>] ...  |  [E2E/JRN-...] ...
       PACK-  도메인 spec 팩 (②가 발행, ③ 도메인 구현 단위)
       SPEC-  플랫폼/baseline spec (예: SPEC-000, SPEC-OPS-000)
       MOD    모듈 단위 변경
       E2E    화면 간 여정(JRN-) Playwright E2E (③ Phase γ)
종료코드: 0 = 통과, 1 = 차단
정책: rules/commit-convention.md
"""

import sys
import re

# Windows 콘솔(cp949 등) 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


# [PACK-ORDER/T001] ... (REQ-...)  형태
SPEC_RE = re.compile(r"^\[(PACK|SPEC|MOD)-?[A-Z0-9-]*\/T\d+\]")
# baseline 사유 토큰: (baseline) / (ops baseline) 등 괄호 안에 'baseline' 포함
BASELINE_RE = re.compile(r"\([^)]*baseline[^)]*\)", re.IGNORECASE)
SCAFFOLD_RE = re.compile(r"^\[SCAFFOLD\]")
CO_RE = re.compile(r"^\[CO\/(dismiss|amend|regenerate)\]")
# [E2E/JRN-ORDER-REFUND] ... — 화면 간 여정 Playwright E2E (③ Phase γ). JRN-가 스파인 ID 역할.
E2E_RE = re.compile(r"^\[E2E\/JRN-[A-Z0-9-]+\]")
# spec-kit SDD 산출물(spec/plan/tasks 등) 자동 커밋 예외.
# 이 커밋들은 코드가 아니라 명세 문서이며 아직 T###/REQ-가 없으므로 면제한다.
# git-config.yml의 auto_commit 메시지가 이 형식을 사용한다: [spec-kit/<stage>] ...
SPECKIT_RE = re.compile(r"^\[spec-kit\/(constitution|specify|clarify|plan|tasks|analyze|checklist|taskstoissues)\]")
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

    if E2E_RE.match(first):
        print("[commit-spine-id] PASS (e2e journey)")
        return 0

    if SPECKIT_RE.match(first):
        print("[commit-spine-id] PASS (spec-kit artifact)")
        return 0

    m = SPEC_RE.match(first)
    if not m:
        print("[commit-spine-id] BLOCK: 커밋 머리말 형식 오류. "
              "예) [PACK-ORDER/T001] 요약 (REQ-ORDER-LIST.001)", file=sys.stderr)
        return 1

    # PACK/MOD(도메인 작업)은 관련 REQ- 필수. SPEC-(baseline)은 REQ- 대신 (baseline) 사유 토큰 필수.
    prefix = m.group(1)
    if prefix in ("PACK", "MOD") and not REQ_RE.search(msg):
        print("[commit-spine-id] BLOCK: 관련 REQ- 스파인 ID가 메시지에 없습니다.", file=sys.stderr)
        return 1
    if prefix == "SPEC" and not (REQ_RE.search(msg) or BASELINE_RE.search(msg)):
        print("[commit-spine-id] BLOCK: SPEC- 커밋은 REQ- 또는 (baseline)/(ops baseline) 사유 토큰이 "
              "필요합니다 (commit-convention.md). 예) [SPEC-000/T003] JWT 인증 필터 (baseline)", file=sys.stderr)
        return 1

    print("[commit-spine-id] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
