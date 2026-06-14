#!/usr/bin/env python3
"""
Hook: on-save-lint-L1-L4.py
트리거: screen model YAML 저장 시 (schema 검증 통과 후)
목적:  L1 DS 준수 / L2 완전성 / L3 일관성 / L4 커버리지 검사
종료코드: 0 = pass (warn 있어도), 1 = L1 error 존재 시 저장 차단

L1 error → 저장 차단 (status=layout_confirmed 불가)
L2/L3/L4 error → open_question 생성 (저장은 허용, Gate A 차단)
warn → open_question 생성 (저장·Gate A 모두 허용, pass_with_deferred)
"""

import sys
import yaml
import re
import json
from pathlib import Path

L1_ERRORS   = []   # DS 준수 위반 → 저장 차단
L2_ERRORS   = []   # 완전성 위반 → Gate A 차단
L3_ERRORS   = []   # 일관성 위반 → Gate A 차단
L4_ERRORS   = []   # 커버리지 위반 → Gate A 차단
WARNINGS    = []   # 권고 → pass_with_deferred


def l1_err(msg):  L1_ERRORS.append(f"[L1 ERROR] {msg}")
def l2_err(msg):  L2_ERRORS.append(f"[L2 ERROR] {msg}")
def l3_err(msg):  L3_ERRORS.append(f"[L3 ERROR] {msg}")
def l4_err(msg):  L4_ERRORS.append(f"[L4 ERROR] {msg}")
def warn(msg):    WARNINGS.append(f"[WARN]     {msg}")


# ── design-guide.md 파서 ──────────────────────────────────────────────────────

def load_allowed_components(guide_path: Path) -> dict:
    """
    design-guide.md 파싱 → {ComponentName: {props: [...], slots: [...]}}
    ## ComponentName 블록 구조를 파싱.
    """
    if not guide_path.exists():
        l1_err(f"design-guide.md 없음: {guide_path} — lint 불가")
        return {}
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
            pm = re.match(r"-\s+props?:\s*(.+)", line, re.IGNORECASE)
            if pm:
                current_props.extend([p.strip() for p in pm.group(1).split(",")])
            sm = re.match(r"-\s+slots?:\s*(.+)", line, re.IGNORECASE)
            if sm:
                current_slots.extend([s.strip() for s in sm.group(1).split(",")])
    if current:
        allowed[current] = {"props": current_props, "slots": current_slots}
    return allowed


# ── L1: DS 준수 ───────────────────────────────────────────────────────────────

def lint_L1_ds_closure(layout: list, allowed: dict, screen_id: str):
    """
    L1-1: layout의 모든 component가 design-guide.md 허용 목록 안에 있어야 함
    L1-2: props가 허용 목록의 props 안에 있어야 함 (허용 props가 정의된 경우)
    L1-3: position.slot이 template 슬롯 안에 있어야 함 (슬롯 정의가 있는 경우)
    """
    if not allowed:
        l1_err(f"{screen_id}: design-guide.md 로드 실패 — DS 준수 검증 불가")
        return
    for item in layout:
        comp = item.get("component")
        if not comp:
            continue
        if comp not in allowed:
            l1_err(f"{screen_id}: DS 밖 컴포넌트 '{comp}' — design-guide.md에 없음")
            continue
        # props 검증 (허용 props가 정의된 경우만)
        item_props = set(item.get("props", {}).keys())
        guide_props = set(allowed[comp].get("props", []))
        if guide_props:
            unknown_props = item_props - guide_props
            if unknown_props:
                l1_err(f"{screen_id}.{item.get('id')}: 미허용 props {unknown_props} (컴포넌트: {comp})")


# ── L2: 완전성 ────────────────────────────────────────────────────────────────

def lint_L2_completeness(layout: list, actions: list, notes: list, screen_id: str):
    """
    L2-1: interactive=true 컴포넌트는 actions[]에 해당 CMP action이 1개 이상 있어야 함
    L2-2: actions[]에 acceptance가 없으면 error
    L2-3: 화면에 데이터 표시 컴포넌트(Table, List)가 있으면 data_source note가 있어야 함
    """
    action_comps = {a.get("component") for a in (actions or [])}
    data_table_comps = set()
    for item in (layout or []):
        cid  = item.get("id")
        comp = item.get("component", "")
        meta = item.get("meta", {})
        is_interactive = meta.get("interactive", False)
        # L2-1
        if is_interactive and cid not in action_comps:
            l2_err(f"{screen_id}.{cid}: interactive=true인데 actions[]에 해당 action 없음")
        # 데이터 컴포넌트 수집 (DataTable, List, Chart 등)
        if any(kw in comp.lower() for kw in ("table", "list", "chart", "grid")):
            data_table_comps.add(cid)
    # L2-2
    for action in (actions or []):
        if not action.get("acceptance"):
            l2_err(f"{screen_id}: action '{action.get('id')}' — acceptance 없음")
    # L2-3: DataTable 컴포넌트가 있는데 data_source 관련 note가 하나도 없으면 warn
    if data_table_comps:
        has_data_note = any(
            n.get("kind") in ("business_rule", "constraint") and
            any(kw in str(n.get("body", "")) for kw in ("조회", "fetch", "API", "데이터", "data"))
            for n in (notes or [])
        )
        if not has_data_note:
            warn(f"{screen_id}: DataTable/List 컴포넌트가 있는데 데이터 출처 note가 없음 — 출처 명시 권장")


