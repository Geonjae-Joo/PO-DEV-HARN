#!/usr/bin/env python3
"""
Hook: speckit-artifact-guard.py
트리거: commit-msg (commit-spine-id 다음, blocking)
목적:  `[spec-kit/<stage>]` 커밋 마커가 **프로세스 없이 머리말만** 붙는 단락(short-circuit)을 막는다.
       commit-spine-id.py 는 마커 문자열만 검사하므로(spec-kit 예외 무조건 PASS), 골든패스 v2처럼
       spec.md/plan.md/tasks.md 가 없어도 [spec-kit/plan] 커밋이 통과됐다. 이 가드가 산출물 실재를 강제한다.

검사:
  - [spec-kit/specify] → feature_dir/spec.md 존재
  - [spec-kit/plan]    → feature_dir/spec.md + plan.md 존재
  - [spec-kit/tasks]   → feature_dir/plan.md + tasks.md 존재
  - 그 외 stage(constitution/clarify/analyze/checklist/taskstoissues) 및 비-spec-kit 커밋 → 관심 밖(PASS)

graceful degradation(오차단 방지):
  - spec-kit 마커가 아니면 PASS
  - .specify/feature.json 을 못 찾거나 feature_dir 해석 실패 → WARN 후 PASS
  - 필요한 산출물이 분명히 없을 때만 BLOCK(exit 1)

정책: PROPOSAL-speckit-correct-usage.md C4/C5
종료코드: 0 = 통과/관심밖, 1 = 차단
"""

import json
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

SPECKIT_RE = re.compile(r"^\[spec-kit\/(specify|plan|tasks)\]")
TEMPLATE_MARKER = "[PACK-ID — 도메인명]"  # spec-template 미수정 표식


def read_commit_message() -> str:
    if len(sys.argv) > 1:
        try:
            return open(sys.argv[1], encoding="utf-8").read()
        except OSError:
            return ""
    return ""


def find_specify_root(start: Path):
    for anc in [start, *start.parents]:
        if (anc / ".specify").is_dir():
            return anc
    return None


def resolve_feature_dir(root: Path):
    fj = root / ".specify" / "feature.json"
    if not fj.exists():
        return None
    try:
        data = json.loads(fj.read_text(encoding="utf-8"))
    except Exception:
        return None
    fd = data.get("feature_directory")
    if not fd:
        return None
    p = Path(fd)
    if not p.is_absolute():
        p = root / fd
    return p if p.is_dir() else None


def main() -> int:
    msg = read_commit_message().strip()
    if not msg:
        # 메시지 판독 불가는 commit-spine-id 가 이미 처리. 여기선 관심 밖.
        return 0
    first = msg.splitlines()[0]
    m = SPECKIT_RE.match(first)
    if not m:
        return 0  # spec-kit specify/plan/tasks 마커가 아님 → 관심 밖

    stage = m.group(1)
    root = find_specify_root(Path.cwd())
    if root is None:
        print("[speckit-artifact-guard] WARN: .specify 루트를 못 찾음 — 검사 생략(PASS).", file=sys.stderr)
        return 0
    fdir = resolve_feature_dir(root)
    if fdir is None:
        print("[speckit-artifact-guard] WARN: .specify/feature.json 으로 feature_dir 해석 실패 — "
              "검사 생략(PASS). /speckit-specify 가 feature.json 을 남기는지 확인하세요.", file=sys.stderr)
        return 0

    required = {
        "specify": ["spec.md"],
        "plan": ["spec.md", "plan.md"],
        "tasks": ["plan.md", "tasks.md"],
    }[stage]

    missing = [f for f in required if not (fdir / f).is_file()]
    if missing:
        print(f"[speckit-artifact-guard] BLOCK: [spec-kit/{stage}] 커밋인데 산출물이 없습니다: "
              f"{', '.join(missing)} (feature_dir={fdir}). "
              f"마커만 붙이지 말고 /speckit-{stage} 를 먼저 실행하세요.", file=sys.stderr)
        return 1

    # spec.md 가 미수정 템플릿이면 경고(비차단)
    spec = fdir / "spec.md"
    if "spec.md" in required and spec.is_file():
        try:
            body = spec.read_text(encoding="utf-8")
            if TEMPLATE_MARKER in body or len(body.strip()) < 200:
                print("[speckit-artifact-guard] WARN: spec.md 가 미수정 템플릿/빈 초안으로 보입니다 — "
                      "내용을 확정했는지 확인하세요.", file=sys.stderr)
        except OSError:
            pass

    print(f"[speckit-artifact-guard] PASS ({stage}: {', '.join(required)} 존재)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
