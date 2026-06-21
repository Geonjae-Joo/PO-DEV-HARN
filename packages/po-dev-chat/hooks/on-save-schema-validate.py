#!/usr/bin/env python3
"""
Hook: on-save-schema-validate.py
트리거: screen model YAML 저장 시 (Claude Code pre-tool-use hook)
목적:  screen-model-schema-v2의 필수 필드·enum 유효성 검증
종료코드: 0 = pass, 1 = fail (stderr에 에러 목록)

스키마 v2 기준:
  - 최상위 키는 `screen:` (구 스키마의 `meta:`가 아님)
  - layout item은 `source: {kind, ref, version}` (구 스키마의 `component:`가 아님)
  - action.status enum: proposed | user_confirmed
  - 최상위 `schema_version: 2`

ADR-002 확장 (모두 OPTIONAL, 있을 때만 검증 — 하위호환 유지):
  - position v2: `position.base: {col_start, col_span, row, row_span}` + `position.at.<bp>`
    col_span은 정수 또는 shorthand(full/half/third/quarter). 픽셀 좌표·auto 흐름값 금지.
    레거시 `position: {slot, order}` (base 없음)은 그대로 유효.
  - `screen.from_template: {page: DP-*, version: int}` 인스턴스화 출처 핀 (권장).
"""

import sys
import yaml
import re
from pathlib import Path

# Windows 콘솔(cp949 등) 유니코드 출력 크래시 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

ERRORS = []
WARNINGS = []

# ── 허용 enum 값 ──────────────────────────────────────────────────────────────
STATUS_VALUES   = {"draft", "layout_confirmed", "actions_in_progress", "review", "confirmed"}
OUTCOME_TYPES   = {"navigate", "query", "mutate", "export", "open", "validate", "noop"}
NOTE_KINDS      = {"business_rule", "nfr", "ux", "constraint", "assumption", "open_question"}
COMPLEXITY      = {"low", "med", "high"}
PERMISSIONS     = {"all", "login", "admin", "manager", "viewer"}   # 프로젝트별 확장 가능
ACTION_STATUS   = {"proposed", "user_confirmed"}
SOURCE_KINDS    = {"ds", "page-region"}

# ── 위치 스키마 v2 (ADR-002 §1) ───────────────────────────────────────────────
COLSPAN_SHORTHAND = {"full", "half", "third", "quarter"}
BREAKPOINT_NAMES  = {"lg", "md", "sm"}

# ── spine ID 패턴 ─────────────────────────────────────────────────────────────
SCR_RE  = re.compile(r"^SCR-[A-Z][A-Z0-9-]+$")
CMP_RE  = re.compile(r"^CMP-[A-Z][A-Z0-9-]+\.[a-zA-Z][a-zA-Z0-9_]+$")
REQ_RE  = re.compile(r"^REQ-[A-Z][A-Z0-9-]+\.\d{3}$")
NOTE_RE = re.compile(r"^NOTE-[A-Z][A-Z0-9-]+\.\d{3}$")
NFR_RE  = re.compile(r"^NFR-[A-Z][A-Z0-9-]+\.\d{3}$")
PRM_RE  = re.compile(r"^PRM-\d{3,}$")
DP_RE   = re.compile(r"^DP-[A-Z][A-Z0-9-]+$")
Q_RE    = re.compile(r"^Q-\d{3,}$")


def err(msg: str):
    ERRORS.append(f"[ERROR] {msg}")

def warn(msg: str):
    WARNINGS.append(f"[WARN]  {msg}")


def validate_schema_version(doc: dict, path: str):
    sv = doc.get("schema_version")
    if sv is None:
        warn(f"{path}: schema_version 없음 (schema_version: 2 권장)")
    elif sv != 2:
        err(f"{path}: schema_version={sv} — 이 검증기는 v2 전용")


