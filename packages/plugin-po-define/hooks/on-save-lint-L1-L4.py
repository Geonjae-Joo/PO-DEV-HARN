#!/usr/bin/env python3
"""
Hook: on-save-lint-L1-L4.py
트리거: screen model YAML 저장 시 (schema 검증 통과 후)
목적:  L1 DS 준수 / L2 완전성 / L3 일관성 / L4 커버리지 / L5 캔버스 경계 검사 (L1~L5)
종료코드: 0 = pass (warn 있어도), 1 = L1 error 존재 시 저장 차단

스키마 v2 기준: layout item은 `source: {kind, ref}` 를 쓴다 (구 `component:` 아님).

L1 error → 저장 차단 (status=layout_confirmed 불가)
L2/L3/L4/L5 error → open_question 생성 (저장은 허용, Gate A 차단)
warn → open_question 생성 (저장·Gate A 모두 허용, pass_with_deferred)

ADR-002 L5 canvas-bounds (D3, 결정 6) — OPTIONAL, 하위호환:
  - position.base 가 있는 item만 검사 (순수 레거시 {slot, order} 는 건너뜀).
  - 가로: col_start + col_span - 1 <= 슬롯/캔버스 grid_columns (초과 → L5 error).
  - editable:false (locked) 슬롯에 컴포넌트 추가 → L5 error.
  - 세로(row)는 봉쇄하지 않음(내부 스크롤 허용).
  - DP 캔버스 정보를 읽을 수 없으면 L5 조용히 건너뜀(거짓 에러 방지).
"""

from __future__ import annotations

import sys
import json
import yaml
import re
from pathlib import Path

# Windows 콘솔(cp949 등) 유니코드 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# ── 공용 DS 폐쇄 라이브러리 (harness-core/lib) 단일 출처 ─────────────────────────
# 시스템 모노레포에서는 packages/harness-core/lib 에 위치.
# 런타임 레이아웃이 달라 import 실패 시 동치 로컬 구현으로 폴백한다.
_CORE_LIB = Path(__file__).resolve().parents[2] / "harness-core" / "lib"
if _CORE_LIB.exists() and str(_CORE_LIB) not in sys.path:
    sys.path.insert(0, str(_CORE_LIB))
try:
    from ds_closure import load_allowed_components as _core_load_allowed  # type: ignore
except Exception:
    _core_load_allowed = None

L1_ERRORS   = []   # DS 준수 위반 → 저장 차단
L2_ERRORS   = []   # 완전성 위반 → Gate A 차단
L3_ERRORS   = []   # 일관성 위반 → Gate A 차단
L4_ERRORS   = []   # 커버리지 위반 → Gate A 차단
L5_ERRORS   = []   # 캔버스 경계 위반 → Gate A 차단
WARNINGS    = []   # 권고 → pass_with_deferred


def l1_err(msg):  L1_ERRORS.append(f"[L1 ERROR] {msg}")
def l2_err(msg):  L2_ERRORS.append(f"[L2 ERROR] {msg}")
def l3_err(msg):  L3_ERRORS.append(f"[L3 ERROR] {msg}")
def l4_err(msg):  L4_ERRORS.append(f"[L4 ERROR] {msg}")
def l5_err(msg):  L5_ERRORS.append(f"[L5 ERROR] {msg}")
def warn(msg):    WARNINGS.append(f"[WARN]     {msg}")

# ── col_span shorthand → 정수 resolve (ADR-002 §1) ────────────────────────────
DEFAULT_GRID_COLUMNS = 12

def resolve_col_span(span, grid_columns: int):
    """col_span(정수 또는 shorthand)을 grid_columns에 맞춰 정수로 resolve.
    해석 불가하면 None 반환(검사 건너뜀)."""
    if isinstance(span, bool):
        return None
    if isinstance(span, int):
        return span
    if isinstance(span, str):
        s = span.strip().lower()
        if s == "full":
            return grid_columns
        if s == "half":
            return round(grid_columns / 2)
        if s == "third":
            return round(grid_columns / 3)
        if s == "quarter":
            return round(grid_columns / 4)
    return None


