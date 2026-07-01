#!/usr/bin/env python3
"""harness-core/render/render_screen.py — SCR-*.yaml → renders/SCR-*.render.html.

결정론적 엔진(engine.render_screen) 위임. layout-recommend 스킬·on-save 파이프라인이 호출.

사용:
  python render_screen.py <SCR-*.yaml> [<SCR-*.yaml> ...]
  python render_screen.py --check <SCR-*.yaml>   # 재렌더 후 render_hash 동일성만 검사(파일 미수정)

DP 탐색: screen.template.page(DP-ID) → foundation/design-pages/DP-*.yaml.
출력: <project>/model_repo/renders/<SCR-ID>.render.html
종료코드: 0 = 성공, 1 = 실패(또는 --check 불일치).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402
import ds_assets as ds_assets_mod  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def find_project_root(scr_path: Path) -> Path:
    """SCR 파일에서 상위로 올라가며 foundation/ 를 가진 프로젝트 루트 탐색."""
    for parent in [scr_path.parent] + list(scr_path.parents):
        if (parent / "foundation" / "design-pages").exists():
            return parent
    # model_repo/screens/SCR.yaml → 상위 2단계가 프로젝트 루트
    return scr_path.parents[2] if len(scr_path.parents) >= 3 else scr_path.parent


def load_dp(project_root: Path, dp_id: str) -> dict:
    dp_path = project_root / "foundation" / "design-pages" / f"{dp_id}.yaml"
    if not dp_path.exists():
        return {}
    return yaml.safe_load(dp_path.read_text(encoding="utf-8")) or {}


def render_one(scr_path: Path, check: bool = False) -> int:
    if not scr_path.exists():
        print(f"[render-screen] ❌ 파일 없음: {scr_path}", file=sys.stderr)
        return 1
    scr = yaml.safe_load(scr_path.read_text(encoding="utf-8")) or {}
    screen = scr.get("screen", {})
    scr_id = screen.get("id", scr_path.stem)
    dp_id = (screen.get("template") or {}).get("page", "DP-MAIN")

    project_root = find_project_root(scr_path)
    dp = load_dp(project_root, dp_id)
    if not dp:
        print(f"[render-screen] ⚠ DP '{dp_id}' 없음 — 빈 캔버스로 렌더", file=sys.stderr)

    assets = ds_assets_mod.load_ds_assets(project_root)
    ts = datetime.now(timezone.utc).isoformat()
    html, layout_hash, render_hash = engine.render_screen(scr, dp, timestamp=ts, ds_assets=assets)

    out_dir = project_root / "model_repo" / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{scr_id}.render.html"

    if check:
        # 결정성 검사: 기존 파일이 있으면 render_hash 비교
        if out_path.exists():
            old_hash = engine.compute_render_hash(out_path.read_text(encoding="utf-8"))
            if old_hash != render_hash:
                print(f"[render-screen] ❌ {scr_id}: render_hash 불일치 (재렌더 결과가 기존과 다름)",
                      file=sys.stderr)
                return 1
        # 한 번 더 렌더해 자기 자신과 바이트 동일한지(타임스탬프 제외)
        html2, _, render_hash2 = engine.render_screen(scr, dp, timestamp="2000-01-01T00:00:00+00:00",
                                                       ds_assets=assets)
        if render_hash != render_hash2:
            print(f"[render-screen] ❌ {scr_id}: 비결정적 렌더 (동일 입력 2회 해시 불일치)",
                  file=sys.stderr)
            return 1
        print(f"[render-screen] ✅ {scr_id}: 결정성 OK  layout={layout_hash[:23]}…  render={render_hash[:23]}…")
        return 0

    out_path.write_text(html, encoding="utf-8")
    print(f"[render-screen] ✅ {scr_id} → {out_path.relative_to(project_root).as_posix()}")
    print(f"    layout_hash: {layout_hash}")
    print(f"    render_hash: {render_hash}")
    return 0


def main(argv: list) -> int:
    args = argv[1:]
    check = "--check" in args
    targets = [Path(a) for a in args if not a.startswith("--")]
    if not targets:
        targets = list(Path(".").glob("model_repo/screens/SCR-*.yaml"))
    if not targets:
        print("[render-screen] 렌더할 SCR 파일 없음", file=sys.stderr)
        return 0
    rc = 0
    for t in targets:
        rc |= render_one(t, check=check)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