def validate_screen(screen: dict, path: str):
    """구 스키마의 meta 섹션을 대체하는 screen 섹션 검증."""
    if not screen:
        err(f"{path}: screen 섹션 없음 (스키마 v2 최상위 키는 'screen')")
        return
    # 필수 필드
    for field in ("id", "name", "status", "version"):
        if field not in screen:
            err(f"{path}.screen: 필수 필드 '{field}' 없음")
    # ID 패턴
    if "id" in screen and not SCR_RE.match(str(screen["id"])):
        err(f"{path}.screen.id: SCR- 패턴 불일치 (값: {screen['id']})")
    # status enum
    if "status" in screen and screen["status"] not in STATUS_VALUES:
        err(f"{path}.screen.status: 허용되지 않은 값 '{screen['status']}' (허용: {STATUS_VALUES})")
    # version 정수
    if "version" in screen and not isinstance(screen["version"], int):
        err(f"{path}.screen.version: 정수 타입 필요 (값: {screen['version']})")
    # permission enum (있을 때만, 비표준은 warn)
    if "permission" in screen and screen["permission"] not in PERMISSIONS:
        warn(f"{path}.screen.permission: 비표준 값 '{screen['permission']}' — 역할 목록과 일치하는지 확인")
    # template.page 패턴
    tmpl = screen.get("template", {})
    if isinstance(tmpl, dict) and "page" in tmpl and not DP_RE.match(str(tmpl["page"])):
        warn(f"{path}.screen.template.page: DP- 패턴 불일치 (값: {tmpl['page']})")
    # from_template 핀 (신규, ADR-002 §5) — 있을 때만 검증 (하위호환: 없어도 무방)
    ft = screen.get("from_template")
    if ft is not None:
        if not isinstance(ft, dict):
            err(f"{path}.screen.from_template: dict 타입 필요 ({{page: DP-*, version: int}})")
        else:
            if "page" in ft and not DP_RE.match(str(ft["page"])):
                err(f"{path}.screen.from_template.page: DP- 패턴 불일치 (값: {ft['page']})")
            if "version" in ft and not isinstance(ft["version"], int):
                err(f"{path}.screen.from_template.version: 정수 타입 필요 (값: {ft['version']})")


def _is_pos_int(v) -> bool:
    """양의 정수인지 (bool 제외) 판정."""
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def validate_grid_position(gp: dict, loc: str, require_full: bool = True):
    """position.base 또는 at.<bp>의 그리드 좌표 dict를 검증한다 (ADR-002 §1).
    col_start·row: 양의 정수 필수. col_span: 양의 정수 OR shorthand. row_span: 있으면 양의 정수.
    픽셀 좌표("320px") / "auto" 흐름값 → ERROR.
    """
    if not isinstance(gp, dict):
        err(f"{loc}: dict 타입 필요 ({{col_start, col_span, row}})")
        return
    # col_start
    cs = gp.get("col_start")
    if cs is None:
        if require_full:
            err(f"{loc}: 'col_start' 없음")
    elif not _is_pos_int(cs):
        err(f"{loc}.col_start: 양의 정수 필요 — 픽셀 좌표·auto 금지 (값: {cs!r})")
    # col_span
    sp = gp.get("col_span")
    if sp is None:
        if require_full:
            err(f"{loc}: 'col_span' 없음")
    elif isinstance(sp, str):
        if sp not in COLSPAN_SHORTHAND:
            err(f"{loc}.col_span: 양의 정수 또는 shorthand{sorted(COLSPAN_SHORTHAND)} 필요 — "
                f"픽셀 좌표·auto 금지 (값: {sp!r})")
    elif not _is_pos_int(sp):
        err(f"{loc}.col_span: 양의 정수 또는 shorthand 필요 — 픽셀 좌표·auto 금지 (값: {sp!r})")
    # row
    rw = gp.get("row")
    if rw is None:
        if require_full:
            err(f"{loc}: 'row' 없음")
    elif not _is_pos_int(rw):
        err(f"{loc}.row: 양의 정수 필요 — 픽셀 좌표·auto 금지 (값: {rw!r})")
    # row_span (optional)
    if "row_span" in gp and not _is_pos_int(gp["row_span"]):
        err(f"{loc}.row_span: 양의 정수 필요 (값: {gp['row_span']!r})")


def validate_position_v2(pos: dict, loc: str):
    """신규 반응형 position(base/at)을 검증한다. base가 없으면 레거시로 간주(검증 안 함)."""
    # 레거시 area/span → deprecated 경고 (에러 아님)
    for legacy in ("area", "span"):
        if legacy in pos:
            warn(f"{loc}.position.{legacy}: deprecated 필드 — 무시됨 (base/at 사용 권장)")
    base = pos.get("base")
    if base is None:
        return  # 레거시 {slot, order} — 하위호환, 검증 안 함
    validate_grid_position(base, f"{loc}.position.base", require_full=True)
    at = pos.get("at")
    if at is not None:
        if not isinstance(at, dict):
            err(f"{loc}.position.at: dict 타입 필요 (브레이크포인트명: 좌표)")
            return
        for bp, gp in at.items():
            if bp not in BREAKPOINT_NAMES:
                warn(f"{loc}.position.at.{bp}: 비표준 브레이크포인트명 (허용: {sorted(BREAKPOINT_NAMES)})")
            if not isinstance(gp, dict):
                err(f"{loc}.position.at.{bp}: dict 타입 필요")
                continue
            # at 오버라이드는 부분 지정 허용(자동 강등 보완) — require_full=False
            validate_grid_position(gp, f"{loc}.position.at.{bp}", require_full=False)
            if "hidden" in gp and not isinstance(gp["hidden"], bool):
                err(f"{loc}.position.at.{bp}.hidden: boolean 타입 필요 (값: {gp['hidden']!r})")