# ── layout item 헬퍼 (스키마 v2: source.kind / source.ref) ─────────────────────

def item_ref(item: dict) -> str:
    """layout item의 DS 컴포넌트 ref 반환 (source.ref)."""
    return (item.get("source") or {}).get("ref", "") or ""

def item_kind(item: dict) -> str:
    return (item.get("source") or {}).get("kind", "ds") or "ds"


# ── ds-allowlist.md 파서 ──────────────────────────────────────────────────────

def load_allowed_components(guide_path: Path) -> dict:
    """
    ds-allowlist.md 파싱 → {ComponentName: {props: [...], slots: [...]}}
    공용 harness-core/lib/ds_closure.py 를 단일 출처로 사용.
    import 실패 시 아래 동치 로컬 구현으로 폴백한다.
    """
    if not guide_path.exists():
        l1_err(f"ds-allowlist.md 없음: {guide_path} — lint 불가")
        return {}
    if _core_load_allowed is not None:
        return _core_load_allowed(guide_path)
    # ── 폴백 (core lib 미탑재 런타임) — ds_closure.load_allowed_components 와 동일 로직 ──
    text = guide_path.read_text(encoding="utf-8")
    allowed = {}
    current = None
    current_props = []
    current_slots = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\w+)", line)
        if m:
            if current:
                allowed[current] = {"props": current_props, "slots": current_slots}
            current = m.group(1)
            current_props = []
            current_slots = []
            continue
        if current:
            pm = re.match(r"-\s+\*?\*?props?\*?\*?:\s*(.+)", line, re.IGNORECASE)
            if pm:
                for p in pm.group(1).split(","):
                    name = p.split(":")[0].strip()
                    if name:
                        current_props.append(name)
            sm = re.match(r"-\s+\*?\*?slots?\*?\*?:\s*(.+)", line, re.IGNORECASE)
            if sm:
                current_slots.extend([s.strip() for s in sm.group(1).split(",")])
    if current:
        allowed[current] = {"props": current_props, "slots": current_slots}
    return allowed


# ── design page 슬롯 로더 (page-region 검증용) ────────────────────────────────

def load_design_page_slots(start: Path) -> set:
    """foundation/design-pages/DP-*.yaml 에서 슬롯명 집합을 수집."""
    slots = set()
    for parent in [start] + list(start.parents)[:5]:
        dp_dir = parent / "foundation" / "design-pages"
        if dp_dir.exists():
            for f in dp_dir.glob("DP-*.yaml"):
                try:
                    doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                except Exception:
                    continue
                for s in (doc.get("slots") or []):
                    if isinstance(s, dict):
                        slots.add(s.get("name") or s.get("id"))
                    else:
                        slots.add(s)
            break
    return {s for s in slots if s}


# ── DP 캔버스 로더 (L5 canvas-bounds용, ADR-002 §2) ────────────────────────────

def load_design_page_canvas(start: Path) -> dict:
    """foundation/design-pages/DP-*.yaml 를 읽어 DP-id별 캔버스 정보를 반환.

    반환: { "DP-MAIN": {
              "canvas_columns": 12,
              "slots": { "content": {"editable": True,  "grid_columns": 12, "locks": []},
                         "header":  {"editable": False, "grid_columns": 12, "locks": [...]}, ... }
           }, ... }

    하위호환: 평면 slots(문자열 목록)은 전부 editable:true, grid_columns = 기본 12 로 간주.
    """
    out = {}
    for parent in [start] + list(start.parents)[:5]:
        dp_dir = parent / "foundation" / "design-pages"
        if not dp_dir.exists():
            continue
        for f in dp_dir.glob("DP-*.yaml"):
            try:
                doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            dp_id = doc.get("id") or f.stem
            canvas = doc.get("canvas") or {}
            grid = canvas.get("grid") or {}
            canvas_columns = grid.get("columns", DEFAULT_GRID_COLUMNS)
            if not isinstance(canvas_columns, int) or isinstance(canvas_columns, bool):
                canvas_columns = DEFAULT_GRID_COLUMNS
            slot_map = {}
            for s in (doc.get("slots") or []):
                if isinstance(s, dict):
                    sid = s.get("id") or s.get("name")
                    if not sid:
                        continue
                    editable = s.get("editable", True)
                    gc = s.get("grid_columns", canvas_columns)
                    if not isinstance(gc, int) or isinstance(gc, bool):
                        gc = canvas_columns
                    slot_map[sid] = {
                        "editable": bool(editable),
                        "grid_columns": gc,
                        "locks": s.get("locks") or [],
                    }
                else:
                    # 레거시 평면 슬롯: 전부 editable, 캔버스 컬럼 사용
                    slot_map[s] = {
                        "editable": True,
                        "grid_columns": canvas_columns,
                        "locks": [],
                    }
            out[dp_id] = {"canvas_columns": canvas_columns, "slots": slot_map}
        break
    return out


