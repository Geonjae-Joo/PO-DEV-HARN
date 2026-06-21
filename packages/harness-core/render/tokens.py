#!/usr/bin/env python3
"""harness-core/render/tokens.py — DS-불가지론 토큰·allowlist 로더 (ADR-002 D4 카탈로그 입력).

정식 토큰 아티팩트가 없을 수 있으므로(프로젝트마다 DS가 다름), **현재 design-system 폴더에 있는 내용**을
토대로 토큰을 추출한다:
  - `foundation/design-system/ds-source/**/*.css` 의 `:root { --name: value }` CSS 변수를 스캔·분류
  - 토큰이 구조화된 DS면 그대로, 아니면 있는 그대로 보여준다(있을 수도/없을 수도 있음).
  - spacing 은 엔진 기본 토큰(engine.DEFAULT_TOKENS)으로 보강.

또한 `ds-allowlist.md`를 description/props/usage/states 까지 풍부하게 파싱한다(카탈로그 갤러리·가이드용).

순수 파싱 + 결정론적 정렬(같은 입력 → 같은 출력).
"""

from __future__ import annotations

import re
from pathlib import Path

# value 가 '단일 색상 값'인지 판정 (box-shadow 처럼 색함수 뒤에 길이 토큰이 붙은 값은 색상 아님)
_COLOR_RE = re.compile(
    r"^\s*(#[0-9a-fA-F]{3,8}|(?:rgba?|hsla?|oklch|hwb|lab|lch)\([^)]*\))\s*$"
)
_DIM_RE = re.compile(r"-?\d*\.?\d+(px|rem|em|vh|vw|%|ch)\b")
_FONT_HINT = ("font", "sans", "serif", "mono", "heading", "family")
_FONT_VAL_HINT = ("system-ui", "sans-serif", "serif", "monospace", "ui-monospace",
                  "roboto", "arial", "segoe", "helvetica")
# --name: value;  (한 줄 선언만; 멀티라인 shadow 등은 첫 줄 기준)
_VAR_RE = re.compile(r"--([a-zA-Z0-9-]+)\s*:\s*([^;]+);")


def _classify(name: str, value: str) -> str:
    n = name.lower()
    v = value.strip().lower()
    # shadow/elevation 등 복합 값은 색상·치수 어디에도 넣지 않음(카탈로그 미표시 'other')
    if any(k in n for k in ("shadow", "elevation", "gradient")):
        return "other"
    if _COLOR_RE.match(value) or n.startswith("color") or "color" in n or n in ("bg", "text", "accent", "border"):
        if _COLOR_RE.match(value) or v in ("currentcolor", "transparent"):
            return "color"
    if any(h in n for h in _FONT_HINT) or any(h in v for h in _FONT_VAL_HINT):
        return "font"
    if _DIM_RE.search(value) or any(h in n for h in ("space", "gap", "size", "radius", "width", "height", "spacing")):
        return "dimension"
    return "other"


def load_tokens(project_root: Path) -> dict:
    """
    프로젝트 루트 → {colors:[{name,value}], fonts:[...], dimensions:[...], other:[...], sources:[...]}.
    각 카테고리는 name 오름차순 정렬, 중복 name 은 첫 출현(보통 light 테마) 유지.
    """
    ds_root = project_root / "foundation" / "design-system"
    css_files = []
    src = ds_root / "ds-source"
    if src.exists():
        css_files = sorted(src.rglob("*.css"))
        css_files = [f for f in css_files if "node_modules" not in f.parts]

    seen: dict[str, str] = {}
    cats: dict[str, list] = {"color": [], "font": [], "dimension": [], "other": []}
    sources = []
    for f in css_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        found_here = False
        for m in _VAR_RE.finditer(text):
            name, value = m.group(1), m.group(2).strip()
            if name in seen:
                continue
            seen[name] = value
            cats[_classify(name, value)].append({"name": name, "value": value})
            found_here = True
        if found_here:
            try:
                sources.append(f.relative_to(project_root).as_posix())
            except ValueError:
                sources.append(f.name)

    for k in cats:
        cats[k].sort(key=lambda d: d["name"])
    return {
        "colors": cats["color"], "fonts": cats["font"],
        "dimensions": cats["dimension"], "other": cats["other"],
        "sources": sorted(sources),
    }


def load_allowlist_full(allowlist_path: Path) -> list:
    """
    ds-allowlist.md → [{name, description, props:[...], usage, states:[...]}], name 오름차순.
    states 는 선택적 `- **states**: a, b, c` 라인(§9 결정: 없으면 카탈로그가 기본 상태셋 사용).
    """
    if not allowlist_path.exists():
        return []
    text = allowlist_path.read_text(encoding="utf-8")
    comps: dict[str, dict] = {}
    cur = None
    for line in text.splitlines():
        h = re.match(r"^##\s+(\w+)", line)
        if h:
            cur = h.group(1)
            comps[cur] = {"name": cur, "description": "", "props": [], "usage": "", "states": []}
            continue
        if not cur:
            continue
        dm = re.match(r"-\s+\*?\*?description\*?\*?:\s*(.+)", line, re.IGNORECASE)
        if dm:
            comps[cur]["description"] = dm.group(1).strip()
            continue
        pm = re.match(r"-\s+\*?\*?props?\*?\*?:\s*(.+)", line, re.IGNORECASE)
        if pm:
            comps[cur]["props"] = [p.split(":")[0].strip() for p in pm.group(1).split(",") if p.strip()]
            continue
        um = re.match(r"-\s+\*?\*?usage\*?\*?:\s*(.+)", line, re.IGNORECASE)
        if um:
            comps[cur]["usage"] = um.group(1).strip()
            continue
        sm = re.match(r"-\s+\*?\*?states?\*?\*?:\s*(.+)", line, re.IGNORECASE)
        if sm:
            comps[cur]["states"] = [s.strip() for s in sm.group(1).split(",") if s.strip()]
            continue
    return [comps[k] for k in sorted(comps.keys())]
