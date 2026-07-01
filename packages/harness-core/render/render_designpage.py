#!/usr/bin/env python3
"""harness-core/render/render_designpage.py — DP-*.yaml → design-pages/renders/DP-*.html.

design-page-builder 스킬(①)이 호출. locked 슬롯은 실제 컴포넌트, editable 슬롯은
그리드 오버레이+슬롯명+경계로 시각화한다(PO가 DP 골격을 본다).

사용:
  python render_designpage.py <DP-*.yaml> [...]
  python render_designpage.py --root <project>   # foundation/design-pages/DP-*.yaml 전체
출력: <project>/foundation/design-pages/renders/<DP-ID>.html
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402
import ds_assets as ds_assets_mod  # noqa: E402


def find_project_root(dp_path: Path) -> Path | None:
    """DP 파일에서 상위로 올라가며 foundation/design-system 을 가진 프로젝트 루트 탐색."""
    for parent in dp_path.parents:
        if (parent / "foundation" / "design-system").exists():
            return parent
    return None

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def render_one(dp_path: Path) -> int:
    if not dp_path.exists():
        print(f"[render-dp] ❌ 파일 없음: {dp_path}", file=sys.stderr)
        return 1
    dp = yaml.safe_load(dp_path.read_text(encoding="utf-8")) or {}
    dp_id = dp.get("id", dp_path.stem)
    ts = datetime.now(timezone.utc).isoformat()
    assets = ds_assets_mod.load_ds_assets(find_project_root(dp_path))
    html = engine.render_designpage(dp, timestamp=ts, ds_assets=assets)

    out_dir = dp_path.parent / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{dp_id}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"[render-dp] ✅ {dp_id} → {out_path.as_posix()}")
    return 0


def main(argv: list) -> int:
    args = argv[1:]
    targets: list = []
    if "--root" in args:
        root = Path(args[args.index("--root") + 1])
        targets = sorted((root / "foundation" / "design-pages").glob("DP-*.yaml"))
    else:
        targets = [Path(a) for a in args if not a.startswith("--")]
    if not targets:
        print("[render-dp] 렌더할 DP 파일 없음", file=sys.stderr)
        return 0
    rc = 0
    for t in targets:
        rc |= render_one(t)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