# ── L1: DS 준수 ───────────────────────────────────────────────────────────────

def lint_L1_ds_closure(layout: list, allowed: dict, dp_slots: set, screen_id: str):
    """
    L1-1: source.kind=='ds' 인 모든 component(ref)가 ds-allowlist.md 허용 목록 안에 있어야 함
    L1-2: props가 허용 목록의 props 안에 있어야 함 (허용 props가 정의된 경우)
    L1-3: source.kind=='page-region' 인 경우 ref가 design-page 슬롯 안에 있어야 함
    """
    if not allowed:
        l1_err(f"{screen_id}: ds-allowlist.md 로드 실패 — DS 준수 검증 불가")
        return
    for item in layout:
        cid  = item.get("id")
        ref  = item_ref(item)
        kind = item_kind(item)
        if not ref:
            l1_err(f"{screen_id}.{cid}: source.ref 없음 — DS 매핑 불가")
            continue
        if kind == "page-region":
            # design page 슬롯명 검증 (슬롯 목록을 로드한 경우만)
            if dp_slots and ref not in dp_slots:
                l1_err(f"{screen_id}.{cid}: page-region '{ref}'이 design-page 슬롯 목록에 없음")
            continue
        # kind == 'ds'
        if ref not in allowed:
            l1_err(f"{screen_id}.{cid}: DS 밖 컴포넌트 '{ref}' — ds-allowlist.md에 없음")
            continue
        # props 검증 (허용 props가 정의된 경우만)
        item_props = set((item.get("props") or {}).keys())
        guide_props = set(allowed[ref].get("props", []))
        if guide_props:
            unknown_props = item_props - guide_props
            if unknown_props:
                l1_err(f"{screen_id}.{cid}: 미허용 props {unknown_props} (컴포넌트: {ref})")


# ── L2: 완전성 ────────────────────────────────────────────────────────────────

def lint_L2_completeness(layout: list, actions: list, notes: list, screen_id: str):
    """
    L2-1: interactive=true 컴포넌트는 actions[]에 해당 CMP action이 1개 이상 있어야 함 (error)
    L2-2: actions[]에 acceptance가 없으면 error
    L2-3: 데이터 표시 컴포넌트(Table/List)가 있는데 데이터 출처 note가 없으면 warn
          (data_source의 강한 강제는 sufficiency-check.py가 담당)
    """
    action_comps = {a.get("component") for a in (actions or [])}
    data_table_comps = set()
    for item in (layout or []):
        cid  = item.get("id")
        ref  = item_ref(item).lower()
        meta = item.get("meta", {})
        is_interactive = meta.get("interactive", False)
        # L2-1
        if is_interactive and cid not in action_comps:
            l2_err(f"{screen_id}.{cid}: interactive=true인데 actions[]에 해당 action 없음")
        # 데이터 컴포넌트 수집 (DataTable, List, Chart 등)
        if any(kw in ref for kw in ("table", "list", "chart", "grid")):
            data_table_comps.add(cid)
    # L2-2
    for action in (actions or []):
        if not action.get("acceptance"):
            l2_err(f"{screen_id}: action '{action.get('id')}' — acceptance 없음")
    # L2-3 (warn)
    if data_table_comps:
        has_data_note = any(
            n.get("kind") in ("business_rule", "constraint") and
            any(kw in str(n.get("body", "")) for kw in ("조회", "fetch", "API", "데이터", "data"))
            for n in (notes or [])
        )
        if not has_data_note:
            warn(f"{screen_id}: DataTable/List 컴포넌트가 있는데 데이터 출처 note가 없음 — 출처 명시 권장")


