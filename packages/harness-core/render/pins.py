#!/usr/bin/env python3
"""harness-core/render/pins.py — 해시 핀 계산 단일 출처 (ADR-002 D5).

②(spec-generator: pinned_contract 작성)와 ③(Phase α 해시 가드)가 **같은 코드**로
layout_hash·render_hash 를 계산하도록 한다(ADR-001 "복사 대신 참조" — 도구 간 강제 일치).

engine 은 순수(파일 IO 없음)이므로, 여기서 SCR/DP 파일 로드 + DP 탐색을 담당하고
계산은 engine 에 위임한다.

CLI:
  python pins.py <SCR-*.yaml>            # version/layout_hash/render_hash 출력(텍스트)
  python pins.py --json <SCR-*.yaml>     # JSON 출력
  python pins.py --verify <SCR-*.yaml> --expect-layout sha256:... [--expect-render sha256:...]
                                         # 핀 일치 검증 (불일치 → exit 1, ③ Phase α 가드용)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


import re as _re

_REAL_HASH_RE = _re.compile(r"^sha256:[0-9a-f]{64}$")


def is_placeholder_hash(value) -> bool:
    """
    핀 값이 '아직 미작성(placeholder)'인지 판정하는 **단일 출처**.
    실제 계산 핀은 항상 `sha256:<64 hex 소문자>`. 그 외(빈값·'sha256:...'·'sha256:golden'·
    'golden'·비-64자 등)는 전부 placeholder로 본다.
    ②(spec-pack-guard) ③(layout-hash-guard)가 동일 판정을 쓰도록 공유한다(D5 단일 출처).
    """
    if value is None:
        return True
    return not _REAL_HASH_RE.match(str(value).strip())


def find_project_root(scr_path: Path) -> Path:
    for parent in [scr_path.parent] + list(scr_path.parents):
        if (parent / "foundation" / "design-pages").exists():
            return parent
    return scr_path.parents[2] if len(scr_path.parents) >= 3 else scr_path.parent


def load_screen_and_dp(scr_path: Path) -> tuple:
    """SCR yaml 로드 + template.page 가 가리키는 DP yaml 로드. (scr_doc, dp_doc) 반환."""
    scr = yaml.safe_load(scr_path.read_text(encoding="utf-8")) or {}
    dp_id = ((scr.get("screen") or {}).get("template") or {}).get("page", "DP-MAIN")
    root = find_project_root(scr_path)
    dp_path = root / "foundation" / "design-pages" / f"{dp_id}.yaml"
    dp = yaml.safe_load(dp_path.read_text(encoding="utf-8")) or {} if dp_path.exists() else {}
    return scr, dp


def compute_pins(scr_path: Path) -> dict:
    """SCR 경로 → {version, layout_hash, render_hash}. 핀의 단일 출처."""
    scr, dp = load_screen_and_dp(scr_path)
    version = (scr.get("screen") or {}).get("version")
    # 고정 타임스탬프로 렌더(타임스탬프는 어차피 render_hash 에서 제외되지만 명시적으로 비움)
    _, layout_hash, render_hash = engine.render_screen(scr, dp, timestamp="")
    return {"version": version, "layout_hash": layout_hash, "render_hash": render_hash}


def _main(argv: list) -> int:
    args = argv[1:]
    as_json = "--json" in args
    verify = "--verify" in args
    expect_layout = None
    expect_render = None
    if "--expect-layout" in args:
        expect_layout = args[args.index("--expect-layout") + 1]
    if "--expect-render" in args:
        expect_render = args[args.index("--expect-render") + 1]
    targets = [Path(a) for a in args if not a.startswith("--") and
               a not in (expect_layout or "", expect_render or "")]
    if not targets:
        print("[pins] SCR 파일 경로 필요", file=sys.stderr)
        return 2

    rc = 0
    for scr_path in targets:
        if not scr_path.exists():
            print(f"[pins] ❌ 파일 없음: {scr_path}", file=sys.stderr)
            rc = 1
            continue
        pins = compute_pins(scr_path)
        if verify:
            ok = True
            if expect_layout and pins["layout_hash"] != expect_layout:
                print(f"[pins] ❌ {scr_path.stem}: layout_hash 불일치\n"
                      f"    expected {expect_layout}\n    actual   {pins['layout_hash']}",
                      file=sys.stderr)
                ok = False
            if expect_render and pins["render_hash"] != expect_render:
                print(f"[pins] ❌ {scr_path.stem}: render_hash 불일치\n"
                      f"    expected {expect_render}\n    actual   {pins['render_hash']}",
                      file=sys.stderr)
                ok = False
            if ok:
                print(f"[pins] ✅ {scr_path.stem}: 핀 일치")
            else:
                rc = 1
        elif as_json:
            print(json.dumps({"id": scr_path.stem, **pins}, ensure_ascii=False))
        else:
            print(f"{scr_path.stem}:")
            print(f"  version: {pins['version']}")
            print(f"  layout_hash: {pins['layout_hash']}")
            print(f"  render_hash: {pins['render_hash']}")
    return rc


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
