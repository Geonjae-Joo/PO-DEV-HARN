#!/usr/bin/env python3
"""harness-core/render/ds_assets.py — 시각 충실도 자산 로더 (ADR-002 §3 시각 충실도 레이어).

build_ds_assets.mjs(① 준비단계, ds-bootstrap Phase 9)가 1회 생성·커밋하는 두 정적 자산을 로드한다:
  - foundation/design-system/ds-compiled.css   (실제 DS CSS: 토큰 + 컴파일된 유틸리티)
  - foundation/design-system/ds-fixtures.json  (ref → 기본상태 정적 마크업)

엔진은 이 둘만 읽어 실제 DS 모양으로 렌더한다(프레임워크 무관·결정적). 자산이 없으면
{"css": None, "fixtures": {}} 를 돌려주고, 엔진은 기존 와이어프레임 동작으로 폴백한다
(바이트 동일 → 기존 골든 불변). 컴파일은 렌더 시점이 아니라 자산 생성 시점에 1회만 일어난다.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_ds_assets(project_root: Path | None) -> dict:
    """프로젝트 루트 → {"css": str|None, "fixtures": {ref: {"html": str}}}.

    자산 파일이 없으면 css=None, fixtures={} (엔진 폴백). 순수 파일 IO + JSON 파싱.
    """
    if project_root is None:
        return {"css": None, "fixtures": {}}
    ds_dir = Path(project_root) / "foundation" / "design-system"
    css_path = ds_dir / "ds-compiled.css"
    fx_path = ds_dir / "ds-fixtures.json"

    css = None
    if css_path.exists():
        try:
            css = css_path.read_text(encoding="utf-8")
        except Exception:
            css = None

    fixtures: dict = {}
    if fx_path.exists():
        try:
            data = json.loads(fx_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # "_note" 등 메타 키 제외, html 가진 항목만
                fixtures = {k: v for k, v in data.items()
                            if isinstance(v, dict) and isinstance(v.get("html"), str)}
        except Exception:
            fixtures = {}

    return {"css": css, "fixtures": fixtures}