# ── L3: 일관성 ────────────────────────────────────────────────────────────────

_component_label_registry: dict = {}   # label → ref (전체 screen 통합)

def register_labels(layout: list, screen_id: str, emit_error: bool):
    """라벨↔컴포넌트 매핑 등록. emit_error=True면 충돌 시 L3 error."""
    for item in (layout or []):
        ref   = item_ref(item)
        label = (item.get("props") or {}).get("label")
        if label and ref:
            existing = _component_label_registry.get(label)
            if existing and existing != ref and emit_error:
                l3_err(f"{screen_id}: label '{label}'이 '{existing}'과 '{ref}' 두 가지 컴포넌트로 사용됨 — 일관성 위반")
            _component_label_registry.setdefault(label, ref)


def lint_L3_consistency(layout: list, actions: list, screen_id: str, all_screens: set):
    """
    L3-1: 같은 props.label이 다른 DS component에 할당된 경우 error (전체 화면 대상)
    L3-2: navigate target SCR-가 model_repo에 존재하지 않으면 warn
    """
    register_labels(layout, screen_id, emit_error=True)
    for action in (actions or []):
        outcome = action.get("outcome", {})
        if isinstance(outcome, dict) and outcome.get("type") == "navigate":
            target = outcome.get("target", "")
            if target and target not in all_screens and not target.startswith("EXT-"):
                warn(f"{screen_id}: navigate target '{target}'이 model_repo에 없음 (미래 화면이면 무시)")


# ── L4: 커버리지 ──────────────────────────────────────────────────────────────

def lint_L4_coverage(layout: list, actions: list, screen_id: str, status: str = "draft"):
    """
    L4-1: actions[]의 component가 layout에 없는 CMP를 참조하면 error (항상)
    L4-2: 모든 interactive CMP에 user_confirmed action이 있어야 함 (Gate A 직전 커버리지)
          — 작성 중(draft/layout_confirmed/actions_in_progress)에는 정상적으로 미완이므로
            error 가 아니라 warning 으로 보고하고, review/confirmed 단계에서만 error 로 강제한다.
            (이전에는 draft 에서도 error 가 떠 Gate A 사전 점검을 오염시켰다.)
    """
    layout_ids = {item.get("id") for item in (layout or [])}
    # L4-1
    for action in (actions or []):
        comp = action.get("component")
        if comp and comp not in layout_ids:
            l4_err(f"{screen_id}: action '{action.get('id')}'의 component '{comp}'이 layout에 없음 — 실존하지 않는 CMP 참조")
    # L4-2
    enforce = status in ("review", "confirmed")
    confirmed_comps = {
        a.get("component") for a in (actions or [])
        if a.get("status") == "user_confirmed"
    }
    for item in (layout or []):
        if (item.get("meta") or {}).get("interactive"):
            cid = item.get("id")
            if cid not in confirmed_comps:
                if enforce:
                    l4_err(f"{screen_id}.{cid}: interactive=true인데 user_confirmed action 없음 — 커버리지 미달")
                else:
                    warn(f"{screen_id}.{cid}: interactive=true인데 아직 user_confirmed action 없음 "
                         f"(status={status}) — Gate A 전 채워야 함")


# ── L5: 캔버스 경계 (ADR-002 D3, 결정 6) ──────────────────────────────────────