def validate_layout(layout: list, path: str):
    if not isinstance(layout, list):
        err(f"{path}.layout: list 타입 필요")
        return
    ids_seen = set()
    for i, item in enumerate(layout):
        loc = f"{path}.layout[{i}]"
        for field in ("id", "source", "position"):
            if field not in item:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in item:
            cmp_id = str(item["id"])
            if not CMP_RE.match(cmp_id):
                err(f"{loc}.id: CMP- 패턴 불일치 (값: {cmp_id})")
            if cmp_id in ids_seen:
                err(f"{loc}.id: 중복 CMP ID '{cmp_id}'")
            ids_seen.add(cmp_id)
        # source: kind + ref
        src = item.get("source")
        if isinstance(src, dict):
            if "ref" not in src:
                err(f"{loc}.source: 'ref' 없음 (DS 컴포넌트 키)")
            kind = src.get("kind")
            if kind is None:
                warn(f"{loc}.source: 'kind' 없음 (ds | page-region)")
            elif kind not in SOURCE_KINDS:
                err(f"{loc}.source.kind: 허용되지 않은 값 '{kind}' (허용: {SOURCE_KINDS})")
        elif "source" in item:
            err(f"{loc}.source: dict 타입 필요 ({{kind, ref, version}})")
        if "position" in item:
            pos = item["position"]
            if not isinstance(pos, dict):
                err(f"{loc}.position: dict 타입 필요")
            else:
                if "slot" not in pos:
                    err(f"{loc}.position: 'slot' 없음")
                # 신규 반응형(base) vs 레거시({slot, order}) 분기
                if "base" in pos:
                    validate_position_v2(pos, loc)
                elif "order" not in pos:
                    warn(f"{loc}.position: 'order' 없음 (렌더링 순서 미정)")
        if "meta" in item and "interactive" in item["meta"]:
            if not isinstance(item["meta"]["interactive"], bool):
                err(f"{loc}.meta.interactive: boolean 타입 필요")


def validate_actions(actions: list, layout: list, path: str):
    if not isinstance(actions, list):
        err(f"{path}.actions: list 타입 필요")
        return
    layout_ids = {item.get("id") for item in (layout or [])}
    ids_seen = set()
    for i, action in enumerate(actions):
        loc = f"{path}.actions[{i}]"
        for field in ("id", "component", "trigger", "behavior", "outcome", "permission"):
            if field not in action:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in action:
            req_id = str(action["id"])
            if not REQ_RE.match(req_id):
                err(f"{loc}.id: REQ- 패턴 불일치 (값: {req_id})")
            if req_id in ids_seen:
                err(f"{loc}.id: 중복 REQ ID '{req_id}'")
            ids_seen.add(req_id)
        # action.component → layout[].id 참조 검증
        if "component" in action and action["component"] not in layout_ids:
            err(f"{loc}.component: layout에 존재하지 않는 CMP 참조 '{action['component']}'")
        # outcome.type enum
        if "outcome" in action and isinstance(action["outcome"], dict):
            ot = action["outcome"].get("type")
            if ot and ot not in OUTCOME_TYPES:
                err(f"{loc}.outcome.type: 허용되지 않은 값 '{ot}' (허용: {OUTCOME_TYPES})")
        # permission
        if "permission" in action and action["permission"] not in PERMISSIONS:
            warn(f"{loc}.permission: 비표준 값 '{action['permission']}' — tech-stack.md의 role 목록과 일치하는지 확인")
        # acceptance
        if "acceptance" not in action or not action["acceptance"]:
            warn(f"{loc}: acceptance 없음 — Stage 2에서 추가 필요")
        # status
        if "status" in action and action["status"] not in ACTION_STATUS:
            err(f"{loc}.status: 허용되지 않은 값 '{action['status']}' (허용: {ACTION_STATUS})")


