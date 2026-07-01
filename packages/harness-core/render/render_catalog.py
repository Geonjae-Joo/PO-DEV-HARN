#!/usr/bin/env python3
"""harness-core/render/render_catalog.py — DS 카탈로그(대시보드) 생성 (ADR-002 D4).

토큰(현재 design-system 폴더 기반) + ds-allowlist 컴포넌트 메타 → 시각 카탈로그.
PO가 이름으로 디자인을 지시할 근거(P2 "백지 캔버스" 제거). ② 챗봇 읽기전용 패널로 노출 예정.

사용:
  python render_catalog.py --root <projects/id>
  python render_catalog.py --root <projects/id> --check   # 결정성(재생성 후 동일) 검사
출력: <project>/foundation/design-system/catalog/index.html
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine   # noqa: E402
import tokens as tokens_mod   # noqa: E402
import ds_assets as ds_assets_mod   # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def build(project_root: Path, timestamp: str = "") -> str:
    toks = tokens_mod.load_tokens(project_root)
    allowlist = project_root / "foundation" / "design-system" / "ds-allowlist.md"
    comps = tokens_mod.load_allowlist_full(allowlist)
    assets = ds_assets_mod.load_ds_assets(project_root)
    return engine.render_catalog(toks, comps, timestamp=timestamp, ds_assets=assets)


def main(argv: list) -> int:
    args = argv[1:]
    if "--root" not in args:
        print("[catalog] --root <projects/id> 필요", file=sys.stderr)
        return 2
    project_root = Path(args[args.index("--root") + 1])
    check = "--check" in args

    if check:
        h1 = engine.compute_render_hash(build(project_root, "T1"))
        h2 = engine.compute_render_hash(build(project_root, "T2-diff"))
        if h1 != h2:
            print("[catalog] ❌ 비결정적 카탈로그 (타임스탬프 외 차이)", file=sys.stderr)
            return 1
        print(f"[catalog] ✅ 결정성 OK  render={h1[:23]}…")
        return 0

    ts = datetime.now(timezone.utc).isoformat()
    html = build(project_root, ts)
    out_dir = project_root / "foundation" / "design-system" / "catalog"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    n_colors = len(tokens_mod.load_tokens(project_root).get("colors", []))
    n_comps = len(tokens_mod.load_allowlist_full(
        project_root / "foundation" / "design-system" / "ds-allowlist.md"))
    print(f"[catalog] ✅ {out_path.as_posix()}")
    print(f"    색상 토큰 {n_colors}개 · 컴포넌트 {n_comps}개")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