def _check_horizontal_bound(gp: dict, slot_columns: int, screen_id: str, cid: str, where: str):
    """단일 좌표 dict(base 또는 at.<bp>)의 가로 경계를 검사한다."""
    if not isinstance(gp, dict):
        return
    col_start = gp.get("col_start")
    span_raw = gp.get("col_span")
    if not isinstance(col_start, int) or isinstance(col_start, bool):
        return  # schema-validate가 별도로 잡음; L5는 경계만
    if span_raw is None:
        return
    span = resolve_col_span(span_raw, slot_columns)
    if span is None:
        return  # 해석 불가(픽셀 등)는 schema-validate 담당
    if col_start + span - 1 > slot_columns:
        l5_err(f"{screen_id}.{cid}: 가로 캔버스 초과 ({where}: col_start={col_start} + "
               f"col_span={span} - 1 > grid_columns={slot_columns})")


def lint_L5_canvas_bounds(layout: list, screen_id: str, dp_info: dict):
    """
    L5-1: position.base가 있는 item만 검사 (순수 레거시는 하위호환으로 건너뜀).
    L5-2: 가로 경계 — base 및 각 at.<bp>에서 col_start+col_span-1 <= grid_columns.
          editable 슬롯이면 slot.grid_columns, 아니면 canvas columns 기준.
    L5-3: editable:false (locked) 슬롯에 컴포넌트 추가 → error.
          (레거시 평면 DP는 locked 슬롯이 없으므로 에러 없음.)
    DP 캔버스 정보를 못 읽으면 조용히 건너뜀.
    """
    if not dp_info:
        return
    slots = dp_info.get("slots") or {}
    canvas_columns = dp_info.get("canvas_columns", DEFAULT_GRID_COLUMNS)
    for item in (layout or []):
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        if not isinstance(pos, dict) or "base" not in pos:
            continue  # 순수 레거시 — 건너뜀
        cid = item.get("id")
        slot_id = pos.get("slot")
        slot_def = slots.get(slot_id) if slot_id is not None else None
        # L5-3: locked 슬롯 추가 금지
        if slot_def is not None and slot_def.get("editable") is False:
            l5_err(f"{screen_id}.{cid}: locked 슬롯 '{slot_id}'에 컴포넌트 추가 불가 (editable:false)")
            continue
        # 슬롯 컬럼 수: editable 슬롯이면 자체 grid_columns, 아니면 canvas columns
        if slot_def is not None:
            slot_columns = slot_def.get("grid_columns", canvas_columns)
        else:
            slot_columns = canvas_columns
        # L5-2: base
        _check_horizontal_bound(pos.get("base"), slot_columns, screen_id, cid, "base")
        # L5-2: at.<bp>
        at = pos.get("at")
        if isinstance(at, dict):
            for bp, gp in at.items():
                _check_horizontal_bound(gp, slot_columns, screen_id, cid, f"at.{bp}")


# ── main ──────────────────────────────────────────────────────────────────────

def find_guide(start: Path) -> Path:
    """상위 디렉터리를 탐색해서 ds-allowlist.md 위치 찾기"""
    for parent in [start] + list(start.parents)[:5]:
        g = parent / "foundation" / "design-system" / "ds-allowlist.md"
        if g.exists():
            return g
        g2 = parent / "input" / "design-system" / "ds-allowlist.md"
        if g2.exists():
            return g2
    return Path("ds-allowlist.md")   # fallback (current dir)


def load_all_screen_ids(screens_dir: Path) -> set:
    ids = set()
    for f in screens_dir.glob("SCR-*.yaml"):
        ids.add(f.stem)
    return ids


def preload_label_registry(screens_dir: Path, target_paths: set):
    """L3-1 cross-screen 검증을 위해 대상 외 화면들의 라벨을 먼저 등록(충돌은 대상 처리 시 보고)."""
    for f in screens_dir.glob("SCR-*.yaml"):
        if str(f) in target_paths:
            continue
        try:
            doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        register_labels(doc.get("layout", []), doc.get("screen", {}).get("id", f.stem), emit_error=False)


def _is_scr_target(p: Path) -> bool:
    """SCR-*.yaml 만 lint 대상 (무관 파일 편집은 통과)."""
    return p.suffix == ".yaml" and p.stem.startswith("SCR-")


