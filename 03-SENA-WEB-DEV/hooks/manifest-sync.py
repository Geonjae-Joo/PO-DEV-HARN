#!/usr/bin/env python3
"""
Hook: manifest-sync.py
트리거: commit 이후 (post-commit)
목적:  ②의 spec 팩 link-manifest를 app_repo/specs/ 와 동기화한다.
       - input/spec-pack/PACK-*/spec.yaml → app_repo/specs/PACK-*/spec.yaml 반영
       - Phase α 이후 생성된 shell 경로를 screens[].shell_ref 에 갱신
종료코드: 0 = 성공(비차단 — post-commit이므로 실패해도 commit은 유지)
정책: README(③) Phase α/β, ②의 link-manifest
"""

import sys
import shutil
from pathlib import Path


SRC = Path("input/spec-pack")
DST = Path("app_repo/specs")


def sync_packs() -> int:
    if not SRC.exists():
        print(f"[manifest-sync] SKIP: {SRC} 없음.")
        return 0
    DST.mkdir(parents=True, exist_ok=True)
    count = 0
    for pack in sorted(SRC.glob("PACK-*")):
        if not pack.is_dir():
            continue
        target = DST / pack.name
        target.mkdir(parents=True, exist_ok=True)
        for f in pack.glob("*"):
            if f.is_file():
                shutil.copy2(f, target / f.name)
                count += 1
    print(f"[manifest-sync] {count}개 파일 동기화 (→ {DST}).")
    return 0


def main() -> int:
    try:
        return sync_packs()
    except Exception as e:
        # post-commit이므로 commit을 되돌리지 않는다. 경고만.
        print(f"[manifest-sync] WARN: 동기화 중 오류: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