def validate_notes(notes: list, layout: list, path: str):
    if not isinstance(notes, list):
        return
    layout_ids = {item.get("id") for item in (layout or [])} | {"screen"}
    for i, note in enumerate(notes):
        loc = f"{path}.notes[{i}]"
        for field in ("id", "body", "kind", "complexity"):
            if field not in note:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in note and not NOTE_RE.match(str(note["id"])):
            err(f"{loc}.id: NOTE- 패턴 불일치 (값: {note['id']})")
        if "kind" in note and note["kind"] not in NOTE_KINDS:
            err(f"{loc}.kind: 허용되지 않은 값 '{note['kind']}'")
        if "complexity" in note and note["complexity"] not in COMPLEXITY:
            err(f"{loc}.complexity: 허용되지 않은 값 '{note['complexity']}'")
        if "verbatim" in note and note["verbatim"] is not True:
            warn(f"{loc}.verbatim: note는 항상 verbatim:true 권장")
        if "scope" in note and note["scope"] not in layout_ids:
            warn(f"{loc}.scope: layout에 없는 scope '{note['scope']}'")


def validate_prompt_log(prompt_log: list, path: str):
    if not isinstance(prompt_log, list):
        return
    prev_id = -1
    for i, entry in enumerate(prompt_log):
        loc = f"{path}.prompt_log[{i}]"
        for field in ("id", "stage", "text", "applied_version"):
            if field not in entry:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in entry and not PRM_RE.match(str(entry["id"])):
            err(f"{loc}.id: PRM- 패턴 불일치 (값: {entry['id']})")
        if "applied_version" in entry:
            v = entry["applied_version"]
            if isinstance(v, int) and v < prev_id:
                warn(f"{loc}: applied_version이 역순 ({v} < {prev_id}) — append-only 원칙 확인")
            if isinstance(v, int):
                prev_id = v


def validate_intake(intake: dict, path: str):
    if not intake:
        return
    oqs = intake.get("open_questions", [])
    if not isinstance(oqs, list):
        err(f"{path}.intake.open_questions: list 타입 필요")
        return
    for i, q in enumerate(oqs):
        loc = f"{path}.intake.open_questions[{i}]"
        for field in ("id", "ask", "status"):
            if field not in q:
                err(f"{loc}: 필수 필드 '{field}' 없음")
        if "id" in q and not Q_RE.match(str(q["id"])):
            err(f"{loc}.id: Q- 패턴 불일치 (값: {q['id']}, 예: Q-001)")
        if "status" in q and q["status"] == "deferred" and "defer_reason" not in q:
            err(f"{loc}: status=deferred인데 defer_reason 없음")


def validate_file(file_path: Path):
    text = file_path.read_text(encoding="utf-8")
    # raw HTML 감지
    if re.search(r"<(div|span|table|button|input|form)\s", text, re.IGNORECASE):
        err(f"{file_path.name}: raw HTML 감지 — screen model에 HTML 직접 작성 금지")
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        err(f"{file_path.name}: YAML 파싱 실패 — {e}")
        return
    if not isinstance(doc, dict):
        err(f"{file_path.name}: 최상위 구조가 dict가 아님")
        return
    p = file_path.stem
    screen = doc.get("screen", {})
    layout = doc.get("layout", [])
    validate_schema_version(doc, p)
    validate_screen(screen, p)
    validate_layout(layout, p)
    # 신규 반응형 position을 쓰면서 from_template 핀이 없으면 권장 경고 (하위호환: warn에 그침)
    has_responsive = any(
        isinstance(it, dict) and isinstance(it.get("position"), dict) and "base" in it["position"]
        for it in (layout or [])
    )
    if has_responsive and not screen.get("from_template"):
        warn(f"{p}.screen: 반응형 position(base)을 쓰는 신규 화면은 from_template 핀 권장 (ADR-002 §5)")
    validate_actions(doc.get("actions", []), layout, p)
    validate_notes(doc.get("notes", []), layout, p)
    validate_prompt_log(doc.get("prompt_log", []), p)
    validate_intake(doc.get("intake", {}), p)


def main():
    if len(sys.argv) < 2:
        # Claude Code가 파일 경로를 stdin JSON으로 줄 수도 있으므로 glob 대안
        targets = list(Path(".").glob("model_repo/screens/SCR-*.yaml"))
    else:
        targets = [Path(p) for p in sys.argv[1:]]

    if not targets:
        print("[schema-validate] 검증할 파일 없음", file=sys.stderr)
        sys.exit(0)

    for fp in targets:
        if not fp.exists():
            err(f"{fp}: 파일 없음")
            continue
        validate_file(fp)

    for w in WARNINGS:
        print(w, file=sys.stderr)
    if ERRORS:
        for e in ERRORS:
            print(e, file=sys.stderr)
        print(f"\n[schema-validate] ❌ {len(ERRORS)} error(s) — 저장 차단", file=sys.stderr)
        sys.exit(1)
    print(f"[schema-validate] ✅ pass ({len(targets)} file(s), {len(WARNINGS)} warning(s))")
    sys.exit(0)


if __name__ == "__main__":
    main()