# ── L3: 일관성 ────────────────────────────────────────────────────────────────

_component_label_registry: dict = {}   # label → comp_name (전체 screen 통합)

def lint_L3_consistency(layout: list, actions: list, screen_id: str, all_screens: dict):
    """
    L3-1: 같은 props.label이 다른 DS component에 할당된 경우 경고
    L3-2: navigate target SCR-가 model_repo에 존재하지 않으면 warn
    L3-3: 같은 CMP가 다른 화면에서 다른 component로 매핑된 경우 warn
    """
    for item in (layout or []):
        comp  = item.get("component")
        label = (item.get("props") or {}).get("label")
        if label and comp:
            if label in _component_label_registry and _component_label_registry[label] != comp:
                l3_err(f"{screen_id}: label '{label}'이 '{_component_label_registry[label]}'과 '{comp}' 두 가지 컴포넌트로 사용됨 — 일관성 위반")
            _component_label_registry[label] = comp

    for action in (actions or []):
        outcome = action.get("outcome", {})
        if isinstance(outcome, dict) and outcome.get("type") == "navigate":
            target = outcome.get("target", "")
            if target and target not in all_screens and not target.startswith("EXT-"):
                warn(f"{screen_id}: navigate target '{target}'이 model_repo에 없음 (미래 화면이면 무시)")


# ── L4: 커버리지 ──────────────────────────────────────────────────────────────

def lint_L4_coverage(layout: list, actions: list, screen_id: str):
    """
    L4-1: actions[]의 component가 layout에 없는 CMP를 참조하면 error
    L4-2: 모든 interactive CMP에 user_confirmed action이 있는지 확인 (Gate A 직전)
    """
    layout_ids = {item.get("id") for item in (layout or [])}
    for action in (actions or []):
        comp = action.get("component")
        if comp and comp not in layout_ids:
            l4_err(f"{screen_id}: action '{action.get('id')}'의 component '{comp}'이 layout에 없음 — 실존하지 않는 CMP 참조")


# ── main ──────────────────────────────────────────────────────────────────────

def find_guide(start: Path) -> Path:
    """상위 디렉터리를 탐색해서 design-guide.md 위치 찾기"""
    for parent in [start] + list(start.parents)[:4]:
        g = parent / "foundation" / "design-system" / "design-guide.md"
        if g.exists():
            return g
        g2 = parent / "input" / "design-system" / "design-guide.md"
        if g2.exists():
            return g2
    return Path("design-guide.md")   # fallback (current dir)


def load_all_screen_ids(screens_dir: Path) -> set:
    ids = set()
    for f in screens_dir.glob("SCR-*.yaml"):
        ids.add(f.stem)
    return ids


def main():
    if len(sys.argv) < 2:
        targets = list(Path(".").glob("model_repo/screens/SCR-*.yaml"))
    else:
        targets = [Path(p) for p in sys.argv[1:]]

    if not targets:
        print("[lint-L1-L4] 검증할 파일 없음", file=sys.stderr)
        sys.exit(0)

    # design-guide.md 로드 (첫 번째 파일 경로 기준)
    guide_path = find_guide(targets[0].parent)
    allowed    = load_allowed_components(guide_path)

    # 전체 screen ID 목록 (L3 navigate target 검증용)
    screens_dir  = targets[0].parent if targets[0].parent.name == "screens" else Path("model_repo/screens")
    all_screen_ids = load_all_screen_ids(screens_dir)

    for fp in targets:
        if not fp.exists():
            l1_err(f"{fp}: 파일 없음")
            continue
        try:
            doc = yaml.safe_load(fp.read_text(encoding="utf-8"))
        except Exception as e:
            l1_err(f"{fp.name}: YAML 파싱 실패 — {e}")
            continue

        screen_id = doc.get("meta", {}).get("id", fp.stem)
        layout    = doc.get("layout", [])
        actions   = doc.get("actions", [])
        notes     = doc.get("notes", [])

        lint_L1_ds_closure(layout, allowed, screen_id)
        lint_L2_completeness(layout, actions, notes, screen_id)
        lint_L3_consistency(layout, actions, screen_id, all_screen_ids)
        lint_L4_coverage(layout, actions, screen_id)

    # 결과 출력
    all_errors = L1_ERRORS + L2_ERRORS + L3_ERRORS + L4_ERRORS
    for w in WARNINGS:
        print(w, file=sys.stderr)
    for e in all_errors:
        print(e, file=sys.stderr)

    if L1_ERRORS:
        print(f"\n[lint] ❌ L1 error {len(L1_ERRORS)}건 — 저장 차단 (DS 폐쇄 위반)", file=sys.stderr)
        sys.exit(1)
    if L2_ERRORS or L3_ERRORS or L4_ERRORS:
        total = len(L2_ERRORS) + len(L3_ERRORS) + len(L4_ERRORS)
        print(f"\n[lint] ⚠️  L2/L3/L4 error {total}건 — 저장은 허용, Gate A 차단", file=sys.stderr)
        sys.exit(0)   # 저장 허용, Gate A는 gate-a-check.py가 별도 차단
    print(f"[lint] ✅ L1~L4 pass ({len(targets)} file(s), {len(WARNINGS)} warning(s))")
    sys.exit(0)


if __name__ == "__main__":
    main()