def resolve_targets() -> list[Path] | None:
    """lint 대상 결정 (dp-render.py·schema-validate와 동일 규약).
    [] = 훅인데 SCR 아님(스킵), None = 수동 CLI(glob 폴백), 리스트 = 대상 SCR.
    """
    # 1) 훅 stdin payload
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
        except Exception:
            raw = ""
        if raw.strip():
            try:
                payload = json.loads(raw)
                fp = (payload.get("tool_input") or {}).get("file_path")
            except Exception:
                fp = None
            if fp:
                p = Path(fp)
                return [p] if _is_scr_target(p) else []
    # 2) argv 폴백
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        return [Path(a) for a in args if _is_scr_target(Path(a))]
    # 3) 수동 CLI 모드 — glob
    return None


def main():
    targets = resolve_targets()
    if targets == []:
        sys.exit(0)   # 훅 컨텍스트지만 SCR 파일 아님 — 통과
    if targets is None:
        targets = list(Path(".").glob("model_repo/screens/SCR-*.yaml"))

    if not targets:
        print("[lint-L1-L4] 검증할 파일 없음", file=sys.stderr)
        sys.exit(0)

    # ds-allowlist.md + design page 슬롯 로드 (첫 번째 파일 경로 기준)
    guide_path = find_guide(targets[0].parent)
    allowed    = load_allowed_components(guide_path)
    dp_slots   = load_design_page_slots(targets[0].parent)
    dp_canvas  = load_design_page_canvas(targets[0].parent)   # L5용 DP-id별 캔버스 정보

    # 전체 screen ID 목록 (L3 navigate target 검증용)
    screens_dir  = targets[0].parent if targets[0].parent.name == "screens" else Path("model_repo/screens")
    all_screen_ids = load_all_screen_ids(screens_dir)

    # L3-1: 대상 외 화면 라벨을 먼저 등록해 cross-screen 충돌을 탐지
    preload_label_registry(screens_dir, {str(t) for t in targets})

    for fp in targets:
        if not fp.exists():
            l1_err(f"{fp}: 파일 없음")
            continue
        try:
            doc = yaml.safe_load(fp.read_text(encoding="utf-8"))
        except Exception as e:
            l1_err(f"{fp.name}: YAML 파싱 실패 — {e}")
            continue

        screen_id = doc.get("screen", {}).get("id", fp.stem)
        status    = doc.get("screen", {}).get("status", "draft")
        layout    = doc.get("layout", [])
        actions   = doc.get("actions", [])
        notes     = doc.get("notes", [])

        # L5: screen.template.page → DP 캔버스 매핑
        tmpl_page = (doc.get("screen", {}).get("template") or {}).get("page")
        dp_info = dp_canvas.get(tmpl_page) if tmpl_page else None

        lint_L1_ds_closure(layout, allowed, dp_slots, screen_id)
        lint_L2_completeness(layout, actions, notes, screen_id)
        lint_L3_consistency(layout, actions, screen_id, all_screen_ids)
        lint_L4_coverage(layout, actions, screen_id, status)
        lint_L5_canvas_bounds(layout, screen_id, dp_info)

    # 결과 출력
    all_errors = L1_ERRORS + L2_ERRORS + L3_ERRORS + L4_ERRORS + L5_ERRORS
    for w in WARNINGS:
        print(w, file=sys.stderr)
    for e in all_errors:
        print(e, file=sys.stderr)

    if L1_ERRORS:
        print(f"\n[lint] ❌ L1 error {len(L1_ERRORS)}건 — 저장 차단 (DS 폐쇄 위반)", file=sys.stderr)
        sys.exit(1)
    if L2_ERRORS or L3_ERRORS or L4_ERRORS or L5_ERRORS:
        total = len(L2_ERRORS) + len(L3_ERRORS) + len(L4_ERRORS) + len(L5_ERRORS)
        print(f"\n[lint] ⚠️  L2/L3/L4/L5 error {total}건 — 저장은 허용, Gate A 차단", file=sys.stderr)
        sys.exit(0)   # 저장 허용, Gate A는 gate-a-check.py가 별도 차단
    print(f"[lint] ✅ L1~L5 pass ({len(targets)} file(s), {len(WARNINGS)} warning(s))")
    sys.exit(0)


if __name__ == "__main__":
    main()
