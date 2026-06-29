#!/usr/bin/env python3
"""
dp-render.py
Trigger: Claude Code PostToolUse(Write|Edit) hook — DP-*.yaml 저장 직후.
역할: design page YAML → foundation/design-pages/renders/DP-*.html 렌더.

호출 규약(현행 Claude Code 훅):
  - 훅 payload(JSON)가 stdin 으로 들어온다: {"tool_input": {"file_path": "...", ...}, ...}
  - 파일 경로 필터는 이 스크립트가 한다 (DP-*.yaml 만 대상).
  - PostToolUse 이므로 파일은 이미 디스크에 기록됨.
종료코드: 0 = 완료/대상아님 (렌더 실패도 0 — 빌드 블로킹 없음, stderr 경고만).
"""

from __future__ import annotations

import sys
import json
import subprocess
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# render_designpage.py 위치: packages/harness-core/render/
_HOOK_DIR = Path(__file__).resolve().parent          # packages/plugin-prerequisite/hooks/
_RENDER_SCRIPT = _HOOK_DIR.parents[1] / "harness-core" / "render" / "render_designpage.py"


def resolve_target() -> Path | None:
    """저장된 파일 경로 결정. DP-*.yaml 이 아니면 None(스킵)."""
    file_path: str | None = None

    # 1) 훅 stdin payload
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                payload = json.loads(raw)
                file_path = (payload.get("tool_input") or {}).get("file_path")
        except Exception:
            file_path = None

    # 2) argv 폴백
    if not file_path:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        if args:
            file_path = args[0]

    if not file_path:
        return None

    p = Path(file_path)
    # DP-*.yaml 만 대상
    if not (p.suffix == ".yaml" and p.stem.startswith("DP-")):
        return None
    return p


def main() -> int:
    target = resolve_target()
    if target is None:
        return 0  # 대상 파일 아님 — 조용히 통과

    if not target.exists():
        print(f"[dp-render] WARN: 파일 없음 — {target}", file=sys.stderr)
        return 0

    if not _RENDER_SCRIPT.exists():
        print(f"[dp-render] WARN: render_designpage.py 없음 — {_RENDER_SCRIPT}", file=sys.stderr)
        return 0

    result = subprocess.run(
        [sys.executable, str(_RENDER_SCRIPT), str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0 and result.stderr:
        print(f"[dp-render] WARN: 렌더 실패\n{result.stderr}", file=sys.stderr)

    return 0  # 렌더 실패도 빌드 블로킹 안 함


if __name__ == "__main__":
    sys.exit(main())
