#!/usr/bin/env python3
"""harness-core/render/engine.py — ADR-002 결정론적 렌더 엔진 (공용 코어).

책임:
  - DP 캔버스 정규화(신규 canvas 모델 + 레거시 평면 slots 하위호환)
  - SCR layout position resolve (반응형 그리드 정수 좌표; shorthand→int; 레거시→자동변환; 자동강등)
  - 토큰→CSS, 컴포넌트→HTML, 그리드 배치 → 결정론적 HTML
  - layout_hash / render_hash 계산

결정성 계약(계약 명세 §3):
  - LF 줄바꿈, 2-space 들여쓰기, UTF-8, 후행 공백 없음
  - 요소 속성 알파벳 정렬, CSS 선언 알파벳 정렬, dict 직렬화 키 정렬
  - 인라인 style 금지(토큰 컴파일 CSS만 <style>에), 외부 CDN/폰트 금지
  - rendered-at 주석 줄만 render_hash 에서 제외

외부 의존: pyyaml(파일 로드 시), 표준 라이브러리만. ds_closure(allowlist)는 선택적.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Windows 콘솔(cp949 등) 유니코드 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# ── 기본 토큰 (token-only 치수; 별도 토큰 파일은 키스톤 범위 밖) ────────────────────
DEFAULT_TOKENS = {
    "space-0": 0, "space-1": 4, "space-2": 8, "space-3": 12,
    "space-4": 16, "space-5": 24, "space-6": 32, "space-8": 48,
}
SYSTEM_FONT = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
               '"Helvetica Neue", Arial, "Noto Sans KR", sans-serif')

# ADR 결정 1 — 기본 브레이크포인트
DEFAULT_BREAKPOINTS = [
    {"name": "lg", "min": 1280, "columns": 12},
    {"name": "md", "min": 768, "columns": 8},
    {"name": "sm", "min": 0, "columns": 4},
]
DEFAULT_GRID = {"columns": 12, "gap": "space-4", "max_width": 1440}

SHORTHAND = {"full": 1.0, "half": 0.5, "third": 1 / 3, "quarter": 0.25}

# rendered-at 주석 (render_hash 제외 대상)
TIMESTAMP_RE = re.compile(r"^<!-- rendered-at: .* -->\n?", re.MULTILINE)

# ADR 결정 3 — DS 카탈로그 표준 상태(반응) 세트
DEFAULT_STATES = ["default", "hover", "focus", "active", "disabled",
                  "loading", "error", "selected", "read-only", "empty"]
# 컴포넌트별 해당 상태(allowlist에 states 선언이 없을 때의 기본 추정; §9 결정)
STATES_BY_REF = {
    "Button": ["default", "hover", "focus", "active", "disabled", "loading"],
    "Input": ["default", "focus", "disabled", "error", "read-only"],
    "Textarea": ["default", "focus", "disabled", "error", "read-only"],
    "Select": ["default", "focus", "disabled", "error"],
    "Checkbox": ["default", "selected", "disabled"],
    "Switch": ["default", "selected", "disabled"],
    "Table": ["default", "loading", "empty"],
    "DataTable": ["default", "loading", "empty"],
    "Badge": ["default", "selected"],
    "Card": ["default"],
    "FilterBar": ["default"],
    "Dialog": ["default"],
    "Tabs": ["default", "selected"],
    "DropdownMenu": ["default", "disabled"],
    "Form": ["default", "error"],
    "Header": ["default"],
    "Breadcrumb": ["default"],
    "Separator": ["default"],
}

# 컴포넌트 ref → (HTML 태그, void 여부)
TAG_MAP = {
    "Button": ("button", False),
    "Input": ("input", True),
    "Select": ("select", False),
    "Table": ("table", False),
    "DataTable": ("table", False),
    "Checkbox": ("input", True),
    "Badge": ("span", False),
    "Card": ("div", False),
    "Header": ("div", False),
    "Breadcrumb": ("nav", False),
    "FilterBar": ("div", False),
    "Separator": ("hr", True),
    "Dialog": ("div", False),
    "Tabs": ("div", False),
    "DropdownMenu": ("div", False),
    "Form": ("form", False),
}


# ── 토큰 resolve ──────────────────────────────────────────────────────────────

def token_px(value) -> int:
    """token 명(space-4) 또는 정수 → px 정수."""
    if isinstance(value, int):
        return value
    return DEFAULT_TOKENS.get(str(value), 0)


def resolve_span(value, columns: int) -> int:
    """col_span shorthand(full/half/third/quarter) 또는 정수 → 정수 컬럼 수."""
    if isinstance(value, bool):  # 방어
        return columns
    if isinstance(value, int):
        return max(1, value)
    frac = SHORTHAND.get(str(value))
    if frac is None:
        return columns  # 알 수 없는 값 → full
    return max(1, round(columns * frac))


# ── DP 캔버스 정규화 (신규 canvas 모델 + 레거시 평면 slots) ────────────────────────

def normalize_canvas(dp: dict) -> dict:
    """DP doc → {grid, breakpoints, slots:[{id,editable,grid_columns,overflow,locks}], components}."""
    canvas = dp.get("canvas")
    slots_raw = dp.get("slots") or []
    components = dp.get("components") or []
    is_new = bool(canvas) and slots_raw and isinstance(slots_raw[0], dict)

    if is_new:
        grid = {**DEFAULT_GRID, **(canvas.get("grid") or {})}
        bps = canvas.get("breakpoints") or DEFAULT_BREAKPOINTS
        slots = []
        for s in slots_raw:
            editable = bool(s.get("editable", True))
            slots.append({
                "id": s.get("id"),
                "editable": editable,
                "grid_columns": int(s.get("grid_columns", grid.get("columns", 12))),
                "overflow": s.get("overflow", "scroll-y" if editable else None),
                "locks": list(s.get("locks") or []),
            })
    else:
        # 레거시 평면 slots: 모두 editable, canvas 미선언
        grid = dict(DEFAULT_GRID)
        bps = list(DEFAULT_BREAKPOINTS)
        slots = []
        for s in slots_raw:
            sid = s if isinstance(s, str) else s.get("id")
            slots.append({
                "id": sid, "editable": True,
                "grid_columns": grid.get("columns", 12),
                "overflow": None, "locks": [],
            })
    return {"grid": grid, "breakpoints": bps, "slots": slots,
            "components": components, "is_new": is_new}


# ── 위치 resolve (반응형 정수 좌표) ─────────────────────────────────────────────

def _order_key(item: dict):
    pos = item.get("position", {}) or {}
    base = pos.get("base")
    if base:
        return (0, int(base.get("row", 1)), int(base.get("col_start", 1)), str(item.get("id", "")))
    return (0, int(pos.get("order", 999)), 0, str(item.get("id", "")))


def _resolve_coord(coord: dict, cols: int) -> dict:
    return {
        "col_start": int(coord.get("col_start", 1)),
        "col_span": resolve_span(coord.get("col_span", "full"), cols),
        "row": int(coord.get("row", 1)),
        "row_span": int(coord.get("row_span", 1)),
        "hidden": bool(coord.get("hidden", False)),
    }


def resolve_positions(scr: dict, dp: dict) -> dict:
    """
    각 layout item의 브레이크포인트별 정수 좌표를 결정론적으로 계산.
    반환: { cmp_id: { bp_name: {col_start,col_span,row,row_span,hidden} } }

    규칙(계약 명세 §1):
      - 가장 큰 bp(lg) = base 사용. 레거시(base 없음) = full-width 세로 스택.
      - 작은 bp = at.<bp> 오버라이드 또는 자동강등(full-width 세로 스택).
      - 정렬: (base.row, base.col_start) 또는 (order) 오름차순.
    """
    canvas = normalize_canvas(dp)
    bps = canvas["breakpoints"]
    if not bps:
        return {}
    largest = max(bps, key=lambda b: b["min"])["name"]

    by_slot = defaultdict(list)
    for it in scr.get("layout", []) or []:
        by_slot[(it.get("position", {}) or {}).get("slot")].append(it)

    resolved: dict = {}
    for slot_id, items in by_slot.items():
        ordered = sorted(items, key=_order_key)
        for bp in bps:
            cols = bp["columns"]
            # 1패스: 명시 좌표(base 또는 at.<bp>) 수집 → 점유 행 집합
            explicit_coords = []   # [(cid, coord_or_None)]
            occupied_rows = set()
            for it in ordered:
                cid = it.get("id")
                pos = it.get("position", {}) or {}
                src = pos.get("base") if bp["name"] == largest else (pos.get("at") or {}).get(bp["name"])
                coord = _resolve_coord(src, cols) if src else None
                if coord and not coord["hidden"]:
                    occupied_rows.add(coord["row"])
                explicit_coords.append((cid, coord))
            # 2패스: 자동 강등 항목은 명시 항목이 점유한 행을 건너뛰며 연속 스택(ADR 결정 2; 겹침 0)
            cursor = 0
            for cid, coord in explicit_coords:
                if coord is None:
                    cursor += 1
                    while cursor in occupied_rows:
                        cursor += 1
                    coord = {"col_start": 1, "col_span": cols, "row": cursor,
                             "row_span": 1, "hidden": False}
                resolved.setdefault(cid, {})[bp["name"]] = coord
    return resolved


# ── 해시 ──────────────────────────────────────────────────────────────────────

def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_layout_hash(scr: dict, dp: dict) -> str:
    """layout_hash = sha256(canonical_json(layout_contract)) — 계약 명세 §4."""
    canvas = normalize_canvas(dp)
    resolved = resolve_positions(scr, dp)
    items = []
    for it in scr.get("layout", []) or []:
        cid = it.get("id")
        items.append({
            "id": cid,
            "slot": (it.get("position", {}) or {}).get("slot"),
            "resolved": resolved.get(cid, {}),
        })
    items.sort(key=lambda x: str(x["id"]))
    contract = {
        "grid": canvas["grid"],
        "breakpoints": canvas["breakpoints"],
        "items": items,
    }
    digest = hashlib.sha256(_canonical(contract).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_render_hash(html: str) -> str:
    """render_hash = sha256(rendered-at 주석 제거 + LF 정규화) — 계약 명세 §4."""
    stripped = TIMESTAMP_RE.sub("", html)
    stripped = stripped.replace("\r\n", "\n")
    digest = hashlib.sha256(stripped.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


# ── HTML 빌더 (결정론적) ────────────────────────────────────────────────────────

def _attrs(d: dict) -> str:
    """속성 dict → 알파벳 정렬된 ' k="v"' 문자열."""
    parts = []
    for k in sorted(d.keys()):
        v = d[k]
        if v is None:
            continue
        parts.append(f'{k}="{_esc(str(v))}"')
    return (" " + " ".join(parts)) if parts else ""


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _component_html(ref: str, props: dict, cmp_id: str | None, label: str, indent: int) -> list:
    """DS 컴포넌트 1개 → HTML 라인 목록(시각 뷰, 실제 동작 아님)."""
    pad = "  " * indent
    tag, void = TAG_MAP.get(ref, ("div", False))
    attrs = {"data-ref": ref}
    if cmp_id:
        attrs["data-cmp"] = cmp_id
    text = label or (props.get("label") if isinstance(props, dict) else None) or ref

    if ref in ("Table", "DataTable"):
        attrs["class"] = "ds-table"
        lines = [f"{pad}<table{_attrs(attrs)}>"]
        cols = []
        if isinstance(props, dict):
            cols = props.get("columns") or props.get("headers") or []
        ths = "".join(f"<th>{_esc(str(c))}</th>" for c in cols) or "<th>—</th>"
        lines.append(f"{pad}  <thead><tr>{ths}</tr></thead>")
        lines.append(f"{pad}  <tbody><!-- 데이터 파생 렌더, 행 없음 --></tbody>")
        lines.append(f"{pad}</table>")
        return lines

    if void:
        if ref == "Input":
            attrs["placeholder"] = (props.get("placeholder") if isinstance(props, dict) else None) or text
            attrs["type"] = (props.get("type") if isinstance(props, dict) else None) or "text"
        elif ref == "Checkbox":
            attrs["type"] = "checkbox"
        return [f"{pad}<{tag}{_attrs(attrs)} />"]

    return [f"{pad}<{tag}{_attrs(attrs)}>{_esc(str(text))}</{tag}>"]


def _slot_tag(slot_id: str) -> str:
    return {"header": "header", "footer": "footer", "content": "main"}.get(slot_id, "section")


def _label_of(item: dict) -> str:
    props = item.get("props") or {}
    return props.get("label") or (item.get("meta") or {}).get("label") or item_ref(item)


def item_ref(item: dict) -> str:
    return (item.get("source") or {}).get("ref", "") or ""


# ── CSS 빌더 ──────────────────────────────────────────────────────────────────

def _css_rule(selector: str, decls: dict) -> str:
    body = ";".join(f"{k}:{decls[k]}" for k in sorted(decls.keys()))
    return f"{selector}{{{body}}}"


def _build_css(canvas: dict, resolved: dict, editable_slot_ids: list) -> list:
    """결정론적 CSS 라인 목록. base(가장 작은 bp) → @media 오름차순."""
    grid = canvas["grid"]
    gap = token_px(grid.get("gap", "space-4"))
    maxw = int(grid.get("max_width", 1440))
    bps = canvas["breakpoints"]
    bps_asc = sorted(bps, key=lambda b: b["min"])  # sm, md, lg
    base_bp = bps_asc[0]["name"]
    media_bps = bps_asc[1:]
    cols_by_name = {b["name"]: b["columns"] for b in bps}

    # D6 렌더 환경 동결: 행 최소 높이·텍스트 영역 높이를 space 토큰으로 고정(줄바꿈 변동 격리, magic number 금지)
    row_min = token_px("space-8")
    lines = ["* { box-sizing: border-box; }",
             _css_rule("body", {"font-family": SYSTEM_FONT, "margin": "0"}),
             _css_rule(".page", {"margin": "0 auto", "max-width": f"{maxw}px",
                                 "padding": f"{gap}px"}),
             _css_rule(".ds-table", {"border-collapse": "collapse", "min-height": f"{row_min}px",
                                     "width": "100%"})]

    # 슬롯 컨테이너 그리드 (editable 슬롯만)
    slot_map = {s["id"]: s for s in canvas["slots"]}
    for sid in editable_slot_ids:
        slot = slot_map.get(sid, {})
        sel = f'[data-slot="{sid}"]'
        decls = {"display": "grid", "gap": f"{gap}px",
                 "grid-auto-rows": f"minmax({row_min}px,auto)",   # ADR 결정 1: 행 min = space 토큰
                 "grid-template-columns": f"repeat({cols_by_name.get(base_bp, 4)},1fr)"}
        if slot.get("overflow") == "scroll-y":
            decls["overflow-y"] = "auto"
        lines.append(_css_rule(sel, decls))

    # 아이템 좌표 (base = 가장 작은 bp)
    for cid in sorted(resolved.keys()):
        c = resolved[cid][base_bp]
        sel = f'[data-cmp="{_esc(cid)}"]'
        if c.get("hidden"):
            lines.append(_css_rule(sel, {"display": "none"}))
        else:
            lines.append(_css_rule(sel, {
                "grid-column": f"{c['col_start']} / span {c['col_span']}",
                "grid-row": str(c["row"]),
            }))

    # 미디어 쿼리 (오름차순)
    for bp in media_bps:
        name = bp["name"]
        inner = []
        for sid in editable_slot_ids:
            inner.append(_css_rule(f'[data-slot="{sid}"]',
                                   {"grid-template-columns": f"repeat({bp['columns']},1fr)"}))
        for cid in sorted(resolved.keys()):
            c = resolved[cid][name]
            sel = f'[data-cmp="{_esc(cid)}"]'
            if c.get("hidden"):
                inner.append(_css_rule(sel, {"display": "none"}))
            else:
                inner.append(_css_rule(sel, {
                    "grid-column": f"{c['col_start']} / span {c['col_span']}",
                    "grid-row": str(c["row"]),
                    "display": "block",
                }))
        block = "".join(inner)
        lines.append(f"@media (min-width:{bp['min']}px){{{block}}}")
    return lines


# ── 공개 렌더 함수 ──────────────────────────────────────────────────────────────

def _document(title: str, head_comment: list, css_lines: list, body_lines: list) -> str:
    out = []
    out.extend(head_comment)
    out.append("<!DOCTYPE html>")
    out.append('<html lang="ko">')
    out.append("<head>")
    out.append('  <meta charset="utf-8" />')
    out.append('  <meta name="viewport" content="width=device-width, initial-scale=1" />')
    out.append(f"  <title>{_esc(title)}</title>")
    out.append("  <style>")
    for ln in css_lines:
        out.append(f"    {ln}")
    out.append("  </style>")
    out.append("</head>")
    out.append("<body>")
    out.extend(body_lines)
    out.append("</body>")
    out.append("</html>")
    return "\n".join(out) + "\n"


def _render_slots_body(scr: dict, canvas: dict, resolved: dict, dp_id: str) -> tuple:
    """body 라인 목록 + editable 슬롯 id 목록 반환."""
    components = canvas["components"]
    comps_by_slot = defaultdict(list)
    for c in components:
        comps_by_slot[c.get("slot")].append(c)
    for k in comps_by_slot:
        comps_by_slot[k].sort(key=lambda c: (c.get("order", 999), str(c.get("ref", ""))))

    items_by_slot = defaultdict(list)
    for it in scr.get("layout", []) or []:
        items_by_slot[(it.get("position", {}) or {}).get("slot")].append(it)

    screen = scr.get("screen", {})
    body = [f'  <div class="page" data-dp="{_esc(dp_id)}" data-scr="{_esc(screen.get("id",""))}">']
    editable_slot_ids = []

    for slot in canvas["slots"]:
        sid = slot["id"]
        tag = _slot_tag(sid)
        body.append(f'    <{tag} data-slot="{_esc(sid)}">')
        # header 슬롯엔 화면 제목 표시(맥락)
        if sid == "header" and screen.get("name"):
            body.append(f'      <h1>{_esc(screen["name"])}</h1>')

        items = items_by_slot.get(sid, [])
        if not slot.get("editable", True):
            # locked region → DP 실제 컴포넌트
            for c in comps_by_slot.get(sid, []):
                body.extend(_component_html(c.get("ref", ""), {}, None,
                                            c.get("note") or c.get("ref", ""), indent=3))
        else:
            editable_slot_ids.append(sid)
            if items:
                placed = sorted(items, key=_order_key)
                for it in placed:
                    body.extend(_component_html(item_ref(it), it.get("props") or {},
                                                it.get("id"), _label_of(it), indent=3))
            else:
                # 레거시/빈 캔버스: DP 컴포넌트가 있으면 맥락 표시
                for c in comps_by_slot.get(sid, []):
                    body.extend(_component_html(c.get("ref", ""), {}, None,
                                                c.get("note") or c.get("ref", ""), indent=3))
        body.append(f"    </{tag}>")
    body.append("  </div>")
    return body, editable_slot_ids


def render_screen(scr: dict, dp: dict, timestamp: str = "") -> tuple:
    """
    SCR doc + DP doc → (html, layout_hash, render_hash).
    timestamp 는 rendered-at 주석에만 들어가며 render_hash 에서 제외된다.
    """
    canvas = normalize_canvas(dp)
    resolved = resolve_positions(scr, dp)
    screen = scr.get("screen", {})
    scr_id = screen.get("id", "SCR-UNKNOWN")
    title = f'{screen.get("name", scr_id)} ({scr_id})'

    body, editable_slots = _render_slots_body(scr, canvas, resolved, dp.get("id", ""))
    css = _build_css(canvas, resolved, editable_slots)
    head_comment = [
        f"<!-- GENERATED VIEW — source: {scr_id}.yaml v{screen.get('version','?')} — DO NOT EDIT -->",
        "<!-- rendered-by: harness-core/render/engine.py -->",
    ]
    if timestamp:
        head_comment.append(f"<!-- rendered-at: {timestamp} -->")

    html = _document(title, head_comment, css, body)
    return html, compute_layout_hash(scr, dp), compute_render_hash(html)


def render_designpage(dp: dict, timestamp: str = "") -> str:
    """DP doc → HTML. locked=실제 컴포넌트, editable=그리드 오버레이+슬롯명+경계."""
    canvas = normalize_canvas(dp)
    dp_id = dp.get("id", "DP-UNKNOWN")
    comps_by_slot = defaultdict(list)
    for c in canvas["components"]:
        comps_by_slot[c.get("slot")].append(c)
    for k in comps_by_slot:
        comps_by_slot[k].sort(key=lambda c: (c.get("order", 999), str(c.get("ref", ""))))

    body = [f'  <div class="page dp-preview" data-dp="{_esc(dp_id)}">']
    editable_slots = []
    for slot in canvas["slots"]:
        sid = slot["id"]
        tag = _slot_tag(sid)
        locked = not slot.get("editable", True)
        cls = "slot-locked" if locked else "slot-editable"
        body.append(f'    <{tag} class="{cls}" data-slot="{_esc(sid)}">')
        body.append(f'      <span class="slot-label">{_esc(sid)} '
                    f'({"locked" if locked else "editable"})</span>')
        if locked:
            for c in comps_by_slot.get(sid, []):
                body.extend(_component_html(c.get("ref", ""), {}, None,
                                            c.get("note") or c.get("ref", ""), indent=3))
        else:
            editable_slots.append(sid)
            locks = ", ".join(slot.get("locks", [])) or "any (canvas)"
            body.append(f'      <div class="canvas-hint">빈 캔버스 — '
                        f'grid_columns={slot.get("grid_columns")} 허용: {_esc(locks)}</div>')
        body.append(f"    </{tag}>")
    body.append("  </div>")

    grid = canvas["grid"]
    gap = token_px(grid.get("gap", "space-4"))
    css = [
        "* { box-sizing: border-box; }",
        _css_rule("body", {"font-family": SYSTEM_FONT, "margin": "0"}),
        _css_rule(".page", {"margin": "0 auto", "max-width": f"{int(grid.get('max_width',1440))}px",
                            "padding": f"{gap}px"}),
        _css_rule(".slot-locked", {"background": "#f5f5f5", "border": "1px solid #ddd",
                                   "margin-bottom": f"{gap}px", "padding": f"{gap}px"}),
        _css_rule(".slot-editable", {"border": "1px dashed #888",
                                     "margin-bottom": f"{gap}px", "padding": f"{gap}px"}),
        _css_rule(".slot-label", {"color": "#666", "display": "block",
                                  "font-size": "12px", "margin-bottom": "4px"}),
        _css_rule(".canvas-hint", {"color": "#999", "font-size": "13px"}),
    ]
    head_comment = [
        f"<!-- GENERATED DP VIEW — source: {dp_id}.yaml — DO NOT EDIT -->",
        "<!-- rendered-by: harness-core/render/engine.py -->",
    ]
    if timestamp:
        head_comment.append(f"<!-- rendered-at: {timestamp} -->")
    return _document(f"{dp_id} (design page)", head_comment, css, body)


# ── DS 카탈로그 (D4) ────────────────────────────────────────────────────────────

def applicable_states(comp: dict) -> list:
    """allowlist의 states 선언 우선, 없으면 ref 기반 기본 추정(§9 결정 3)."""
    declared = comp.get("states") or []
    if declared:
        return [s for s in DEFAULT_STATES if s in declared] or declared
    return STATES_BY_REF.get(comp.get("name", ""), ["default"])


def _state_chip(ref: str, state: str, indent: int) -> list:
    """컴포넌트 1개를 특정 상태로 시각 렌더(카탈로그 갤러리 셀)."""
    pad = "  " * indent
    lines = [f'{pad}<div class="state-cell">']
    lines.append(f'{pad}  <span class="state-name">{_esc(state)}</span>')
    body = _component_html(ref, {}, None, ref, indent + 1)
    # 상태를 data-state 로 표기(시각 구분용; 실제 상호작용 아님)
    if body:
        first = body[0]
        if first.rstrip().endswith("/>"):
            body[0] = first[:-3] + f' data-state="{_esc(state)}" />'
        elif ">" in first:
            i = first.index(">")
            body[0] = first[:i] + f' data-state="{_esc(state)}"' + first[i:]
    lines.extend(body)
    lines.append(f"{pad}</div>")
    return lines


def render_catalog(tokens: dict, components: list, timestamp: str = "") -> str:
    """
    토큰 + ds-allowlist 컴포넌트 메타 → DS 카탈로그(대시보드) HTML.
    PO가 이름으로 디자인을 지시할 근거(P2 "백지 캔버스" 제거). 결정론적.
    """
    body = ['  <div class="catalog">']
    body.append("    <h1>DS 카탈로그</h1>")
    body.append('    <p class="lead">PO는 이 카탈로그의 <b>이름</b>으로 AI에게 디자인을 지시한다. '
                "각 이름은 screen model의 source.ref·토큰명과 동일.</p>")
    body.append('    <nav class="toc">'
                '<a href="#colors">색상</a> · <a href="#type">타이포</a> · '
                '<a href="#space">치수</a> · <a href="#components">컴포넌트</a> · '
                '<a href="#guide">사용 가이드</a></nav>')

    # 1) 색상 토큰
    body.append('    <section id="colors"><h2>색상 토큰</h2>')
    if tokens.get("colors"):
        body.append('      <div class="swatches">')
        for t in tokens["colors"]:
            body.append('        <div class="swatch">')
            body.append(f'          <div class="chip" data-token="{_esc(t["name"])}"></div>')
            body.append(f'          <code>--{_esc(t["name"])}</code><span>{_esc(t["value"])}</span>')
            body.append("        </div>")
        body.append("      </div>")
    else:
        body.append('      <p class="empty">색상 토큰을 찾지 못함 (DS에 CSS 변수 미정의).</p>')
    body.append("    </section>")

    # 2) 타이포
    body.append('    <section id="type"><h2>타이포 토큰</h2>')
    if tokens.get("fonts"):
        for t in tokens["fonts"]:
            body.append(f'      <div class="type-row"><code>--{_esc(t["name"])}</code>'
                        f'<span class="type-sample">{_esc(t["value"])}</span></div>')
    else:
        body.append('      <p class="empty">타이포 토큰 없음 — 시스템 폰트 스택 사용(렌더 동결).</p>')
    body.append("    </section>")

    # 3) 치수/스페이싱 (DS 토큰 + 엔진 기본 spacing)
    body.append('    <section id="space"><h2>치수·스페이싱 토큰</h2>')
    dims = list(tokens.get("dimensions") or [])
    body.append('      <table class="token-table"><thead><tr><th>토큰</th><th>값</th><th>견본</th></tr></thead><tbody>')
    for t in dims:
        body.append(f'        <tr><td><code>--{_esc(t["name"])}</code></td><td>{_esc(t["value"])}</td><td></td></tr>')
    body.append('      </tbody></table>')
    body.append('      <h3>엔진 기본 spacing (token-only 치수)</h3>')
    body.append('      <div class="space-scale">')
    for name in sorted(DEFAULT_TOKENS.keys()):
        px = DEFAULT_TOKENS[name]
        body.append(f'        <div class="space-row"><code>{_esc(name)}</code>'
                    f'<span class="space-bar" data-space="{px}"></span><span>{px}px</span></div>')
    body.append("      </div>")
    body.append("    </section>")

    # 4) 컴포넌트 갤러리 (variant + 표준 상태)
    body.append('    <section id="components"><h2>컴포넌트 갤러리</h2>')
    for comp in components:
        ref = comp.get("name", "")
        body.append('      <article class="comp-card">')
        body.append(f'        <h3>{_esc(ref)} <code class="ref">source.ref: {_esc(ref)}</code></h3>')
        if comp.get("description"):
            body.append(f'        <p class="desc">{_esc(comp["description"])}</p>')
        if comp.get("props"):
            body.append(f'        <p class="props">props: <code>{_esc(", ".join(comp["props"]))}</code></p>')
        body.append('        <div class="states">')
        for state in applicable_states(comp):
            body.extend(_state_chip(ref, state, indent=5))
        body.append("        </div>")
        body.append("      </article>")
    body.append("    </section>")

    # 5) 사용 가이드
    body.append('    <section id="guide"><h2>사용 가이드</h2><dl class="guide">')
    for comp in components:
        if comp.get("usage"):
            body.append(f'      <dt>{_esc(comp.get("name",""))}</dt><dd>{_esc(comp["usage"])}</dd>')
    body.append("    </dl></section>")

    if tokens.get("sources"):
        body.append('    <footer class="sources">토큰 출처: '
                    + _esc(", ".join(tokens["sources"])) + "</footer>")
    body.append("  </div>")

    # 색상 스와치/스페이싱 바를 토큰 변수로 칠하기 위한 CSS(인라인 style 금지 → 토큰 셀렉터)
    css = [
        "* { box-sizing: border-box; }",
        _css_rule("body", {"color": "#1a1a1a", "font-family": SYSTEM_FONT,
                           "margin": "0", "padding": "24px"}),
        _css_rule(".catalog", {"margin": "0 auto", "max-width": "1100px"}),
        _css_rule(".lead", {"color": "#555"}),
        _css_rule(".toc", {"border-bottom": "1px solid #eee", "margin-bottom": "24px",
                           "padding-bottom": "12px"}),
        _css_rule("section", {"margin-bottom": "40px"}),
        _css_rule("h2", {"border-bottom": "2px solid #111", "padding-bottom": "4px"}),
        _css_rule(".swatches", {"display": "grid", "gap": "12px",
                                "grid-template-columns": "repeat(auto-fill,minmax(180px,1fr))"}),
        _css_rule(".swatch", {"font-size": "13px"}),
        _css_rule(".chip", {"border": "1px solid #ddd", "border-radius": "6px",
                            "height": "48px", "margin-bottom": "4px", "width": "100%"}),
        _css_rule(".swatch code", {"display": "block", "font-weight": "600"}),
        _css_rule(".swatch span", {"color": "#777"}),
        _css_rule(".type-row", {"align-items": "center", "display": "flex", "gap": "16px",
                                "margin": "8px 0"}),
        _css_rule(".token-table", {"border-collapse": "collapse", "width": "100%"}),
        _css_rule(".token-table th, .token-table td",
                  {"border": "1px solid #eee", "padding": "6px 10px", "text-align": "left"}),
        _css_rule(".space-row", {"align-items": "center", "display": "flex", "gap": "12px",
                                 "margin": "6px 0"}),
        _css_rule(".space-bar", {"background": "#aa3bff", "display": "inline-block", "height": "12px"}),
        _css_rule(".comp-card", {"border": "1px solid #e5e5e5", "border-radius": "8px",
                                 "margin-bottom": "16px", "padding": "16px"}),
        _css_rule(".comp-card .ref", {"color": "#888", "font-size": "12px", "font-weight": "400"}),
        _css_rule(".desc", {"color": "#555", "margin": "4px 0"}),
        _css_rule(".props code", {"background": "#f4f3ec", "font-size": "12px", "padding": "2px 4px"}),
        _css_rule(".states", {"display": "flex", "flex-wrap": "wrap", "gap": "16px",
                              "margin-top": "12px"}),
        _css_rule(".state-cell", {"border": "1px dashed #ccc", "border-radius": "6px",
                                  "min-height": "64px", "min-width": "120px", "padding": "8px"}),
        _css_rule(".state-name", {"color": "#999", "display": "block", "font-size": "11px",
                                  "margin-bottom": "6px", "text-transform": "uppercase"}),
        _css_rule(".guide dt", {"font-weight": "600", "margin-top": "8px"}),
        _css_rule(".guide dd", {"color": "#555", "margin": "0 0 4px 0"}),
        _css_rule(".empty", {"color": "#999", "font-style": "italic"}),
        _css_rule(".sources", {"border-top": "1px solid #eee", "color": "#999",
                               "font-size": "12px", "margin-top": "32px", "padding-top": "12px"}),
        _css_rule('[data-state="disabled"]', {"cursor": "not-allowed", "opacity": "0.45"}),
        _css_rule('[data-state="error"]', {"border-color": "#d33", "color": "#d33"}),
        _css_rule('[data-state="focus"]', {"outline": "2px solid #aa3bff"}),
        _css_rule('[data-state="selected"]', {"background": "#aa3bff", "color": "#fff"}),
    ]
    # 색상 칩을 각 토큰 값으로 칠함(토큰 셀렉터; 인라인 style 아님)
    for t in (tokens.get("colors") or []):
        css.append(_css_rule(f'.chip[data-token="{_esc(t["name"])}"]', {"background": t["value"]}))
    # 스페이싱 바 너비를 px 값으로
    for px in sorted({DEFAULT_TOKENS[n] for n in DEFAULT_TOKENS}):
        css.append(_css_rule(f'.space-bar[data-space="{px}"]', {"width": f"{max(px,2)}px"}))

    head_comment = [
        "<!-- GENERATED DS CATALOG — source: ds-allowlist.md + design tokens — DO NOT EDIT -->",
        "<!-- rendered-by: harness-core/render/engine.py -->",
    ]
    if timestamp:
        head_comment.append(f"<!-- rendered-at: {timestamp} -->")
    return _document("DS 카탈로그", head_comment, css, body)
